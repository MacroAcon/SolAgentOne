import os
import json
import logging
from datetime import datetime
import requests
from dotenv import load_dotenv
from typing import Dict, Optional

from utils import validate_required_env_vars

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Validate required environment variables
validate_required_env_vars([
    'SPOTIFY_CLIENT_ID',
    'SPOTIFY_CLIENT_SECRET',
    'MAILCHIMP_API_KEY',
    'MAILCHIMP_LIST_ID'
])

# API Configuration
SPOTIFY_CLIENT_ID = os.getenv('SPOTIFY_CLIENT_ID')
SPOTIFY_CLIENT_SECRET = os.getenv('SPOTIFY_CLIENT_SECRET')
MAILCHIMP_API_KEY = os.getenv('MAILCHIMP_API_KEY')
MAILCHIMP_LIST_ID = os.getenv('MAILCHIMP_LIST_ID')
MAILCHIMP_DC = MAILCHIMP_API_KEY.split('-')[-1]  # Extract datacenter from API key

# Spotify API endpoints
SPOTIFY_TOKEN_URL = 'https://accounts.spotify.com/api/token'
SPOTIFY_API_BASE = 'https://api.spotify.com/v1'
SPOTIFY_PODCASTERS_API = 'https://api.spotify.com/v1/podcasters'

def get_spotify_access_token() -> str:
    """
    Get Spotify access token using client credentials flow.
    
    Returns:
        str: Access token for Spotify API
    """
    try:
        response = requests.post(
            SPOTIFY_TOKEN_URL,
            data={
                'grant_type': 'client_credentials',
                'client_id': SPOTIFY_CLIENT_ID,
                'client_secret': SPOTIFY_CLIENT_SECRET
            }
        )
        response.raise_for_status()
        return response.json()['access_token']
    except Exception as e:
        logger.error(f"Error getting Spotify access token: {str(e)}")
        raise

def upload_to_spotify(
    mp3_path: str,
    script_path: str,
    title: str,
    description: str,
    publish_date: datetime,
    show_id: Optional[str] = None
) -> Dict:
    """
    Upload MP3 to Spotify for Podcasters using the official API.
    
    Args:
        mp3_path: Path to the MP3 file
        script_path: Path to the episode script
        title: Episode title
        description: Episode description
        publish_date: When to publish the episode
        show_id: Optional Spotify show ID (if not provided, will use default show)
        
    Returns:
        Dict containing episode details including episode_id
    """
    if not os.path.exists(mp3_path):
        raise FileNotFoundError(f"Audio file not found: {mp3_path}")
        
    try:
        # Get access token
        access_token = get_spotify_access_token()
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        
        # Step 1: Get upload URL
        upload_url_response = requests.post(
            f'{SPOTIFY_PODCASTERS_API}/episodes/upload_url',
            headers=headers
        )
        upload_url_response.raise_for_status()
        upload_url = upload_url_response.json()['url']
        
        # Step 2: Upload the audio file
        with open(mp3_path, 'rb') as f:
            upload_response = requests.put(
                upload_url,
                data=f,
                headers={'Content-Type': 'audio/mpeg'}
            )
            upload_response.raise_for_status()
        
        # Step 3: Read script for show notes
        with open(script_path, 'r', encoding='utf-8') as f:
            show_notes = f.read()
        
        # Step 4: Create episode
        episode_data = {
            'name': title,
            'description': description,
            'show_notes': show_notes,
            'publish_date': publish_date.isoformat(),
            'audio_url': upload_url,
            'explicit': False,
            'language': 'en'
        }
        
        if show_id:
            episode_data['show_id'] = show_id
        
        create_response = requests.post(
            f'{SPOTIFY_PODCASTERS_API}/episodes',
            headers=headers,
            json=episode_data
        )
        create_response.raise_for_status()
        
        episode_details = create_response.json()
        logger.info(f"Successfully uploaded episode to Spotify for Podcasters: {title}")
        return episode_details
        
    except requests.exceptions.RequestException as e:
        logger.error(f"API error uploading to Spotify for Podcasters: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Error uploading to Spotify for Podcasters: {str(e)}")
        raise

def schedule_mailchimp_newsletter(
    html_content: str,
    image_url: Optional[str] = None,
    send_time: Optional[datetime] = None
) -> str:
    """
    Create and schedule Mailchimp campaign.
    
    Args:
        html_content: HTML content of the newsletter
        image_url: Optional URL for the newsletter header image
        send_time: Optional time to send the newsletter (defaults to next day at 9 AM)
        
    Returns:
        str: Campaign ID
    """
    try:
        # Set default send time if not provided
        if not send_time:
            send_time = datetime.now().replace(hour=9, minute=0, second=0, microsecond=0)
            send_time = send_time.replace(day=send_time.day + 1)
        
        # Create campaign
        campaign_data = {
            'type': 'regular',
            'recipients': {
                'list_id': MAILCHIMP_LIST_ID
            },
            'settings': {
                'subject_line': f"MCP Updates - {send_time.strftime('%Y-%m-%d')}",
                'title': f"Vibe Dev Newsletter - {send_time.strftime('%Y-%m-%d')}",
                'from_name': 'Vibe Dev',
                'reply_to': 'newsletter@vibedev.com',
                'auto_footer': False
            }
        }
        
        # Create campaign
        response = requests.post(
            f'https://{MAILCHIMP_DC}.api.mailchimp.com/3.0/campaigns',
            auth=('anystring', MAILCHIMP_API_KEY),
            json=campaign_data
        )
        response.raise_for_status()
        campaign_id = response.json()['id']
        
        # Set content
        content_data = {'html': html_content}
        if image_url:
            content_data['images'] = [{'type': 'header', 'url': image_url}]
            
        content_response = requests.put(
            f'https://{MAILCHIMP_DC}.api.mailchimp.com/3.0/campaigns/{campaign_id}/content',
            auth=('anystring', MAILCHIMP_API_KEY),
            json=content_data
        )
        content_response.raise_for_status()
        
        # Schedule campaign
        schedule_data = {
            'schedule_time': send_time.isoformat()
        }
        
        schedule_response = requests.post(
            f'https://{MAILCHIMP_DC}.api.mailchimp.com/3.0/campaigns/{campaign_id}/actions/schedule',
            auth=('anystring', MAILCHIMP_API_KEY),
            json=schedule_data
        )
        schedule_response.raise_for_status()
        
        logger.info(f"Successfully scheduled newsletter campaign: {campaign_id}")
        return campaign_id
        
    except requests.exceptions.RequestException as e:
        logger.error(f"API error scheduling Mailchimp campaign: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Error scheduling Mailchimp campaign: {str(e)}")
        raise

if __name__ == '__main__':
    # Test the publisher
    try:
        # Test with sample data
        test_mp3 = 'output/episode.mp3'
        test_script = 'output/episode_script.txt'
        test_title = "Test Episode"
        test_description = "This is a test episode"
        test_publish_date = datetime.now()
        
        # Test Spotify for Podcasters upload
        if os.path.exists(test_mp3) and os.path.exists(test_script):
            result = upload_to_spotify(
                test_mp3,
                test_script,
                test_title,
                test_description,
                test_publish_date
            )
            print("Spotify for Podcasters upload successful!")
            print(f"Episode ID: {result.get('id')}")
            
        # Test Mailchimp scheduling
        test_html = "<h1>Test Newsletter</h1><p>This is a test.</p>"
        test_image = "https://example.com/image.jpg"
        campaign_id = schedule_mailchimp_newsletter(
            test_html,
            test_image,
            test_publish_date
        )
        print(f"Mailchimp scheduling successful! Campaign ID: {campaign_id}")
        
    except Exception as e:
        print(f"Error: {str(e)}") 