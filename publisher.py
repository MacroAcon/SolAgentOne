import os
import json
import requests
from datetime import datetime
from typing import Dict, Optional
from dotenv import load_dotenv

from utils import (
    validate_required_env_vars,
    setup_logging,
    get_spotify_headers,
    handle_api_error,
    SPOTIFY_PODCASTERS_API
)

# Load environment variables
load_dotenv()

# Set up logging
logger = setup_logging(__name__, 'publisher.log')

# Validate required environment variables
validate_required_env_vars([
    'SPOTIFY_CLIENT_ID',
    'SPOTIFY_CLIENT_SECRET',
    'MAILCHIMP_API_KEY',
    'MAILCHIMP_LIST_ID'
])

# API Configuration
MAILCHIMP_API_KEY = os.getenv('MAILCHIMP_API_KEY')
MAILCHIMP_LIST_ID = os.getenv('MAILCHIMP_LIST_ID')
MAILCHIMP_DC = MAILCHIMP_API_KEY.split('-')[-1]  # Extract datacenter from API key

def upload_to_spotify(audio_path: str, script_path: str) -> Optional[str]:
    """
    Upload a podcast episode to Spotify for Podcasters.
    
    Args:
        audio_path: Path to the MP3 file
        script_path: Path to the episode script
        
    Returns:
        Episode ID if successful, None otherwise
    """
    try:
        # Read script content
        with open(script_path, 'r', encoding='utf-8') as f:
            script_content = f.read()
            
        # Extract metadata from script
        title = script_content.split('\n')[0].strip()
        description = '\n'.join(script_content.split('\n')[1:]).strip()
        
        # Get upload URL
        response = requests.post(
            f'{SPOTIFY_PODCASTERS_API}/episodes/upload',
            headers=get_spotify_headers()
        )
        response.raise_for_status()
        upload_url = response.json()['upload_url']
        
        # Upload audio file
        with open(audio_path, 'rb') as f:
            upload_response = requests.put(
                upload_url,
                data=f,
                headers={'Content-Type': 'audio/mpeg'}
            )
            upload_response.raise_for_status()
            
        # Create episode
        episode_response = requests.post(
            f'{SPOTIFY_PODCASTERS_API}/episodes',
            headers=get_spotify_headers(),
            json={
                'title': title,
                'description': description,
                'audio_url': upload_url,
                'publish_date': datetime.now().isoformat()
            }
        )
        episode_response.raise_for_status()
        
        return episode_response.json()['id']
        
    except Exception as e:
        return handle_api_error(e, logger, None)

def schedule_mailchimp_newsletter(newsletter_path: str, image_url: str) -> Optional[str]:
    """
    Schedule a newsletter campaign in Mailchimp.
    
    Args:
        newsletter_path: Path to the newsletter content
        image_url: URL of the newsletter header image
        
    Returns:
        Campaign ID if successful, None otherwise
    """
    try:
        # Read newsletter content
        with open(newsletter_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Create campaign
        campaign_response = requests.post(
            f'https://{MAILCHIMP_DC}.api.mailchimp.com/3.0/campaigns',
            auth=('anystring', MAILCHIMP_API_KEY),
            json={
                'type': 'regular',
                'recipients': {
                    'list_id': MAILCHIMP_LIST_ID
                },
                'settings': {
                    'subject_line': content.split('\n')[0],
                    'title': f"Newsletter {datetime.now().strftime('%Y-%m-%d')}",
                    'from_name': 'Solstice Team',
                    'reply_to': 'team@solstice.com',
                    'auto_footer': True
                }
            }
        )
        campaign_response.raise_for_status()
        campaign_id = campaign_response.json()['id']
        
        # Set content
        content_response = requests.put(
            f'https://{MAILCHIMP_DC}.api.mailchimp.com/3.0/campaigns/{campaign_id}/content',
            auth=('anystring', MAILCHIMP_API_KEY),
            json={
                'html': f'<img src="{image_url}" style="width: 100%; max-width: 600px;"><br><br>{content}'
            }
        )
        content_response.raise_for_status()
        
        # Schedule campaign
        schedule_response = requests.post(
            f'https://{MAILCHIMP_DC}.api.mailchimp.com/3.0/campaigns/{campaign_id}/actions/schedule',
            auth=('anystring', MAILCHIMP_API_KEY),
            json={
                'schedule_time': datetime.now().isoformat()
            }
        )
        schedule_response.raise_for_status()
        
        return campaign_id
        
    except Exception as e:
        return handle_api_error(e, logger, None)

if __name__ == '__main__':
    # Test the publisher
    audio_path = 'output/episode.mp3'
    script_path = 'output/episode_script.txt'
    
    # Upload to Spotify
    episode_id = upload_to_spotify(audio_path, script_path)
    if episode_id:
        print(f"Successfully uploaded episode to Spotify. Episode ID: {episode_id}")
    else:
        print("Failed to upload episode to Spotify")
        
    # Schedule newsletter
    newsletter_path = 'output/newsletter.txt'
    image_url = 'https://example.com/image.jpg'
    campaign_id = schedule_mailchimp_newsletter(newsletter_path, image_url)
    if campaign_id:
        print(f"Successfully scheduled newsletter. Campaign ID: {campaign_id}")
    else:
        print("Failed to schedule newsletter") 