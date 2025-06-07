import os
import logging
import tweepy
from linkedin_api import Linkedin
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('social.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Initialize Twitter API client
twitter_client = tweepy.Client(
    consumer_key=os.getenv('TWITTER_API_KEY'),
    consumer_secret=os.getenv('TWITTER_API_SECRET'),
    access_token=os.getenv('TWITTER_ACCESS_TOKEN'),
    access_token_secret=os.getenv('TWITTER_ACCESS_TOKEN_SECRET')
)

# Initialize LinkedIn API client
linkedin_client = Linkedin(
    os.getenv('LINKEDIN_USER'),
    os.getenv('LINKEDIN_PASSWORD')
)

def generate_social_post(title: str, podcast_url: str, news_headlines: list, platform: str = 'twitter') -> str:
    """
    Generate a social media post for the specified platform.
    
    Args:
        title: The podcast episode title
        podcast_url: URL to the podcast episode
        news_headlines: List of news headlines to include
        platform: The social media platform ('twitter' or 'linkedin')
        
    Returns:
        str: The generated post text
    """
    try:
        # Format news headlines
        news_text = "\n".join([f"• {headline}" for headline in news_headlines[:3]])
        
        if platform == 'twitter':
            # Twitter post (shorter, more concise)
            post = f"""🎙️ New episode of Vibe Dev Podcast is out!

{title}

Listen here: {podcast_url}

Latest MCP updates:
{news_text}"""
            
        else:  # LinkedIn
            # LinkedIn post (longer, more professional)
            post = f"""🎙️ Excited to share the latest episode of the Vibe Dev Podcast!

In this episode, we dive into the most recent developments in Machine Conversation Protocol (MCP) and explore how they're shaping the future of AI development.

{title}

Key topics covered:
{news_text}

Listen to the full episode here: {podcast_url}

#MCP #AI #MachineLearning #Podcast #TechNews"""
            
        return post
        
    except Exception as e:
        logger.error(f"Error generating social post: {str(e)}")
        raise

def _publish_to_twitter(post_text: str) -> bool:
    """
    Publish a post to Twitter.
    
    Args:
        post_text: The text to post
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Split post into chunks if it exceeds Twitter's limit
        max_length = 280
        if len(post_text) > max_length:
            # Find the last complete line before the limit
            last_newline = post_text[:max_length].rfind('\n')
            if last_newline == -1:
                last_newline = max_length
                
            # Split into two tweets
            first_tweet = post_text[:last_newline]
            second_tweet = post_text[last_newline:].strip()
            
            # Post first tweet
            first_response = twitter_client.create_tweet(text=first_tweet)
            first_tweet_id = first_response.data['id']
            
            # Post second tweet as a reply
            twitter_client.create_tweet(
                text=second_tweet,
                in_reply_to_tweet_id=first_tweet_id
            )
        else:
            # Post single tweet
            twitter_client.create_tweet(text=post_text)
            
        logger.info("Successfully posted to Twitter")
        return True
        
    except Exception as e:
        logger.error(f"Error posting to Twitter: {str(e)}")
        return False

def _publish_to_linkedin(post_text: str, article_url: str = None) -> bool:
    """
    Publish a post to LinkedIn.
    
    Args:
        post_text: The text to post
        article_url: Optional URL to attach to the post
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Prepare the post data
        post_data = {
            'author': linkedin_client.get_profile()['public_id'],
            'lifecycleState': 'PUBLISHED',
            'specificContent': {
                'com.linkedin.ugc.ShareContent': {
                    'shareCommentary': {
                        'text': post_text
                    },
                    'shareMediaCategory': 'NONE'
                }
            },
            'visibility': {
                'com.linkedin.ugc.MemberNetworkVisibility': 'PUBLIC'
            }
        }
        
        # Add article URL if provided
        if article_url:
            post_data['specificContent']['com.linkedin.ugc.ShareContent']['shareMediaCategory'] = 'ARTICLE'
            post_data['specificContent']['com.linkedin.ugc.ShareContent']['media'] = [{
                'status': 'READY',
                'originalUrl': article_url
            }]
        
        # Create the post
        linkedin_client.post(post_data)
        logger.info("Successfully posted to LinkedIn")
        return True
        
    except Exception as e:
        logger.error(f"Error posting to LinkedIn: {str(e)}")
        return False

def publish_social_posts(title: str, podcast_url: str, news_headlines: list) -> bool:
    """
    Publish promotional posts to all social media platforms.
    
    Args:
        title: The podcast episode title
        podcast_url: URL to the podcast episode
        news_headlines: List of news headlines to include
        
    Returns:
        bool: True if all posts were successful, False otherwise
    """
    try:
        success = True
        
        # Generate and post to Twitter
        twitter_post = generate_social_post(title, podcast_url, news_headlines, 'twitter')
        if not _publish_to_twitter(twitter_post):
            success = False
            logger.error("Failed to post to Twitter")
            
        # Generate and post to LinkedIn
        linkedin_post = generate_social_post(title, podcast_url, news_headlines, 'linkedin')
        if not _publish_to_linkedin(linkedin_post, podcast_url):
            success = False
            logger.error("Failed to post to LinkedIn")
            
        return success
        
    except Exception as e:
        logger.error(f"Error in social media publishing: {str(e)}")
        return False

if __name__ == '__main__':
    # Test the social publisher
    test_title = "Test Episode Title"
    test_url = "https://anchor.fm/vibedev/episodes/test"
    test_headlines = [
        "New MCP specification released",
        "Community project reaches 1,000 stars",
        "Latest AI developments in conversation protocols"
    ]
    
    if publish_social_posts(test_title, test_url, test_headlines):
        print("Test posts published successfully")
    else:
        print("Test posts failed") 