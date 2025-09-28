import feedparser
from collections import defaultdict
import json
from datetime import datetime
import time
import logging
import sys
import sqlite3


def get_rss_feeds_from_database():
    """Get RSS feeds from database and organize them by topic"""
    
    # Connect to database
    conn = sqlite3.connect('RSS_monitor.db')
    cursor = conn.cursor()
    
    # Get all sources organized by topic
    cursor.execute("""
        SELECT topic, rss_url 
        FROM sources 
        ORDER BY topic, name
    """)
    
    # Build the dictionary
    rss_feeds = {}
    
    for topic, rss_url in cursor.fetchall():
        if topic not in rss_feeds:
            rss_feeds[topic] = []
        rss_feeds[topic].append(rss_url)

    
    return rss_feeds

# Get the dictionary
RSS_FEEDS = get_rss_feeds_from_database()

SEEN_FILE = "seen_articles.json"

# Configure logging for commercial use
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('rss_monitor.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def load_seen():
    """Load all seen URLs from the database"""
    
    conn = sqlite3.connect('RSS_monitor.db')
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT url FROM articles WHERE seen = TRUE")
        results = cursor.fetchall()
        return {row[0] for row in results}  # Extract URLs from tuples
        
    finally:
        cursor.close()
        conn.close()

def save_seen(url, cursor):
    """Mark a specific article as seen in the database"""
    
    try:
        # Update the article to mark it as seen
        cursor.execute("""
            UPDATE articles 
            SET seen = TRUE 
            WHERE url = ?
        """, (url,))
        
    except Exception as e:
        print(f"Error marking article as seen: {e}")
        raise  # Re-raise the error to handle it in the calling function
        
    finally:
        cursor.close()
        conn.close()

def fetch_latest_news(limit_per_feed=50, max_per_topic=100, max_total_articles=300):
    conn = sqlite3.connect('RSS_monitor.db')
    cursor = conn.cursor()
    
    try:
        seen = load_seen()
        new_articles = []
        newly_seen_urls = []  # Collect URLs to mark as seen
        
        # Track articles per topic across ALL topics
        topic_counts = {topic: 0 for topic in RSS_FEEDS.keys()}

        for topic, rss_feed_urls in RSS_FEEDS.items():
            logger.info(f"Processing topic: {topic}")
            
            for rss_feed_url in rss_feed_urls:
                try:
                    feed = feedparser.parse(rss_feed_url)
                    
                    for entry in feed.entries[:limit_per_feed]:
                        article_url = entry.link
                        
                        # Check if we should process this article
                        if (article_url and 
                            article_url not in seen and 
                            topic_counts[topic] < max_per_topic and
                            len(new_articles) < max_total_articles):
                            
                            published = getattr(entry, 'published', 'No date')
                            
                            # STEP 1: SAVE ARTICLE TO DATABASE
                            cursor.execute("""
                                INSERT INTO articles (title, url, topic, source, published_date, seen) 
                                VALUES (?, ?, ?, ?, ?, FALSE)
                            """, (entry.title, article_url, topic, 'RSS Source', published))
                            
                            # Get the ID of the newly inserted article
                            article_id = cursor.lastrowid
                            
                            # STEP 2: ADD TO MEMORY LIST (for JSON output)
                            article_data = {
                                "id": article_id,
                                "topic": topic,
                                "title": entry.title,
                                "link": article_url,
                                "published": published
                            }
                            new_articles.append(article_data)
                            
                            # STEP 3: COLLECT URL TO MARK AS SEEN LATER
                            newly_seen_urls.append(article_url)
                            
                            # STEP 4: UPDATE COUNTERS
                            topic_counts[topic] += 1
                            seen.add(article_url)
                            
                            logger.info(f"Added article: {entry.title[:50]}... to {topic}")
                            
                        # Check if we've hit topic limit
                        if topic_counts[topic] >= max_per_topic:
                            logger.info(f"[{topic}] Reached limit of {max_per_topic} articles, moving to next topic...")
                            break
                        
                        # Check if we've hit total limit
                        if len(new_articles) >= max_total_articles:
                            logger.info(f"Reached total limit of {max_total_articles} articles, stopping collection")
                            break
                    
                    # Check total limit after processing each RSS feed
                    if len(new_articles) >= max_total_articles:
                        break
                        
                except Exception as e:
                    logger.error(f"Error processing {topic} RSS feed {rss_feed_url}: {e}")
                    continue
                
                # Check topic limit after processing each RSS feed
                if topic_counts[topic] >= max_per_topic:
                    break
            
            # Check total limit after processing each topic
            if len(new_articles) >= max_total_articles:
                break

        # STEP 5: MARK ALL NEW ARTICLES AS SEEN IN ONE BATCH
        if newly_seen_urls:
            cursor.executemany("""
                UPDATE articles 
                SET seen = TRUE 
                WHERE url = ?
            """, [(url,) for url in newly_seen_urls])
            
            logger.info(f"Marked {len(newly_seen_urls)} articles as seen")

        # Commit all database changes at once
        conn.commit()
        
        # Log summary
        for topic, count in topic_counts.items():
            if count > 0:
                logger.info(f"{topic}: {count} articles")
        
        return new_articles
        
    except Exception as e:
        logger.error(f"Error in fetch_latest_news: {e}")
        conn.rollback()  # Rollback on error
        raise
        
    finally:
        cursor.close()
        conn.close()

def get_source_name_from_url(rss_url):
    """Extract source name from RSS URL"""
    
    # Map RSS URLs to source names
    source_mapping = {
        'bbc.com': 'BBC',
        'theguardian.com': 'The Guardian',
        'reuters.com': 'Reuters',
        'apnews.com': 'AP News',
        'cnn.com': 'CNN',
        'npr.org': 'NPR'
    }
    
    for domain, name in source_mapping.items():
        if domain in rss_url:
            return name
    
    return "Unknown Source"

def parse_published_date(entry):
    """Parse and validate published date"""
    
    try:
        if hasattr(entry, 'published_parsed') and entry.published_parsed:
            # Convert RSS date to Python datetime
            dt = datetime(*entry.published_parsed[:6])
            
            # Validate the date isn't in the future
            if dt > datetime.now():
                return None  # Invalid future date
            return dt
            
    except (ValueError, TypeError):
        pass
    
    return None

def clean_url(url):
    """Remove tracking parameters from URLs"""
    
    # Remove common tracking parameters
    tracking_params = ['utm_', 'at_medium', 'at_campaign', 'ref_', 'source=']
    
    for param in tracking_params:
        if param in url:
            # Remove everything from this parameter onwards
            url = url.split(param)[0].rstrip('?&')
    
    return url

if __name__ == "__main__":
    start_time = time.time()
    
    logger.info("=" * 60)
    logger.info("COMMERCIAL RSS FEED MONITOR - STARTING")
    logger.info("=" * 60)
    logger.info(f"Monitoring {len(RSS_FEEDS)} topic categories")
    logger.info(f"Feed limits: {50} per feed, {100} per topic, {300} total articles max")
    logger.info("=" * 60)
    
    try:
        # Set a reasonable timeout (5 minutes max)
        timeout_seconds = 300  # 5 minutes
        logger.info(f"Timeout set to: {timeout_seconds} seconds")
        
        # Run once to get initial articles with timeout
        start_fetch_time = time.time()
        fresh_news = fetch_latest_news()
        
        # Check if we exceeded timeout
        fetch_time = time.time() - start_fetch_time
        if fetch_time > timeout_seconds:
            logger.warning(f"Fetch operation took {fetch_time:.2f}s, exceeded timeout of {timeout_seconds}s")
        
        if fresh_news:
            logger.info(f"SUCCESS: Found {len(fresh_news)} new articles")
            
            # Performance metrics
            total_articles = len(fresh_news)
            topics_covered = len(set(article['topic'] for article in fresh_news))
            
            # Group links by topic for commercial output
            grouped = defaultdict(list)
            for article in fresh_news:
                grouped[article['topic']].append(article['link'])
            
            # Commercial-grade output
            logger.info(f"ARTICLES BY TOPIC:")
            for topic, links in grouped.items():
                logger.info(f"  {topic}: {len(links)} articles")
            
            # NEW: Database statistics
            conn = sqlite3.connect('RSS_monitor.db')
            cursor = conn.cursor()
            
            try:
                # Get total articles in database
                cursor.execute("SELECT COUNT(*) FROM articles")
                total_in_db = cursor.fetchone()[0]
                
                # Get articles by topic in database
                cursor.execute("""
                    SELECT topic, COUNT(*) as count 
                    FROM articles 
                    GROUP BY topic 
                    ORDER BY count DESC
                """)
                db_topic_counts = cursor.fetchall()
                
                # Get seen vs unseen articles
                cursor.execute("SELECT COUNT(*) FROM articles WHERE seen = TRUE")
                seen_count = cursor.fetchone()[0]
                unseen_count = total_in_db - seen_count
                
                logger.info("=" * 60)
                logger.info("DATABASE STATISTICS:")
                logger.info(f"  Total articles in database: {total_in_db}")
                logger.info(f"  Articles marked as seen: {seen_count}")
                logger.info(f"  Articles not yet seen: {unseen_count}")
                logger.info("  Articles by topic in database:")
                for topic, count in db_topic_counts:
                    logger.info(f"    {topic}: {count} articles")
                
            finally:
                cursor.close()
                conn.close()
            
            # Save to commercial output file (keep this for reporting)
            output_data = {
                "timestamp": datetime.now().isoformat(),
                "total_articles": total_articles,
                "topics_covered": topics_covered,
                "articles_by_topic": dict(grouped),
                "database_stats": {
                    "total_in_database": total_in_db,
                    "seen_articles": seen_count,
                    "unseen_articles": unseen_count
                },
                "performance_metrics": {
                    "processing_time_seconds": round(time.time() - start_time, 2),
                    "articles_per_second": round(total_articles / (time.time() - start_time), 2)
                }
            }
            
            with open("commercial_articles_output.json", "w") as f:
                json.dump(output_data, f, indent=2)
            
            logger.info(f"Commercial output saved to: commercial_articles_output.json")
            
        else:
            logger.warning("No new articles found in this run")
            
            # NEW: Show database status even when no new articles
            conn = sqlite3.connect('RSS_monitor.db')
            cursor = conn.cursor()
            
            try:
                cursor.execute("SELECT COUNT(*) FROM articles")
                total_in_db = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(*) FROM articles WHERE seen = TRUE")
                seen_count = cursor.fetchone()[0]
                
                logger.info("=" * 60)
                logger.info("DATABASE STATUS:")
                logger.info(f"  Total articles in database: {total_in_db}")
                logger.info(f"  Articles marked as seen: {seen_count}")
                logger.info(f"  Articles not yet seen: {total_in_db - seen_count}")
                
            finally:
                cursor.close()
                conn.close()
        
        # Final performance summary
        processing_time = time.time() - start_time
        logger.info("=" * 60)
        logger.info("PERFORMANCE SUMMARY:")
        logger.info(f"  Total processing time: {processing_time:.2f} seconds")
        if fresh_news:
            logger.info(f"  Articles processed: {len(fresh_news)}")
            logger.info(f"  Processing rate: {len(fresh_news)/processing_time:.2f} articles/second")
        logger.info("=" * 60)
        logger.info("COMMERCIAL RSS FEED MONITOR - COMPLETE")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"CRITICAL ERROR: {str(e)}")
        logger.error("Stack trace:", exc_info=True)
        sys.exit(1)