import os
import json
import logging
import shutil
from datetime import datetime, timedelta
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
import requests
from dotenv import load_dotenv
from typing import Dict, Optional, Tuple, List
import concurrent.futures

# Import our agents
from scraper import scrape_mcp_news
from script_generator import generate_podcast_script, read_content_files as read_script_content
from newsletter_generator import generate_newsletter_content, read_content_files as read_newsletter_content
from publisher import upload_to_spotify, schedule_mailchimp_newsletter
from researcher import research_and_write_content
from image_generator import create_newsletter_image, generate_header_image
from social_publisher import publish_social_posts
from analytics_agent import run_analysis
from tts_agent import generate_audio_from_script, generate_audio
from blog_publisher import publish_to_blog
from synthesis_agent import develop_narrative_theme
from community_engagement_agent import post_engagement_comments
from quality_agent import run_quality_check

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('orchestrator.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Constants
FALLBACK_IMAGE_URL = os.getenv('FALLBACK_IMAGE_URL', 'https://example.com/fallback.jpg')
MAX_WORKERS = 3  # Number of parallel workers for data gathering
CRITICAL_STEPS = {
    'analysis': False,  # Analytics is non-critical
    'news_scraping': True,  # News is critical
    'content_research': True,  # Content research is critical
    'narrative_theme': True,  # Theme is critical
    'script_generation': True,  # Script is critical
    'audio_generation': True,  # Audio is critical
    'newsletter_generation': True,  # Newsletter is critical
    'blog_publishing': True,  # Blog is critical
    'anchor_upload': True,  # Anchor is critical
    'newsletter_scheduling': True,  # Newsletter scheduling is critical
    'transcript_archiving': False,  # Archiving is non-critical
    'social_publishing': False  # Social media is non-critical
}

def send_alert(message: str, is_critical: bool = False) -> None:
    """
    Send alert to configured channels.
    
    Args:
        message: Alert message
        is_critical: Whether this is a critical alert
    """
    try:
        # Send to Slack if configured
        slack_webhook = os.getenv('SLACK_WEBHOOK_URL')
        if slack_webhook:
            payload = {
                'text': f"{'🚨 CRITICAL: ' if is_critical else '⚠️ '}{message}"
            }
            requests.post(slack_webhook, json=payload)
            
        # Log the alert
        if is_critical:
            logger.error(message)
        else:
            logger.warning(message)
            
    except Exception as e:
        logger.error(f"Error sending alert: {str(e)}")

def get_episode_number() -> int:
    """Read the current episode number from the counter file."""
    try:
        with open('data/episode_counter.txt', 'r') as f:
            return int(f.read().strip())
    except (FileNotFoundError, ValueError):
        logger.error("Error reading episode counter, defaulting to 1")
        return 1

def increment_episode_number():
    """Increment the episode number in the counter file."""
    try:
        current_number = get_episode_number()
        with open('data/episode_counter.txt', 'w') as f:
            f.write(str(current_number + 1))
        logger.info(f"Incremented episode number to {current_number + 1}")
    except Exception as e:
        logger.error(f"Error incrementing episode number: {str(e)}")

def archive_transcript(episode_number: int):
    """Archive the episode script to the history/transcripts directory."""
    try:
        # Create history/transcripts directory if it doesn't exist
        os.makedirs('history/transcripts', exist_ok=True)
        
        # Get current date
        date_str = datetime.now().strftime('%Y-%m-%d')
        
        # Construct archive filename
        archive_filename = f"history/transcripts/{date_str}_EP{episode_number:03d}_script.txt"
        
        # Copy the script file
        shutil.copy2('output/episode_script.txt', archive_filename)
        logger.info(f"Archived transcript to {archive_filename}")
    except Exception as e:
        logger.error(f"Error archiving transcript: {str(e)}")

def update_publication_log(campaign_id: str, episode_id: str, publish_date: str, blog_url: str = None):
    """Update the publication log with the latest publication details."""
    try:
        os.makedirs('data', exist_ok=True)
        log_data = {
            'campaign_id': campaign_id,
            'episode_id': episode_id,
            'publish_date': publish_date,
            'blog_url': blog_url,
            'log_date': datetime.now().isoformat()
        }
        
        with open('data/publication_log.json', 'w') as f:
            json.dump(log_data, f, indent=2)
            
        logger.info("Updated publication log")
    except Exception as e:
        logger.error(f"Error updating publication log: {str(e)}")

def run_parallel_tasks(episode_number: int) -> Tuple[Optional[str], Optional[List[Dict]], Optional[Dict[str, str]]]:
    """
    Run independent data-gathering tasks in parallel.
    
    Returns:
        Tuple of (insights_summary, news_items, content_files)
    """
    try:
        with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            # Submit tasks
            analysis_future = executor.submit(run_analysis)
            news_future = executor.submit(scrape_mcp_news)
            content_future = executor.submit(research_and_write_content, episode_number)
            
            # Get results
            insights_summary = None
            try:
                insights_summary = analysis_future.result()
                logger.info("Analytics completed successfully")
            except Exception as e:
                error_msg = f"Analytics failed: {str(e)}"
                send_alert(error_msg, CRITICAL_STEPS['analysis'])
                if CRITICAL_STEPS['analysis']:
                    raise
                
            news_items = None
            try:
                news_items = news_future.result()
                if not news_items:
                    raise ValueError("No news items found")
                logger.info("News scraping completed successfully")
            except Exception as e:
                error_msg = f"News scraping failed: {str(e)}"
                send_alert(error_msg, CRITICAL_STEPS['news_scraping'])
                if CRITICAL_STEPS['news_scraping']:
                    raise
                
            content_files = None
            try:
                content_files = content_future.result()
                logger.info("Content research completed successfully")
            except Exception as e:
                error_msg = f"Content research failed: {str(e)}"
                send_alert(error_msg, CRITICAL_STEPS['content_research'])
                if CRITICAL_STEPS['content_research']:
                    raise
                
            return insights_summary, news_items, content_files
            
    except Exception as e:
        logger.error(f"Error in parallel tasks: {str(e)}")
        raise

def run_full_workflow(episode_number: int) -> None:
    """
    Run the full podcast production workflow.
    
    Args:
        episode_number: Current episode number
    """
    try:
        logger.info(f"Starting workflow for episode {episode_number}")
        
        # Step 1: Run parallel data gathering tasks
        logger.info("Step 1: Gathering data in parallel")
        try:
            analysis_results, news_results, content_results = run_parallel_tasks(episode_number)
            logger.info("Successfully gathered all data")
        except Exception as e:
            logger.error(f"Critical error in data gathering: {str(e)}")
            send_alert(f"❌ Critical Error: Data gathering failed - {str(e)}", is_critical=True)
            return
        
        # Step 2: Generate narrative theme
        logger.info("Step 2: Generating narrative theme")
        try:
            narrative_brief = develop_narrative_theme(
                news_results,
                content_results,
                analysis_results
            )
            logger.info("Successfully generated narrative theme")
        except Exception as e:
            logger.error(f"Critical error in narrative theme generation: {str(e)}")
            send_alert(f"❌ Critical Error: Narrative theme generation failed - {str(e)}", is_critical=True)
            return
        
        # Step 3: Generate podcast script
        logger.info("Step 3: Generating podcast script")
        try:
            script_path = generate_podcast_script(
                content_results['tool_spotlight'],
                content_results['privacy_insight'],
                content_results['community_corner'],
                episode_number,
                narrative_brief
            )
            logger.info("Successfully generated podcast script")
        except Exception as e:
            logger.error(f"Critical error in script generation: {str(e)}")
            send_alert(f"❌ Critical Error: Script generation failed - {str(e)}", is_critical=True)
            return
        
        # Step 4: Generate audio from script
        logger.info("Step 4: Generating audio from script")
        try:
            audio_path = generate_audio_from_script(script_path)
            logger.info("Successfully generated audio")
        except Exception as e:
            logger.error(f"Critical error in audio generation: {str(e)}")
            send_alert(f"❌ Critical Error: Audio generation failed - {str(e)}", is_critical=True)
            return
        
        # Step 5: Generate newsletter content
        logger.info("Step 5: Generating newsletter content")
        try:
            newsletter_path = generate_newsletter_content(
                content_results['tool_spotlight'],
                content_results['privacy_insight'],
                content_results['community_corner'],
                episode_number,
                narrative_brief
            )
            logger.info("Successfully generated newsletter content")
        except Exception as e:
            logger.error(f"Critical error in newsletter generation: {str(e)}")
            send_alert(f"❌ Critical Error: Newsletter generation failed - {str(e)}", is_critical=True)
            return
        
        # Step 6: Generate header image
        logger.info("Step 6: Generating header image")
        try:
            image_url = create_newsletter_image(episode_number, narrative_brief)
            logger.info("Successfully generated header image")
        except Exception as e:
            logger.error(f"Critical error in image generation: {str(e)}")
            send_alert(f"❌ Critical Error: Image generation failed - {str(e)}", is_critical=True)
            return
        
        # Step 7: Upload podcast to Spotify
        logger.info("Step 7: Uploading podcast to Spotify")
        try:
            episode_id = upload_to_spotify(audio_path, script_path)
            logger.info("Successfully uploaded podcast")
        except Exception as e:
            logger.error(f"Critical error in podcast upload: {str(e)}")
            send_alert(f"❌ Critical Error: Podcast upload failed - {str(e)}", is_critical=True)
            return
        
        # Step 8: Publish blog post
        logger.info("Step 8: Publishing blog post")
        try:
            blog_url = publish_to_blog(newsletter_path, image_url)
            logger.info("Successfully published blog post")
        except Exception as e:
            logger.error(f"Critical error in blog publishing: {str(e)}")
            send_alert(f"❌ Critical Error: Blog publishing failed - {str(e)}", is_critical=True)
            return
        
        # Step 9: Schedule newsletter
        logger.info("Step 9: Scheduling newsletter")
        try:
            campaign_id = schedule_mailchimp_newsletter(newsletter_path, image_url)
            logger.info("Successfully scheduled newsletter")
        except Exception as e:
            logger.error(f"Critical error in newsletter scheduling: {str(e)}")
            send_alert(f"❌ Critical Error: Newsletter scheduling failed - {str(e)}", is_critical=True)
            return
        
        # Step 10: Update publication log
        logger.info("Step 10: Updating publication log")
        try:
            publish_date = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
            update_publication_log(campaign_id, episode_id, publish_date, blog_url)
            logger.info("Successfully updated publication log")
        except Exception as e:
            logger.error(f"Error updating publication log: {str(e)}")
            send_alert(f"⚠️ Warning: Failed to update publication log - {str(e)}")
        
        # Step 11: Handle community engagement
        logger.info("Step 11: Handling community engagement")
        try:
            if content_results.get('featured_posts'):
                post_engagement_comments(content_results['featured_posts'])
            logger.info("Successfully handled community engagement")
        except Exception as e:
            logger.error(f"Error in community engagement: {str(e)}")
            send_alert(f"⚠️ Warning: Community engagement failed - {str(e)}")
        
        # Step 12: Archive transcript
        logger.info("Step 12: Archiving transcript")
        try:
            archive_transcript(episode_number)
            logger.info("Successfully archived transcript")
        except Exception as e:
            logger.error(f"Error archiving transcript: {str(e)}")
            send_alert(f"⚠️ Warning: Failed to archive transcript - {str(e)}")
        
        # Increment episode number
        increment_episode_number()
        
        logger.info(f"Successfully completed workflow for episode {episode_number}")
        send_alert(f"✅ Successfully completed workflow for episode {episode_number}")
        
    except Exception as e:
        logger.error(f"Critical error in workflow: {str(e)}")
        send_alert(f"❌ Critical Error: Workflow failed - {str(e)}", is_critical=True)

def main():
    """
    Main entry point for the orchestrator.
    """
    try:
        episode_number = get_episode_number()
        run_full_workflow(episode_number)
    except Exception as e:
        logger.error(f"Critical error in main: {str(e)}")
        send_alert(f"Critical error in main: {str(e)}", True)

if __name__ == "__main__":
    main() 