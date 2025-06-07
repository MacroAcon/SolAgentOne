import os
import json
import logging
import requests
from typing import List, Dict, Set
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
import feedparser
from dotenv import load_dotenv
from slugify import slugify

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_rss_sources() -> List[str]:
    """
    Load RSS feed sources from the configuration file.
    Returns a list of RSS feed URLs.
    """
    try:
        config_path = os.path.join('config', 'sources.json')
        with open(config_path, 'r') as f:
            config = json.load(f)
            return config.get('rss_feeds', [])
    except Exception as e:
        logger.error(f"Error loading RSS sources from config: {str(e)}")
        return []

def get_last_run_time() -> datetime:
    """
    Get the timestamp of the last successful run from last_run.txt.
    If the file doesn't exist or is invalid, return 24 hours ago.
    """
    try:
        if os.path.exists('data/last_run.txt'):
            with open('data/last_run.txt', 'r') as f:
                timestamp = f.read().strip()
                return datetime.fromisoformat(timestamp)
    except Exception as e:
        logger.error(f"Error reading last run time: {str(e)}")
    
    # Default to 24 hours ago if no valid timestamp found
    return datetime.now() - timedelta(hours=24)

def update_last_run_time():
    """Update the last_run.txt file with the current timestamp."""
    try:
        os.makedirs('data', exist_ok=True)
        with open('data/last_run.txt', 'w') as f:
            f.write(datetime.now().isoformat())
    except Exception as e:
        logger.error(f"Error updating last run time: {str(e)}")

def parse_feed(feed_url: str, last_run: datetime) -> List[Dict]:
    """
    Parse a single RSS feed and return new items since last run.
    Returns a list of dictionaries containing title, link, and published date.
    """
    try:
        logger.info(f"Parsing feed: {feed_url}")
        feed = feedparser.parse(feed_url)
        
        if feed.bozo:  # Check for feed parsing errors
            logger.warning(f"Feed parsing error for {feed_url}: {feed.bozo_exception}")
            return []
            
        new_items = []
        for entry in feed.entries:
            try:
                # Handle different date formats and fields
                published = None
                if hasattr(entry, 'published_parsed'):
                    published = datetime(*entry.published_parsed[:6])
                elif hasattr(entry, 'updated_parsed'):
                    published = datetime(*entry.updated_parsed[:6])
                
                if published and published > last_run:
                    new_items.append({
                        'title': entry.title,
                        'link': entry.link,
                        'published': published.isoformat()
                    })
            except Exception as e:
                logger.error(f"Error parsing feed entry: {str(e)}")
                continue
                
        return new_items
        
    except Exception as e:
        logger.error(f"Error parsing feed {feed_url}: {str(e)}")
        return []

def scrape_mcp_news() -> List[Dict]:
    """
    Scrape news from configured RSS feeds and return new items since last run.
    Implements deduplication to prevent duplicate content across feeds.
    """
    try:
        # Get last run time
        last_run = get_last_run_time()
        logger.info(f"Last run time: {last_run.isoformat()}")
        
        # Load RSS sources from config
        rss_sources = load_rss_sources()
        if not rss_sources:
            logger.error("No RSS sources found in configuration")
            return []
            
        # Track processed items to prevent duplicates
        processed_links: Set[str] = set()
        processed_titles: Set[str] = set()
        new_items = []
        
        # Parse each feed
        for feed_url in rss_sources:
            feed_items = parse_feed(feed_url, last_run)
            
            for item in feed_items:
                # Create a normalized version of the title for comparison
                normalized_title = slugify(item['title'])
                
                # Skip if we've seen this link or a similar title before
                if (item['link'] in processed_links or 
                    normalized_title in processed_titles):
                    logger.info(f"Skipping duplicate item: {item['title']}")
                    continue
                    
                # Add to processed sets and new items
                processed_links.add(item['link'])
                processed_titles.add(normalized_title)
                new_items.append(item)
        
        # Sort items by published date (newest first)
        new_items.sort(key=lambda x: x['published'], reverse=True)
        
        # Save to JSON file
        if new_items:
            os.makedirs('data', exist_ok=True)
            with open('data/latest_mcp_news.json', 'w') as f:
                json.dump(new_items, f, indent=2)
            logger.info(f"Saved {len(new_items)} new items to latest_mcp_news.json")
            
            # Update last run time
            update_last_run_time()
            
        return new_items
        
    except Exception as e:
        logger.error(f"Error in scrape_mcp_news: {str(e)}")
        return []

if __name__ == '__main__':
    # Test the scraper
    try:
        news_items = scrape_mcp_news()
        print(f"Found {len(news_items)} new items:")
        for item in news_items:
            print(f"- {item['title']} ({item['published']})")
    except Exception as e:
        print(f"Error: {str(e)}") 