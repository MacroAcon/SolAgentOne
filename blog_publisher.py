import os
import logging
from datetime import datetime
from ghost_admin_api import GhostAdminAPI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('blog.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Initialize Ghost Admin API client
ghost_api = GhostAdminAPI(
    url=os.getenv('GHOST_API_URL'),
    key=os.getenv('GHOST_ADMIN_API_KEY')
)

def publish_to_blog(title: str, html_content: str, tags: list = None) -> str:
    """
    Publish newsletter content to Ghost blog.
    
    Args:
        title: The title of the blog post
        html_content: The HTML content to publish
        tags: Optional list of tags to add to the post
        
    Returns:
        str: URL of the published blog post
    """
    # NOTE: Ensure the GHOST_API_URL environment variable is correct for your Ghost version (e.g., /ghost/api/admin/)
    try:
        # Set default tags if none provided
        if tags is None:
            tags = ['podcast', 'mcp', 'newsletter']
            
        # Add date to title if not already present
        if not any(char.isdigit() for char in title):
            date_str = datetime.now().strftime('%Y-%m-%d')
            title = f"{title} - {date_str}"
            
        # Prepare the post data
        post_data = {
            'title': title,
            'html': html_content,
            'status': 'published',
            'tags': tags,
            'feature_image': None,  # Will be set if available in HTML
            'meta_title': title,
            'meta_description': f"Latest MCP updates and insights from the Vibe Dev Podcast - {date_str}",
            'custom_excerpt': "Stay up to date with the latest developments in Machine Conversation Protocol (MCP) and AI technology."
        }
        
        # Try to extract feature image from HTML content
        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html_content, 'html.parser')
            img_tag = soup.find('img')
            if img_tag and 'src' in img_tag.attrs:
                post_data['feature_image'] = img_tag['src']
        except Exception as e:
            logger.warning(f"Could not extract feature image: {str(e)}")
        
        # Create the post
        logger.info(f"Publishing blog post: {title}")
        post = ghost_api.posts.create(**post_data)
        
        # Get the post URL
        post_url = post['url']
        logger.info(f"Blog post published successfully: {post_url}")
        
        return post_url
        
    except Exception as e:
        logger.error(f"Error publishing to blog: {str(e)}")
        raise

if __name__ == '__main__':
    # Test the blog publisher
    test_title = "Test Blog Post"
    test_content = """
    <h1>Test Content</h1>
    <p>This is a test blog post.</p>
    <img src="https://example.com/test.jpg" alt="Test Image">
    """
    test_tags = ['test', 'podcast']
    
    try:
        url = publish_to_blog(test_title, test_content, test_tags)
        print(f"Test post published successfully: {url}")
    except Exception as e:
        print(f"Test failed: {str(e)}") 