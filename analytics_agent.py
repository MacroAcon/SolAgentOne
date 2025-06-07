import os
import json
import requests
from datetime import datetime, timedelta
from typing import Dict, Optional
from dotenv import load_dotenv

from utils import (
    get_openai_client,
    format_prompt,
    validate_required_env_vars,
    setup_logging,
    get_spotify_headers,
    handle_api_error,
    SPOTIFY_PODCASTERS_API
)

# Load environment variables
load_dotenv()

# Set up logging
logger = setup_logging(__name__, 'analytics.log')

# Validate required environment variables
validate_required_env_vars([
    'OPENAI_API_KEY',
    'MAILCHIMP_API_KEY',
    'SPOTIFY_CLIENT_ID',
    'SPOTIFY_CLIENT_SECRET'
])

# API Configuration
MAILCHIMP_API_KEY = os.getenv('MAILCHIMP_API_KEY')
MAILCHIMP_DC = MAILCHIMP_API_KEY.split('-')[-1]

def get_mailchimp_report(campaign_id: str) -> Dict:
    """
    Fetch campaign report from Mailchimp API.
    
    Args:
        campaign_id: The Mailchimp campaign ID
        
    Returns:
        Dictionary containing campaign metrics
    """
    try:
        # Make API request
        response = requests.get(
            f'https://{MAILCHIMP_DC}.api.mailchimp.com/3.0/reports/{campaign_id}',
            auth=('anystring', MAILCHIMP_API_KEY)
        )
        response.raise_for_status()
        
        # Extract relevant metrics
        report_data = response.json()
        return {
            'open_rate': report_data.get('opens', {}).get('open_rate', 0),
            'clicks_per_unique_open': report_data.get('clicks', {}).get('unique_clicks', 0) / 
                                    report_data.get('opens', {}).get('unique_opens', 1),
            'top_links': [
                {
                    'url': click.get('url', ''),
                    'clicks': click.get('clicks', 0)
                }
                for click in report_data.get('clicks', {}).get('clicks', [])[:5]
            ]
        }
    except Exception as e:
        return handle_api_error(e, logger, {
            'open_rate': 0,
            'clicks_per_unique_open': 0,
            'top_links': []
        })

def get_spotify_stats(episode_id: str) -> Dict:
    """
    Fetch episode statistics from Spotify for Podcasters API.
    
    Args:
        episode_id: The Spotify for Podcasters episode ID
        
    Returns:
        Dictionary containing episode metrics
    """
    try:
        # Fetch episode analytics
        response = requests.get(
            f'{SPOTIFY_PODCASTERS_API}/episodes/{episode_id}/analytics',
            headers=get_spotify_headers(),
            params={
                'start_date': (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d'),
                'end_date': datetime.now().strftime('%Y-%m-%d'),
                'metrics': 'listeners,plays,completion_rate,avg_listen_duration'
            }
        )
        response.raise_for_status()
        
        # Extract relevant metrics
        stats_data = response.json()
        return {
            'listeners': stats_data.get('listeners', 0),
            'plays': stats_data.get('plays', 0),
            'completion_rate': stats_data.get('completion_rate', 0),
            'avg_listen_duration': stats_data.get('avg_listen_duration', 0)
        }
    except Exception as e:
        return handle_api_error(e, logger, {
            'listeners': 0,
            'plays': 0,
            'completion_rate': 0,
            'avg_listen_duration': 0
        })

def summarize_insights(analytics_data: Dict) -> str:
    """
    Generate a human-readable summary of performance insights using GPT-4.
    
    Args:
        analytics_data: Dictionary containing combined analytics data
        
    Returns:
        String containing the performance summary
    """
    try:
        # Get OpenAI client
        client = get_openai_client()
        
        # Prepare the prompt
        prompt = format_prompt(
            """You are an analyst summarizing a weekly content performance report. Based on the JSON data below, write a brief, one-paragraph summary (2-3 sentences) of the key insights.

Focus on what was popular and how the content performed.

Data:
{analytics_data}

Write only the summary paragraph.""",
            analytics_data=json.dumps(analytics_data, indent=2)
        )

        # Call GPT-4
        response = client.chat.completions.create(
            model=os.getenv('MODEL_ANALYST', 'gpt-4-turbo'),
            messages=[
                {"role": "system", "content": "You are a concise and insightful content analyst."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=150,
            temperature=0.7
        )
        
        return response.choices[0].message.content.strip()
    except Exception as e:
        return handle_api_error(e, logger, "Unable to generate performance insights at this time.")

def run_analysis() -> Optional[str]:
    """
    Main function to run the analytics workflow.
    
    Returns:
        String containing the performance summary, or None if no data is available
    """
    try:
        # Read the publication log
        try:
            with open('data/publication_log.json', 'r') as f:
                log_data = json.load(f)
        except FileNotFoundError:
            logger.warning("No publication log found")
            return None
        except json.JSONDecodeError:
            logger.error("Invalid publication log format")
            return None
            
        # Check if the log is from last week
        log_date = datetime.fromisoformat(log_data['publish_date'])
        if datetime.now() - log_date > timedelta(days=7):
            logger.warning("Publication log is too old")
            return None
            
        # Get campaign and episode IDs
        campaign_id = log_data.get('campaign_id')
        episode_id = log_data.get('episode_id')
        
        if not campaign_id or not episode_id:
            logger.warning("Missing campaign or episode ID in publication log")
            return None
            
        # Fetch analytics data
        mailchimp_data = get_mailchimp_report(campaign_id)
        spotify_data = get_spotify_stats(episode_id)
        
        # Combine the data
        analytics_data = {
            'mailchimp': mailchimp_data,
            'spotify': spotify_data,
            'publish_date': log_data['publish_date']
        }
        
        # Generate summary
        return summarize_insights(analytics_data)
        
    except Exception as e:
        return handle_api_error(e, logger, None)

if __name__ == '__main__':
    # Test the analytics workflow
    summary = run_analysis()
    if summary:
        print("\nPerformance Summary:")
        print(summary)
    else:
        print("No analytics data available")