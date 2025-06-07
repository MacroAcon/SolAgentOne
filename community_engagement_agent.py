import os
import logging
import praw
from typing import Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('community_engagement.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Initialize Reddit API client
reddit = praw.Reddit(
    client_id=os.getenv('REDDIT_CLIENT_ID'),
    client_secret=os.getenv('REDDIT_CLIENT_SECRET'),
    user_agent=os.getenv('REDDIT_USER_AGENT')
)

def extract_post_id(url: str) -> Optional[str]:
    """
    Extract Reddit post ID from a URL.
    
    Args:
        url: Reddit post URL
        
    Returns:
        Post ID or None if invalid
    """
    try:
        # Handle different URL formats
        if '/comments/' in url:
            # Format: https://reddit.com/r/subreddit/comments/abc123/title
            parts = url.split('/comments/')
            if len(parts) > 1:
                post_id = parts[1].split('/')[0]
                return post_id
        elif '/t3_' in url:
            # Format: https://reddit.com/t3_abc123
            parts = url.split('/t3_')
            if len(parts) > 1:
                return parts[1]
        return None
    except Exception as e:
        logger.error(f"Error extracting post ID from URL {url}: {str(e)}")
        return None

def post_engagement_comment(
    reddit_post_url: str,
    blog_post_url: str,
    episode_title: str
) -> bool:
    """
    Post an engagement comment to a Reddit thread.
    
    Args:
        reddit_post_url: URL of the Reddit post
        blog_post_url: URL of the blog post
        episode_title: Title of the episode
        
    Returns:
        True if comment was posted successfully, False otherwise
    """
    try:
        # Extract post ID
        post_id = extract_post_id(reddit_post_url)
        if not post_id:
            logger.error(f"Could not extract post ID from URL: {reddit_post_url}")
            return False
            
        # Get the submission
        submission = reddit.submission(id=post_id)
        
        # Check if post is locked or archived
        if submission.locked:
            logger.warning(f"Post {post_id} is locked")
            return False
        if submission.archived:
            logger.warning(f"Post {post_id} is archived")
            return False
            
        # Construct the comment
        comment_text = f"""Hey everyone! 👋

We found this discussion about {submission.title} really insightful, so we featured it in our latest episode: "{episode_title}".

You can check out the segment and the rest of the updates here: {blog_post_url}

Thanks for the great conversation! 🙏"""
        
        # Post the comment
        comment = submission.reply(comment_text)
        logger.info(f"Successfully posted comment to {reddit_post_url}")
        return True
        
    except praw.exceptions.APIException as e:
        logger.error(f"Reddit API error for {reddit_post_url}: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"Error posting comment to {reddit_post_url}: {str(e)}")
        return False

def post_engagement_comments(
    reddit_post_urls: list[str],
    blog_post_url: str,
    episode_title: str
) -> dict[str, bool]:
    """
    Post engagement comments to multiple Reddit threads.
    
    Args:
        reddit_post_urls: List of Reddit post URLs
        blog_post_url: URL of the blog post
        episode_title: Title of the episode
        
    Returns:
        Dictionary mapping URLs to success status
    """
    results = {}
    for url in reddit_post_urls:
        success = post_engagement_comment(url, blog_post_url, episode_title)
        results[url] = success
    return results

if __name__ == '__main__':
    # Test the engagement agent
    test_url = "https://reddit.com/r/LocalLLaMA/comments/abc123/test_post"
    test_blog_url = "https://vibedev.com/blog/episode-1"
    test_title = "MCP Updates - Episode 001"
    
    success = post_engagement_comment(test_url, test_blog_url, test_title)
    print(f"Test comment {'successful' if success else 'failed'}") 