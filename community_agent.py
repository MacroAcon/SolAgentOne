import os
import logging
import praw
from typing import List, Dict
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('community.log'),
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

def get_community_topics(subreddit_name: str, num_posts: int = 3) -> List[Dict]:
    """
    Fetch trending topics from a specified subreddit.
    
    Args:
        subreddit_name: Name of the subreddit (without 'r/')
        num_posts: Number of posts to fetch
        
    Returns:
        List of dictionaries containing post and comment data
    """
    try:
        logger.info(f"Fetching {num_posts} posts from r/{subreddit_name}")
        
        # Get the subreddit
        subreddit = reddit.subreddit(subreddit_name)
        
        # Fetch hot posts
        posts = []
        for post in subreddit.hot(limit=num_posts):
            # Skip stickied posts
            if post.stickied:
                continue
                
            # Get top comments
            post.comments.replace_more(limit=0)  # Remove MoreComments objects
            top_comments = sorted(
                post.comments.list(),
                key=lambda x: x.score,
                reverse=True
            )[:3]  # Get top 3 comments
            
            # Format comment data
            comments = []
            for comment in top_comments:
                comments.append({
                    'author': str(comment.author),
                    'body': comment.body,
                    'score': comment.score,
                    'created_utc': datetime.fromtimestamp(comment.created_utc).isoformat()
                })
            
            # Create post data
            post_data = {
                'title': post.title,
                'url': f"https://reddit.com{post.permalink}",
                'score': post.score,
                'num_comments': post.num_comments,
                'created_utc': datetime.fromtimestamp(post.created_utc).isoformat(),
                'author': str(post.author),
                'selftext': post.selftext if post.is_self else None,
                'link_url': post.url if not post.is_self else None,
                'top_comments': comments
            }
            
            posts.append(post_data)
            
        logger.info(f"Successfully fetched {len(posts)} posts from r/{subreddit_name}")
        return posts
        
    except Exception as e:
        logger.error(f"Error fetching community topics: {str(e)}")
        return []

def format_community_data(posts: List[Dict]) -> str:
    """
    Format community data for use in prompts.
    
    Args:
        posts: List of post dictionaries from get_community_topics
        
    Returns:
        Formatted string containing post and comment data
    """
    try:
        formatted_data = "Recent Community Discussions:\n\n"
        
        for post in posts:
            formatted_data += f"Post: {post['title']}\n"
            formatted_data += f"URL: {post['url']}\n"
            formatted_data += f"Score: {post['score']} | Comments: {post['num_comments']}\n"
            
            if post['selftext']:
                formatted_data += f"Content: {post['selftext'][:200]}...\n"
            elif post['link_url']:
                formatted_data += f"Link: {post['link_url']}\n"
                
            formatted_data += "\nTop Comments:\n"
            for comment in post['top_comments']:
                formatted_data += f"- {comment['author']} ({comment['score']} points):\n"
                formatted_data += f"  {comment['body'][:150]}...\n"
                
            formatted_data += "\n" + "-"*50 + "\n\n"
            
        return formatted_data
        
    except Exception as e:
        logger.error(f"Error formatting community data: {str(e)}")
        return "Error formatting community data"

if __name__ == '__main__':
    # Test the community agent
    subreddit = "LocalLLaMA"  # Example subreddit
    posts = get_community_topics(subreddit)
    
    if posts:
        print(f"\nFetched {len(posts)} posts from r/{subreddit}")
        print("\nFormatted Data:")
        print(format_community_data(posts))
    else:
        print(f"Failed to fetch posts from r/{subreddit}") 