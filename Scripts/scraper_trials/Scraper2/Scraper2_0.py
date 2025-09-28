#!/usr/bin/env python3
"""
Comprehensive News Scraper
Extracts article metadata, full text, and images from news websites.
Completely separate from existing systems.
"""

import requests
import json
import time
import os
import re
from datetime import datetime
from urllib.parse import urljoin, urlparse
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from bs4 import BeautifulSoup
import logging
from pathlib import Path
import hashlib
from PIL import Image
import io

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('news_scraper.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class ArticleMetadata:
    """Data class for article metadata"""
    url: str
    title: str
    author: Optional[str] = None
    publish_date: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    tags: List[str] = None
    word_count: Optional[int] = None
    reading_time: Optional[int] = None
    scraped_at: str = None
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []
        if self.scraped_at is None:
            self.scraped_at = datetime.now().isoformat()

@dataclass
class ArticleContent:
    """Data class for article content"""
    text: str
    images: List[Dict[str, Any]] = None
    links: List[str] = None
    
    def __post_init__(self):
        if self.images is None:
            self.images = []
        if self.links is None:
            self.links = []

@dataclass
class ScrapedArticle:
    """Complete scraped article data"""
    metadata: ArticleMetadata
    content: ArticleContent
    raw_html: Optional[str] = None

class NewsScraper:
    """Main scraper class for extracting news articles"""
    
    def __init__(self, output_dir: str = "scraped_articles", download_images: bool = True):
        self.output_dir = Path(output_dir)
        self.download_images = download_images
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
        
        # Create output directories
        self.output_dir.mkdir(parents=True, exist_ok=True)
        (self.output_dir / "images").mkdir(parents=True, exist_ok=True)
        (self.output_dir / "articles").mkdir(parents=True, exist_ok=True)
        (self.output_dir / "image_metadata").mkdir(parents=True, exist_ok=True)
        
        # News sites configuration with site-specific selectors
        self.news_sites = []
        
        # Site-specific configurations
        self.site_configs = {
            # Left-leaning/Progressive
            'alternet.org': {
                'title': ['.headline', 'h1', '.entry-title'],
                'author': ['.author', '.byline', '.byline-author'],
                'date': ['.date', '.published', 'time'],
                'content': ['.entry-content', '.article-content', '.post-content'],
                'description': ['.excerpt', '.summary']
            },
            'ap.org': {
                'title': ['h1', '.headline', '[data-testid="headline"]'],
                'author': ['.author', '.byline', '[data-testid="author"]'],
                'date': ['.timestamp', 'time', '[data-testid="timestamp"]'],
                'content': ['.Article', '.article-content', '[data-testid="article-content"]'],
                'description': ['.summary', '.lead']
            },
            'theatlantic.com': {
                'title': ['h1', '.c-article-header__hed', '.headline'],
                'author': ['.c-article-header__byline', '.author', '.byline'],
                'date': ['.c-article-header__publish-date', '.date', 'time'],
                'content': ['.c-article-content', '.article-content', '.post-content'],
                'description': ['.c-article-header__dek', '.summary']
            },
            'thedailybeast.com': {
                'title': ['h1', '.headline', '.article-title'],
                'author': ['.author', '.byline', '.author-name'],
                'date': ['.date', '.published', 'time'],
                'content': ['.article-content', '.post-content', '.entry-content'],
                'description': ['.summary', '.excerpt']
            },
            'democracynow.org': {
                'title': ['h1', '.headline', '.entry-title'],
                'author': ['.author', '.byline'],
                'date': ['.date', '.published', 'time'],
                'content': ['.entry-content', '.article-content', '.post-content'],
                'description': ['.excerpt', '.summary']
            },
            'theguardian.com': {
                'title': ['h1', '.headline', '[data-testid="headline"]'],
                'author': ['.author', '.byline', '[data-testid="author"]'],
                'date': ['.date', 'time', '[data-testid="timestamp"]'],
                'content': ['.article-body', '.article-content', '[data-testid="article-content"]'],
                'description': ['.standfirst', '.summary']
            },
            'huffpost.com': {
                'title': ['h1', '.headline', '.entry-title'],
                'author': ['.author', '.byline', '.author-name'],
                'date': ['.date', '.published', 'time'],
                'content': ['.entry-content', '.article-content', '.post-content'],
                'description': ['.excerpt', '.summary']
            },
            'theintercept.com': {
                'title': ['h1', '.headline', '.entry-title'],
                'author': ['.author', '.byline', '.author-name'],
                'date': ['.date', '.published', 'time'],
                'content': ['.entry-content', '.article-content', '.post-content'],
                'description': ['.excerpt', '.summary']
            },
            'jacobin.com': {
                'title': ['h1', '.headline', '.entry-title'],
                'author': ['.author', '.byline', '.author-name'],
                'date': ['.date', '.published', 'time'],
                'content': ['.entry-content', '.article-content', '.post-content'],
                'description': ['.excerpt', '.summary']
            },
            'motherjones.com': {
                'title': ['h1', '.headline', '.entry-title'],
                'author': ['.author', '.byline', '.author-name'],
                'date': ['.date', '.published', 'time'],
                'content': ['.entry-content', '.article-content', '.post-content'],
                'description': ['.excerpt', '.summary']
            },
            'msnbc.com': {
                'title': ['h1', '.headline', '.article-title'],
                'author': ['.author', '.byline', '.author-name'],
                'date': ['.date', '.published', 'time'],
                'content': ['.article-content', '.post-content', '.entry-content'],
                'description': ['.summary', '.excerpt']
            },
            'thenation.com': {
                'title': ['h1', '.headline', '.entry-title'],
                'author': ['.author', '.byline', '.author-name'],
                'date': ['.date', '.published', 'time'],
                'content': ['.entry-content', '.article-content', '.post-content'],
                'description': ['.excerpt', '.summary']
            },
            'nytimes.com': {
                'title': ['h1', '.headline', '[data-testid="headline"]'],
                'author': ['.author', '.byline', '[data-testid="author"]'],
                'date': ['.date', 'time', '[data-testid="timestamp"]'],
                'content': ['.article-content', '[data-testid="article-content"]', '.StoryBodyCompanionColumn'],
                'description': ['.summary', '.standfirst']
            },
            'newyorker.com': {
                'title': ['h1', '.headline', '.article-title'],
                'author': ['.author', '.byline', '.author-name'],
                'date': ['.date', '.published', 'time'],
                'content': ['.article-content', '.post-content', '.entry-content'],
                'description': ['.summary', '.excerpt']
            },
            'slate.com': {
                'title': ['h1', '.headline', '.entry-title'],
                'author': ['.author', '.byline', '.author-name'],
                'date': ['.date', '.published', 'time'],
                'content': ['.entry-content', '.article-content', '.post-content'],
                'description': ['.excerpt', '.summary']
            },
            'vox.com': {
                'title': ['h1', '.headline', '.c-page-title'],
                'author': ['.author', '.byline', '.c-byline'],
                'date': ['.date', '.published', 'time'],
                'content': ['.c-entry-content', '.article-content', '.post-content'],
                'description': ['.excerpt', '.summary']
            },
            
            # Centrist/Mainstream
            'abcnews.go.com': {
                'title': ['h1', '.headline', '[data-testid="headline"]'],
                'author': ['.author', '.byline', '[data-testid="author"]'],
                'date': ['.date', 'time', '[data-testid="timestamp"]'],
                'content': ['.article-content', '[data-testid="article-content"]', '.ArticleBody'],
                'description': ['.summary', '.lead']
            },
            'axios.com': {
                'title': ['h1', '.headline', '.article-title'],
                'author': ['.author', '.byline', '.author-name'],
                'date': ['.date', '.published', 'time'],
                'content': ['.article-content', '.post-content', '.entry-content'],
                'description': ['.summary', '.excerpt']
            },
            'bloomberg.com': {
                'title': ['h1', '.headline', '.article-title'],
                'author': ['.author', '.byline', '.author-name'],
                'date': ['.date', '.published', 'time'],
                'content': ['.article-content', '.post-content', '.entry-content'],
                'description': ['.summary', '.excerpt']
            },
            'cbsnews.com': {
                'title': ['h1', '.headline', '.article-title'],
                'author': ['.author', '.byline', '.author-name'],
                'date': ['.date', '.published', 'time'],
                'content': ['.article-content', '.post-content', '.entry-content'],
                'description': ['.summary', '.excerpt']
            },
            'cnbc.com': {
                'title': ['h1', '.headline', '.article-title'],
                'author': ['.author', '.byline', '.author-name'],
                'date': ['.date', '.published', 'time'],
                'content': ['.article-content', '.post-content', '.entry-content'],
                'description': ['.summary', '.excerpt']
            },
            'cnn.com': {
                'title': ['h1', '.headline__text', '.cd__headline-text', '[data-testid="headline"]'],
                'author': ['.metadata__byline__author', '.byline__name', '[data-testid="author"]'],
                'date': ['.metadata__timestamp', '.update-time', '[data-testid="timestamp"]'],
                'content': ['.article__content', '.l-container', '[data-testid="article-content"]'],
                'description': ['.article__lead', '.summary']
            },
            'insider.com': {
                'title': ['h1', '.headline', '.article-title'],
                'author': ['.author', '.byline', '.author-name'],
                'date': ['.date', '.published', 'time'],
                'content': ['.article-content', '.post-content', '.entry-content'],
                'description': ['.summary', '.excerpt']
            },
            'nbcnews.com': {
                'title': ['h1', '.headline', '.article-title'],
                'author': ['.author', '.byline', '.author-name'],
                'date': ['.date', '.published', 'time'],
                'content': ['.article-content', '.post-content', '.entry-content'],
                'description': ['.summary', '.excerpt']
            },
            'npr.org': {
                'title': ['h1', '.headline', '.article-title'],
                'author': ['.author', '.byline', '.author-name'],
                'date': ['.date', '.published', 'time'],
                'content': ['.article-content', '.post-content', '.entry-content'],
                'description': ['.summary', '.excerpt']
            },
            'politico.com': {
                'title': ['h1', '.headline', '.article-title'],
                'author': ['.author', '.byline', '.author-name'],
                'date': ['.date', '.published', 'time'],
                'content': ['.article-content', '.post-content', '.entry-content'],
                'description': ['.summary', '.excerpt']
            },
            'propublica.org': {
                'title': ['h1', '.headline', '.article-title'],
                'author': ['.author', '.byline', '.author-name'],
                'date': ['.date', '.published', 'time'],
                'content': ['.article-content', '.post-content', '.entry-content'],
                'description': ['.summary', '.excerpt']
            },
            'semafor.com': {
                'title': ['h1', '.headline', '.article-title'],
                'author': ['.author', '.byline', '.author-name'],
                'date': ['.date', '.published', 'time'],
                'content': ['.article-content', '.post-content', '.entry-content'],
                'description': ['.summary', '.excerpt']
            },
            'time.com': {
                'title': ['h1', '.headline', '.article-title'],
                'author': ['.author', '.byline', '.author-name'],
                'date': ['.date', '.published', 'time'],
                'content': ['.article-content', '.post-content', '.entry-content'],
                'description': ['.summary', '.excerpt']
            },
            'usatoday.com': {
                'title': ['h1', '.headline', '.article-title'],
                'author': ['.author', '.byline', '.author-name'],
                'date': ['.date', '.published', 'time'],
                'content': ['.article-content', '.post-content', '.entry-content'],
                'description': ['.summary', '.excerpt']
            },
            'washingtonpost.com': {
                'title': ['h1', '.headline', '.article-title'],
                'author': ['.author', '.byline', '.author-name'],
                'date': ['.date', '.published', 'time'],
                'content': ['.article-content', '.post-content', '.entry-content'],
                'description': ['.summary', '.excerpt']
            },
            'yahoo.com': {
                'title': ['h1', '.headline', '.article-title'],
                'author': ['.author', '.byline', '.author-name'],
                'date': ['.date', '.published', 'time'],
                'content': ['.article-content', '.post-content', '.entry-content'],
                'description': ['.summary', '.excerpt']
            },
            
            # Center-right/Conservative-leaning
            'bbc.com': {
                'title': ['h1', '.headline', '.article-title'],
                'author': ['.author', '.byline', '.author-name'],
                'date': ['.date', '.published', 'time'],
                'content': ['.article-content', '.post-content', '.entry-content'],
                'description': ['.summary', '.excerpt']
            },
            'csmonitor.com': {
                'title': ['h1', '.headline', '.article-title'],
                'author': ['.author', '.byline', '.author-name'],
                'date': ['.date', '.published', 'time'],
                'content': ['.article-content', '.post-content', '.entry-content'],
                'description': ['.summary', '.excerpt']
            },
            'forbes.com': {
                'title': ['h1', '.headline', '.article-title'],
                'author': ['.author', '.byline', '.author-name'],
                'date': ['.date', '.published', 'time'],
                'content': ['.article-content', '.post-content', '.entry-content'],
                'description': ['.summary', '.excerpt']
            },
            'thehill.com': {
                'title': ['h1', '.headline', '.article-title'],
                'author': ['.author', '.byline', '.author-name'],
                'date': ['.date', '.published', 'time'],
                'content': ['.article-content', '.post-content', '.entry-content'],
                'description': ['.summary', '.excerpt']
            },
            'marketwatch.com': {
                'title': ['h1', '.headline', '.article-title'],
                'author': ['.author', '.byline', '.author-name'],
                'date': ['.date', '.published', 'time'],
                'content': ['.article-content', '.post-content', '.entry-content'],
                'description': ['.summary', '.excerpt']
            },
            'newsnationnow.com': {
                'title': ['h1', '.headline', '.article-title'],
                'author': ['.author', '.byline', '.author-name'],
                'date': ['.date', '.published', 'time'],
                'content': ['.article-content', '.post-content', '.entry-content'],
                'description': ['.summary', '.excerpt']
            },
            'newsweek.com': {
                'title': ['h1', '.headline', '.article-title'],
                'author': ['.author', '.byline', '.author-name'],
                'date': ['.date', '.published', 'time'],
                'content': ['.article-content', '.post-content', '.entry-content'],
                'description': ['.summary', '.excerpt']
            },
            'reason.com': {
                'title': ['h1', '.headline', '.article-title'],
                'author': ['.author', '.byline', '.author-name'],
                'date': ['.date', '.published', 'time'],
                'content': ['.article-content', '.post-content', '.entry-content'],
                'description': ['.summary', '.excerpt']
            },
            'reuters.com': {
                'title': ['h1', '.headline', '.article-title'],
                'author': ['.author', '.byline', '.author-name'],
                'date': ['.date', '.published', 'time'],
                'content': ['.article-content', '.post-content', '.entry-content'],
                'description': ['.summary', '.excerpt']
            },
            'straightarrownews.com': {
                'title': ['h1', '.headline', '.article-title'],
                'author': ['.author', '.byline', '.author-name'],
                'date': ['.date', '.published', 'time'],
                'content': ['.article-content', '.post-content', '.entry-content'],
                'description': ['.summary', '.excerpt']
            },
            'wsj.com': {
                'title': ['h1', '.headline', '.article-title'],
                'author': ['.author', '.byline', '.author-name'],
                'date': ['.date', '.published', 'time'],
                'content': ['.article-content', '.post-content', '.entry-content'],
                'description': ['.summary', '.excerpt']
            },
            'thedispatch.com': {
                'title': ['h1', '.headline', '.article-title'],
                'author': ['.author', '.byline', '.author-name'],
                'date': ['.date', '.published', 'time'],
                'content': ['.article-content', '.post-content', '.entry-content'],
                'description': ['.summary', '.excerpt']
            },
            'theepochtimes.com': {
                'title': ['h1', '.headline', '.article-title'],
                'author': ['.author', '.byline', '.author-name'],
                'date': ['.date', '.published', 'time'],
                'content': ['.article-content', '.post-content', '.entry-content'],
                'description': ['.summary', '.excerpt']
            },
            'foxbusiness.com': {
                'title': ['h1', '.headline', '.article-title'],
                'author': ['.author', '.byline', '.author-name'],
                'date': ['.date', '.published', 'time'],
                'content': ['.article-content', '.post-content', '.entry-content'],
                'description': ['.summary', '.excerpt']
            },
            'thefp.com': {
                'title': ['h1', '.headline', '.article-title'],
                'author': ['.author', '.byline', '.author-name'],
                'date': ['.date', '.published', 'time'],
                'content': ['.article-content', '.post-content', '.entry-content'],
                'description': ['.summary', '.excerpt']
            },
            'justthenews.com': {
                'title': ['h1', '.headline', '.article-title'],
                'author': ['.author', '.byline', '.author-name'],
                'date': ['.date', '.published', 'time'],
                'content': ['.article-content', '.post-content', '.entry-content'],
                'description': ['.summary', '.excerpt']
            },
            'nationalreview.com': {
                'title': ['h1', '.headline', '.article-title'],
                'author': ['.author', '.byline', '.author-name'],
                'date': ['.date', '.published', 'time'],
                'content': ['.article-content', '.post-content', '.entry-content'],
                'description': ['.summary', '.excerpt']
            },
            'nypost.com': {
                'title': ['h1', '.headline', '.article-title'],
                'author': ['.author', '.byline', '.author-name'],
                'date': ['.date', '.published', 'time'],
                'content': ['.article-content', '.post-content', '.entry-content'],
                'description': ['.summary', '.excerpt']
            },
            'realclearpolitics.com': {
                'title': ['h1', '.headline', '.article-title'],
                'author': ['.author', '.byline', '.author-name'],
                'date': ['.date', '.published', 'time'],
                'content': ['.article-content', '.post-content', '.entry-content'],
                'description': ['.summary', '.excerpt']
            },
            'upward.news': {
                'title': ['h1', '.headline', '.article-title'],
                'author': ['.author', '.byline', '.author-name'],
                'date': ['.date', '.published', 'time'],
                'content': ['.article-content', '.post-content', '.entry-content'],
                'description': ['.summary', '.excerpt']
            },
            'washingtonexaminer.com': {
                'title': ['h1', '.headline', '.article-title'],
                'author': ['.author', '.byline', '.author-name'],
                'date': ['.date', '.published', 'time'],
                'content': ['.article-content', '.post-content', '.entry-content'],
                'description': ['.summary', '.excerpt']
            },
            'washingtontimes.com': {
                'title': ['h1', '.headline', '.article-title'],
                'author': ['.author', '.byline', '.author-name'],
                'date': ['.date', '.published', 'time'],
                'content': ['.article-content', '.post-content', '.entry-content'],
                'description': ['.summary', '.excerpt']
            },
            'zerohedge.com': {
                'title': ['h1', '.headline', '.article-title'],
                'author': ['.author', '.byline', '.author-name'],
                'date': ['.date', '.published', 'time'],
                'content': ['.article-content', '.post-content', '.entry-content'],
                'description': ['.summary', '.excerpt']
            },
            
            # Right-leaning/Conservative/Far-right
            'theamericanconservative.com': {
                'title': ['h1', '.headline', '.article-title'],
                'author': ['.author', '.byline', '.author-name'],
                'date': ['.date', '.published', 'time'],
                'content': ['.article-content', '.post-content', '.entry-content'],
                'description': ['.summary', '.excerpt']
            },
            'spectator.org': {
                'title': ['h1', '.headline', '.article-title'],
                'author': ['.author', '.byline', '.author-name'],
                'date': ['.date', '.published', 'time'],
                'content': ['.article-content', '.post-content', '.entry-content'],
                'description': ['.summary', '.excerpt']
            },
            'blazemedia.com': {
                'title': ['h1', '.headline', '.article-title'],
                'author': ['.author', '.byline', '.author-name'],
                'date': ['.date', '.published', 'time'],
                'content': ['.article-content', '.post-content', '.entry-content'],
                'description': ['.summary', '.excerpt']
            },
            'breitbart.com': {
                'title': ['h1', '.headline', '.article-title'],
                'author': ['.author', '.byline', '.author-name'],
                'date': ['.date', '.published', 'time'],
                'content': ['.article-content', '.post-content', '.entry-content'],
                'description': ['.summary', '.excerpt']
            },
            'cbn.com': {
                'title': ['h1', '.headline', '.article-title'],
                'author': ['.author', '.byline', '.author-name'],
                'date': ['.date', '.published', 'time'],
                'content': ['.article-content', '.post-content', '.entry-content'],
                'description': ['.summary', '.excerpt']
            },
            'dailycaller.com': {
                'title': ['h1', '.headline', '.article-title'],
                'author': ['.author', '.byline', '.author-name'],
                'date': ['.date', '.published', 'time'],
                'content': ['.article-content', '.post-content', '.entry-content'],
                'description': ['.summary', '.excerpt']
            },
            'dailymail.co.uk': {
                'title': ['h1', '.headline', '.article-title'],
                'author': ['.author', '.byline', '.author-name'],
                'date': ['.date', '.published', 'time'],
                'content': ['.article-content', '.post-content', '.entry-content'],
                'description': ['.summary', '.excerpt']
            },
            'dailywire.com': {
                'title': ['h1', '.headline', '.article-title'],
                'author': ['.author', '.byline', '.author-name'],
                'date': ['.date', '.published', 'time'],
                'content': ['.article-content', '.post-content', '.entry-content'],
                'description': ['.summary', '.excerpt']
            },
            'foxnews.com': {
                'title': ['h1', '.headline', '.article-title'],
                'author': ['.author', '.byline', '.author-name'],
                'date': ['.date', '.published', 'time'],
                'content': ['.article-content', '.post-content', '.entry-content'],
                'description': ['.summary', '.excerpt']
            },
            'thefederalist.com': {
                'title': ['h1', '.headline', '.article-title'],
                'author': ['.author', '.byline', '.author-name'],
                'date': ['.date', '.published', 'time'],
                'content': ['.article-content', '.post-content', '.entry-content'],
                'description': ['.summary', '.excerpt']
            },
            'ijr.com': {
                'title': ['h1', '.headline', '.article-title'],
                'author': ['.author', '.byline', '.author-name'],
                'date': ['.date', '.published', 'time'],
                'content': ['.article-content', '.post-content', '.entry-content'],
                'description': ['.summary', '.excerpt']
            },
            'newsmax.com': {
                'title': ['h1', '.headline', '.article-title'],
                'author': ['.author', '.byline', '.author-name'],
                'date': ['.date', '.published', 'time'],
                'content': ['.article-content', '.post-content', '.entry-content'],
                'description': ['.summary', '.excerpt']
            },
            'oann.com': {
                'title': ['h1', '.headline', '.article-title'],
                'author': ['.author', '.byline', '.author-name'],
                'date': ['.date', '.published', 'time'],
                'content': ['.article-content', '.post-content', '.entry-content'],
                'description': ['.summary', '.excerpt']
            },
            'thepostmillennial.com': {
                'title': ['h1', '.headline', '.article-title'],
                'author': ['.author', '.byline', '.author-name'],
                'date': ['.date', '.published', 'time'],
                'content': ['.article-content', '.post-content', '.entry-content'],
                'description': ['.summary', '.excerpt']
            },
            'freebeacon.com': {
                'title': ['h1', '.headline', '.article-title'],
                'author': ['.author', '.byline', '.author-name'],
                'date': ['.date', '.published', 'time'],
                'content': ['.article-content', '.post-content', '.entry-content'],
                'description': ['.summary', '.excerpt']
            }
        }
        
        # Common selectors for different news sites
        self.common_selectors = {
            'title': [
                'h1', 'h2.title', '.headline', '.article-title', 
                '[data-testid="headline"]', '.entry-title',
                '.headline__text', '.cd__headline-text'  # CNN specific
            ],
            'author': [
                '.author', '.byline', '[rel="author"]', '.article-author',
                '.writer', '.reporter', '[data-testid="author"]',
                '.metadata__byline__author', '.byline__name'  # CNN specific
            ],
            'date': [
                '.date', '.publish-date', '.article-date', 'time',
                '[datetime]', '.timestamp', '.published',
                '.update-time', '.metadata__timestamp'  # CNN specific
            ],
            'content': [
                '.article-content', '.entry-content', '.post-content',
                '.article-body', '.story-body', 'article', '.content',
                '.article__content', '.l-container'  # CNN specific
            ],
            'description': [
                '.excerpt', '.summary', '.article-summary', 'meta[name="description"]',
                '.lead', '.intro', '.article__lead'  # CNN specific
            ]
        }
    
    def add_news_site(self, url: str, custom_selectors: Dict[str, List[str]] = None):
        """Add a news site to the scraping list"""
        site_config = {
            'url': url,
            'selectors': custom_selectors or {}
        }
        self.news_sites.append(site_config)
        logger.info(f"Added news site: {url}")
    
    def get_site_selectors(self, url: str) -> Dict[str, List[str]]:
        """Get site-specific selectors based on URL domain"""
        from urllib.parse import urlparse
        domain = urlparse(url).netloc.lower()
        
        # Remove www. prefix if present
        if domain.startswith('www.'):
            domain = domain[4:]
        
        # Check for exact domain match
        if domain in self.site_configs:
            return self.site_configs[domain]
        
        # Check for partial domain matches (for subdomains)
        for site_domain, selectors in self.site_configs.items():
            if site_domain in domain or domain in site_domain:
                return selectors
        
        # Return common selectors as fallback
        return {}
    
    def handle_special_sites(self, url: str, soup: BeautifulSoup) -> Dict[str, Any]:
        """Handle sites with special requirements or non-standard layouts"""
        from urllib.parse import urlparse
        domain = urlparse(url).netloc.lower()
        
        special_handlers = {
            'cnn.com': self._handle_cnn,
            'foxnews.com': self._handle_fox_news,
            'nytimes.com': self._handle_nytimes,
            'washingtonpost.com': self._handle_washington_post,
            'breitbart.com': self._handle_breitbart,
            'dailymail.co.uk': self._handle_daily_mail,
            'zerohedge.com': self._handle_zero_hedge,
            'theepochtimes.com': self._handle_epoch_times
        }
        
        # Check for exact domain match
        if domain in special_handlers:
            return special_handlers[domain](soup, url)
        
        # Check for partial domain matches
        for site_domain, handler in special_handlers.items():
            if site_domain in domain:
                return handler(soup, url)
        
        return {}
    
    def _handle_cnn(self, soup: BeautifulSoup, url: str) -> Dict[str, Any]:
        """Special handling for CNN's dynamic content"""
        result = {}
        
        # CNN often loads content dynamically, try to find JSON-LD data
        json_ld = soup.find('script', type='application/ld+json')
        if json_ld:
            try:
                import json
                data = json.loads(json_ld.string)
                if isinstance(data, dict) and data.get('@type') == 'NewsArticle':
                    result['title'] = data.get('headline', '')
                    result['author'] = data.get('author', {}).get('name', '') if isinstance(data.get('author'), dict) else ''
                    result['date'] = data.get('datePublished', '')
                    result['description'] = data.get('description', '')
            except:
                pass
        
        return result
    
    def _handle_fox_news(self, soup: BeautifulSoup, url: str) -> Dict[str, Any]:
        """Special handling for Fox News"""
        result = {}
        
        # Fox News sometimes uses different selectors
        title_elem = soup.find('h1', class_='headline') or soup.find('h1', class_='entry-title')
        if title_elem:
            result['title'] = title_elem.get_text(strip=True)
        
        return result
    
    def _handle_nytimes(self, soup: BeautifulSoup, url: str) -> Dict[str, Any]:
        """Special handling for New York Times"""
        result = {}
        
        # NYT has different selectors for opinion vs news
        if '/opinion/' in url:
            title_elem = soup.find('h1', class_='css-1j9dxys e1h9rw200')
            if not title_elem:
                title_elem = soup.find('h1')
            if title_elem:
                result['title'] = title_elem.get_text(strip=True)
        
        return result
    
    def _handle_washington_post(self, soup: BeautifulSoup, url: str) -> Dict[str, Any]:
        """Special handling for Washington Post"""
        result = {}
        
        # WaPo uses specific classes
        title_elem = soup.find('h1', {'data-testid': 'headline'})
        if not title_elem:
            title_elem = soup.find('h1', class_='headline')
        if title_elem:
            result['title'] = title_elem.get_text(strip=True)
        
        return result
    
    def _handle_breitbart(self, soup: BeautifulSoup, url: str) -> Dict[str, Any]:
        """Special handling for Breitbart"""
        result = {}
        
        # Breitbart uses specific selectors
        title_elem = soup.find('h1', class_='entry-title')
        if not title_elem:
            title_elem = soup.find('h1')
        if title_elem:
            result['title'] = title_elem.get_text(strip=True)
        
        return result
    
    def _handle_daily_mail(self, soup: BeautifulSoup, url: str) -> Dict[str, Any]:
        """Special handling for Daily Mail"""
        result = {}
        
        # Daily Mail has complex structure
        title_elem = soup.find('h1', {'itemprop': 'headline'})
        if not title_elem:
            title_elem = soup.find('h1', class_='headline')
        if title_elem:
            result['title'] = title_elem.get_text(strip=True)
        
        return result
    
    def _handle_zero_hedge(self, soup: BeautifulSoup, url: str) -> Dict[str, Any]:
        """Special handling for ZeroHedge"""
        result = {}
        
        # ZeroHedge uses specific classes
        title_elem = soup.find('h1', class_='entry-title')
        if not title_elem:
            title_elem = soup.find('h1')
        if title_elem:
            result['title'] = title_elem.get_text(strip=True)
        
        return result
    
    def _handle_epoch_times(self, soup: BeautifulSoup, url: str) -> Dict[str, Any]:
        """Special handling for Epoch Times"""
        result = {}
        
        # Epoch Times has specific structure
        title_elem = soup.find('h1', class_='entry-title')
        if not title_elem:
            title_elem = soup.find('h1')
        if title_elem:
            result['title'] = title_elem.get_text(strip=True)
        
        return result
    
    def get_page(self, url: str, timeout: int = 30) -> Optional[BeautifulSoup]:
        """Fetch and parse a web page"""
        try:
            logger.info(f"Fetching: {url}")
            response = self.session.get(url, timeout=timeout)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            return soup
            
        except requests.RequestException as e:
            logger.error(f"Error fetching {url}: {e}")
            return None
    
    def extract_metadata(self, soup: BeautifulSoup, url: str, custom_selectors: Dict = None) -> ArticleMetadata:
        """Extract article metadata from the page"""
        # Get site-specific selectors
        site_selectors = self.get_site_selectors(url)
        
        # Handle special sites first
        special_data = self.handle_special_sites(url, soup)
        
        # Merge selectors: custom > site-specific > common
        selectors = {}
        for key, value in self.common_selectors.items():
            selectors[key] = value.copy()
        
        # Override with site-specific selectors
        for key, value in site_selectors.items():
            if key in selectors:
                selectors[key] = value + selectors[key]  # Prepend site-specific selectors
            else:
                selectors[key] = value
        
        # Override with custom selectors if provided
        if custom_selectors:
            for key, value in custom_selectors.items():
                selectors[key] = value
        
        # Extract title (use special data if available)
        title = special_data.get('title') or self._extract_text_by_selectors(soup, selectors.get('title', []))
        
        # Extract author (use special data if available)
        author = special_data.get('author') or self._extract_text_by_selectors(soup, selectors.get('author', []))
        
        # Extract publish date (use special data if available)
        publish_date = special_data.get('date') or self._extract_date(soup, selectors.get('date', []))
        
        # Extract description (use special data if available)
        description = special_data.get('description') or self._extract_text_by_selectors(soup, selectors.get('description', []))
        
        # Extract category/tags
        category = self._extract_category(soup)
        tags = self._extract_tags(soup)
        
        # Calculate word count and reading time
        content_text = self._extract_text_by_selectors(soup, selectors.get('content', []))
        word_count = len(content_text.split()) if content_text else 0
        reading_time = max(1, word_count // 200)  # Assuming 200 words per minute
        
        return ArticleMetadata(
            url=url,
            title=title or "No title found",
            author=author,
            publish_date=publish_date,
            description=description,
            category=category,
            tags=tags,
            word_count=word_count,
            reading_time=reading_time
        )
    
    def extract_content(self, soup: BeautifulSoup, base_url: str, custom_selectors: Dict = None) -> ArticleContent:
        """Extract article content including text and images"""
        selectors = custom_selectors or {}
        content_selectors = selectors.get('content', self.common_selectors['content'])
        
        # Find main content container
        content_container = None
        for selector in content_selectors:
            content_container = soup.select_one(selector)
            if content_container:
                break
        
        if not content_container:
            content_container = soup
        
        # Extract text content
        text_content = self._clean_text(content_container.get_text())
        
        # Extract images
        images = self._extract_images(content_container, base_url)
        
        # Extract links
        links = self._extract_links(content_container, base_url)
        
        return ArticleContent(
            text=text_content,
            images=images,
            links=links
        )
    
    def _extract_text_by_selectors(self, soup: BeautifulSoup, selectors: List[str]) -> Optional[str]:
        """Extract text using multiple selectors"""
        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                text = element.get_text(strip=True)
                if text:
                    return text
        return None
    
    def _extract_date(self, soup: BeautifulSoup, selectors: List[str]) -> Optional[str]:
        """Extract and format publish date"""
        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                # Try to get datetime attribute first
                datetime_attr = element.get('datetime')
                if datetime_attr:
                    return datetime_attr
                
                # Otherwise get text content
                text = element.get_text(strip=True)
                if text:
                    return text
        return None
    
    def _extract_category(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract article category"""
        category_selectors = [
            '.category', '.section', '.breadcrumb', '.topic',
            '[data-testid="category"]', '.article-category'
        ]
        
        for selector in category_selectors:
            element = soup.select_one(selector)
            if element:
                return element.get_text(strip=True)
        
        return None
    
    def _extract_tags(self, soup: BeautifulSoup) -> List[str]:
        """Extract article tags"""
        tags = []
        
        # Look for common tag patterns
        tag_selectors = [
            '.tags a', '.tag', '.keywords', '.topics a',
            '[rel="tag"]', '.article-tags a'
        ]
        
        for selector in tag_selectors:
            elements = soup.select(selector)
            for element in elements:
                tag_text = element.get_text(strip=True)
                if tag_text and tag_text not in tags:
                    tags.append(tag_text)
        
        return tags
    
    def _extract_images(self, container: BeautifulSoup, base_url: str) -> List[Dict[str, Any]]:
        """Extract images from the content"""
        images = []
        img_tags = container.find_all('img')
        downloaded_urls = set()  # Track downloaded URLs to avoid duplicates
        
        for img in img_tags:
            img_data = {
                'src': None,
                'alt': img.get('alt', ''),
                'title': img.get('title', ''),
                'caption': '',
                'downloaded_path': None
            }
            
            # Get image source - try multiple attributes
            src = (img.get('src') or 
                   img.get('data-src') or 
                   img.get('data-lazy-src') or 
                   img.get('data-original') or
                   img.get('data-srcset') or
                   img.get('data-echo'))
            
            if src:
                # Handle srcset (multiple image sources)
                if ',' in src:
                    src = src.split(',')[0].strip().split(' ')[0]
                
                img_data['src'] = urljoin(base_url, src)
                
                # Skip if already downloaded this URL
                if img_data['src'] in downloaded_urls:
                    continue
                
                # Download image if enabled
                if self.download_images:
                    downloaded_path = self._download_image(img_data['src'])
                    img_data['downloaded_path'] = downloaded_path
                    if downloaded_path:
                        downloaded_urls.add(img_data['src'])
            
            # Extract caption
            caption_element = img.find_next(['figcaption', '.caption', '.image-caption'])
            if caption_element:
                img_data['caption'] = caption_element.get_text(strip=True)
            
            # Only add if we have a valid source
            if img_data['src']:
                images.append(img_data)
        
        return images
    
    def _extract_links(self, container: BeautifulSoup, base_url: str) -> List[str]:
        """Extract links from the content"""
        links = []
        link_tags = container.find_all('a', href=True)
        
        for link in link_tags:
            href = link.get('href')
            if href:
                full_url = urljoin(base_url, href)
                if full_url not in links:
                    links.append(full_url)
        
        return links
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize text content"""
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        # Remove common unwanted patterns
        text = re.sub(r'Advertisement|Ad|Sponsored', '', text, flags=re.IGNORECASE)
        return text.strip()
    
    def _download_image(self, image_url: str) -> Optional[str]:
        """Download image and return local path"""
        try:
            # Skip data URLs and invalid URLs
            if image_url.startswith('data:') or not image_url.startswith(('http://', 'https://')):
                return None
            
            response = self.session.get(image_url, timeout=30, stream=True)
            response.raise_for_status()
            
            # Check if it's actually an image
            content_type = response.headers.get('content-type', '').lower()
            if not content_type.startswith('image/'):
                logger.warning(f"URL does not point to an image: {image_url} (content-type: {content_type})")
                return None
            
            # Generate filename from URL hash
            url_hash = hashlib.md5(image_url.encode()).hexdigest()
            file_extension = self._get_image_extension(content_type)
            filename = f"{url_hash}{file_extension}"
            
            # Save image
            image_path = self.output_dir / "images" / filename
            
            # Skip if file already exists
            if image_path.exists():
                logger.info(f"Image already exists: {filename}")
                return str(image_path)
            
            with open(image_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
            # Verify the file was created and has content
            if image_path.exists() and image_path.stat().st_size > 0:
                logger.info(f"Downloaded image: {filename} ({image_path.stat().st_size} bytes)")
                return str(image_path)
            else:
                logger.error(f"Downloaded file is empty or doesn't exist: {filename}")
                if image_path.exists():
                    image_path.unlink()  # Remove empty file
                return None
            
        except Exception as e:
            logger.error(f"Error downloading image {image_url}: {e}")
            return None
    
    def _get_image_extension(self, content_type: str) -> str:
        """Get file extension from content type"""
        extensions = {
            'image/jpeg': '.jpg',
            'image/jpg': '.jpg',
            'image/png': '.png',
            'image/gif': '.gif',
            'image/webp': '.webp',
            'image/svg+xml': '.svg',
            'image/bmp': '.bmp',
            'image/tiff': '.tiff',
            'image/avif': '.avif'
        }
        return extensions.get(content_type.lower(), '.jpg')
    
    def scrape_article(self, url: str, custom_selectors: Dict = None) -> Optional[ScrapedArticle]:
        """Scrape a single article"""
        soup = self.get_page(url)
        if not soup:
            return None
        
        # Extract metadata
        metadata = self.extract_metadata(soup, url, custom_selectors)
        
        # Extract content
        content = self.extract_content(soup, url, custom_selectors)
        
        # Store raw HTML if needed
        raw_html = str(soup) if soup else None
        
        return ScrapedArticle(
            metadata=metadata,
            content=content,
            raw_html=raw_html
        )
    
    def scrape_site(self, site_url: str, custom_selectors: Dict = None, max_articles: int = 10) -> List[ScrapedArticle]:
        """Scrape multiple articles from a news site"""
        articles = []
        
        # Get the main page
        soup = self.get_page(site_url)
        if not soup:
            return articles
        
        # Find article links (common patterns)
        article_links = self._find_article_links(soup, site_url)
        
        logger.info(f"Found {len(article_links)} potential articles")
        
        # Scrape each article
        for i, article_url in enumerate(article_links[:max_articles]):
            logger.info(f"Scraping article {i+1}/{min(len(article_links), max_articles)}")
            
            article = self.scrape_article(article_url, custom_selectors)
            if article:
                articles.append(article)
                self._save_article(article)
            
            # Rate limiting
            time.sleep(1)
        
        return articles
    
    def _find_article_links(self, soup: BeautifulSoup, base_url: str) -> List[str]:
        """Find article links on a news site"""
        links = []
        
        # Common patterns for article links
        link_selectors = [
            'a[href*="/article/"]',
            'a[href*="/news/"]',
            'a[href*="/story/"]',
            'a[href*="/post/"]',
            'a[href*="/2024/"]',  # CNN and other sites use year patterns
            'a[href*="/2025/"]',
            'a[href*="/2023/"]',
            '.headline a',
            '.article-link',
            '.story-link',
            '.container__item a',  # CNN specific
            '.cd__headline a'      # CNN specific
        ]
        
        for selector in link_selectors:
            elements = soup.select(selector)
            for element in elements:
                href = element.get('href')
                if href:
                    full_url = urljoin(base_url, href)
                    if full_url not in links and self._is_article_url(full_url):
                        links.append(full_url)
        
        return links
    
    def _is_article_url(self, url: str) -> bool:
        """Check if URL looks like an article"""
        # Skip common non-article URLs
        skip_patterns = [
            '/category/', '/tag/', '/author/', '/search/',
            '/about/', '/contact/', '/privacy/', '/terms/',
            '/subscribe/', '/newsletter/', '/rss/', '/feed/',
            '/interactive/', '/live/', '/video/', '/photos/',
            '/fact-check', '/elections/', '/exit-polls/'
        ]
        
        for pattern in skip_patterns:
            if pattern in url.lower():
                return False
        
        # CNN specific: URLs with year/month/day pattern are likely articles
        if '/cnn.com/' in url and re.match(r'.*/\d{4}/\d{2}/\d{2}/', url):
            return True
        
        # Other news sites: URLs with common article patterns
        article_patterns = [
            '/article/', '/news/', '/story/', '/post/',
            '/politics/', '/business/', '/world/', '/sports/',
            '/entertainment/', '/health/', '/technology/'
        ]
        
        for pattern in article_patterns:
            if pattern in url.lower():
                return True
        
        return False
    
    def _save_article(self, article: ScrapedArticle):
        """Save article to file"""
        # Ensure directories exist
        (self.output_dir / "articles").mkdir(parents=True, exist_ok=True)
        (self.output_dir / "images").mkdir(parents=True, exist_ok=True)
        (self.output_dir / "image_metadata").mkdir(parents=True, exist_ok=True)
        
        # Generate filename from URL
        url_hash = hashlib.md5(article.metadata.url.encode()).hexdigest()
        article_filename = f"{url_hash}.json"
        article_filepath = self.output_dir / "articles" / article_filename
        
        # Convert to dictionary for JSON serialization
        article_dict = {
            'metadata': asdict(article.metadata),
            'content': asdict(article.content),
            'raw_html': article.raw_html
        }
        
        # Save article
        with open(article_filepath, 'w', encoding='utf-8') as f:
            json.dump(article_dict, f, indent=2, ensure_ascii=False)
        
        # Save image metadata as separate JSON file in image_metadata directory
        if article.content.images:
            images_filename = f"{url_hash}_images.json"
            images_filepath = self.output_dir / "image_metadata" / images_filename
            
            images_dict = {
                'article_url': article.metadata.url,
                'article_title': article.metadata.title,
                'scraped_at': article.metadata.scraped_at,
                'images': article.content.images
            }
            
            with open(images_filepath, 'w', encoding='utf-8') as f:
                json.dump(images_dict, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Saved article: {article_filename} and {len(article.content.images)} images metadata: {images_filename}")
        else:
            logger.info(f"Saved article: {article_filename}")
    
    def scrape_all_sites(self, max_articles_per_site: int = 10) -> Dict[str, List[ScrapedArticle]]:
        """Scrape all configured news sites"""
        results = {}
        
        for site_config in self.news_sites:
            site_url = site_config['url']
            custom_selectors = site_config.get('selectors', {})
            
            logger.info(f"Scraping site: {site_url}")
            
            articles = self.scrape_site(
                site_url, 
                custom_selectors, 
                max_articles_per_site
            )
            
            results[site_url] = articles
            logger.info(f"Scraped {len(articles)} articles from {site_url}")
        
        return results
    
    def create_summary(self, results: Dict[str, List[ScrapedArticle]]):
        """Create a simple summary of scraping results"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        summary_filename = f"scraping_summary_{timestamp}.json"
        summary_filepath = self.output_dir / summary_filename
        
        # Create summary data
        summary_data = {
            'scraping_date': timestamp,
            'total_sites': len(results),
            'total_articles': sum(len(articles) for articles in results.values()),
            'sites': {}
        }
        
        for site_url, articles in results.items():
            total_images = sum(len(article.content.images) for article in articles)
            summary_data['sites'][site_url] = {
                'articles_count': len(articles),
                'images_count': total_images,
                'articles': [
                    {
                        'title': article.metadata.title,
                        'url': article.metadata.url,
                        'author': article.metadata.author,
                        'word_count': article.metadata.word_count,
                        'images_count': len(article.content.images)
                    }
                    for article in articles
                ]
            }
        
        with open(summary_filepath, 'w', encoding='utf-8') as f:
            json.dump(summary_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Created summary: {summary_filename}")
        return summary_filepath


def main():
    """Example usage of the NewsScraper with all news sites from the image"""
    scraper = NewsScraper(output_dir="scraped_news", download_images=True)
    
    # Add all news sites from the image - POLITICS SECTIONS ONLY
    news_sites = [
        # Left-leaning/Progressive - Politics sections
        "https://www.alternet.org/politics",
        "https://www.ap.org/politics",
        "https://www.theatlantic.com/politics",
        "https://www.thedailybeast.com/politics",
        "https://www.democracynow.org/topics/politics",
        "https://www.theguardian.com/us-news/us-politics",
        "https://www.huffpost.com/politics",
        "https://www.theintercept.com/politics",
        "https://www.jacobin.com/politics",
        "https://www.motherjones.com/politics",
        "https://www.msnbc.com/politics",
        "https://www.thenation.com/politics",
        "https://www.nytimes.com/section/politics",
        "https://www.newyorker.com/news/politics",
        "https://www.slate.com/news-and-politics",
        "https://www.vox.com/policy-and-politics",
        
        # Centrist/Mainstream - Politics sections
        "https://www.abcnews.go.com/politics",
        "https://www.axios.com/politics",
        "https://www.bloomberg.com/politics",
        "https://www.cbsnews.com/politics",
        "https://www.cnbc.com/politics",
        "https://www.cnn.com/politics",
        "https://www.insider.com/politics",
        "https://www.nbcnews.com/politics",
        "https://www.npr.org/sections/politics",
        "https://www.politico.com",
        "https://www.propublica.org/politics",
        "https://www.semafor.com/politics",
        "https://www.time.com/politics",
        "https://www.usatoday.com/politics",
        "https://www.washingtonpost.com/politics",
        "https://www.yahoo.com/news/politics",
        
        # Center-right/Conservative-leaning - Politics sections
        "https://www.bbc.com/news/politics",
        "https://www.csmonitor.com/politics",
        "https://www.forbes.com/politics",
        "https://www.thehill.com",
        "https://www.marketwatch.com/politics",
        "https://www.newsnationnow.com/politics",
        "https://www.newsweek.com/politics",
        "https://www.reason.com/politics",
        "https://www.reuters.com/politics",
        "https://www.straightarrownews.com/politics",
        "https://www.wsj.com/politics",
        "https://www.thedispatch.com/politics",
        "https://www.theepochtimes.com/politics",
        "https://www.foxbusiness.com/politics",
        "https://www.thefp.com/politics",
        "https://www.justthenews.com/politics",
        "https://www.nationalreview.com/politics",
        "https://www.nypost.com/politics",
        "https://www.realclearpolitics.com",
        "https://www.upward.news/politics",
        "https://www.washingtonexaminer.com/politics",
        "https://www.washingtontimes.com/politics",
        "https://www.zerohedge.com/politics",
        
        # Right-leaning/Conservative/Far-right - Politics sections
        "https://www.theamericanconservative.com/politics",
        "https://www.spectator.org/politics",
        "https://www.blazemedia.com/politics",
        "https://www.breitbart.com/politics",
        "https://www.cbn.com/politics",
        "https://www.dailycaller.com/politics",
        "https://www.dailymail.co.uk/news/politics",
        "https://www.dailywire.com/politics",
        "https://www.foxnews.com/politics",
        "https://www.thefederalist.com/politics",
        "https://www.ijr.com/politics",
        "https://www.newsmax.com/politics",
        "https://www.oann.com/politics",
        "https://www.thepostmillennial.com/politics",
        "https://www.freebeacon.com/politics"
    ]
    
    # Add all news sites to the scraper
    for site_url in news_sites:
        scraper.add_news_site(site_url)
    
    print(f"Added {len(news_sites)} news sites to the scraper")
    
    # Scrape all configured sites (limit to 3 articles per site for testing)
    results = scraper.scrape_all_sites(max_articles_per_site=3)
    
    # Create summary
    summary_file = scraper.create_summary(results)
    
    print(f"Scraping complete! Check the 'scraped_news' directory for results.")
    print(f"Total sites scraped: {len(results)}")
    total_articles = sum(len(articles) for articles in results.values())
    print(f"Total articles scraped: {total_articles}")
    print(f"Summary file: {summary_file}")
    print(f"Individual articles saved in: scraped_news/articles/")
    print(f"Downloaded images saved in: scraped_news/images/")
    print(f"Image metadata saved in: scraped_news/image_metadata/")


if __name__ == "__main__":
    main()
