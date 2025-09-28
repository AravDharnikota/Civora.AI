#!/usr/bin/env python3
"""
Example usage of the NewsScraper
"""

from Scraper2_0 import NewsScraper

def example_usage():
    """Example of how to use the NewsScraper"""
    
    # Initialize the scraper
    scraper = NewsScraper(
        output_dir="scraped_news", 
        download_images=True
    )
    
    # Add news sites to scrape (blank list as requested)
    # Uncomment and modify these lines to add actual news sites:
    
    # scraper.add_news_site("https://www.bbc.com/news")
    # scraper.add_news_site("https://www.cnn.com")
    # scraper.add_news_site("https://www.reuters.com")
    
    # You can also add custom selectors for specific sites:
    # scraper.add_news_site("https://example-news.com", {
    #     'title': ['.custom-title-class'],
    #     'author': ['.custom-author-class'],
    #     'content': ['.custom-content-class'],
    #     'date': ['.custom-date-class']
    # })
    
    print("News scraper initialized with blank site list.")
    print("Add news sites using scraper.add_news_site() method.")
    print("Example:")
    print("  scraper.add_news_site('https://example-news.com')")
    print("  results = scraper.scrape_all_sites(max_articles_per_site=5)")
    print("  scraper.export_results(results)")

if __name__ == "__main__":
    example_usage()
