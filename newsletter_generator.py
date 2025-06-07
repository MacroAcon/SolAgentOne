import json
import os
import logging
from typing import Dict
from datetime import datetime
from dotenv import load_dotenv

from utils import (
    read_content_files,
    get_openai_client,
    format_prompt,
    validate_required_env_vars
)

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Validate required environment variables
validate_required_env_vars(['OPENAI_API_KEY'])

def generate_newsletter_content(
    tool_filename: str,
    privacy_filename: str,
    community_filename: str,
    episode_number: int,
    narrative_brief: str
) -> str:
    """
    Generate newsletter content.
    
    Args:
        tool_filename: Path to tool spotlight content
        privacy_filename: Path to privacy insight content
        community_filename: Path to community corner content
        episode_number: Current episode number
        narrative_brief: Narrative theme for the episode
        
    Returns:
        Path to generated newsletter HTML file
    """
    try:
        logger.info("Generating newsletter content")
        
        # Read content files
        content = read_content_files()
        tool_content = content.get('tool', '')
        privacy_content = content.get('privacy', '')
        community_content = content.get('community', '')
        
        # Prepare the prompt
        prompt = format_prompt(
            """Create an HTML newsletter for MCP Updates Episode {episode_number}.

Narrative Theme:
{narrative_brief}

Content Segments:

Tool Spotlight:
{tool_content}

Privacy Insight:
{privacy_content}

Community Corner:
{community_content}

Requirements:
1. Use the narrative theme as the central thread throughout the newsletter
2. Create a professional, modern HTML layout
3. Include clear section headings and transitions
4. Add relevant links and resources
5. Keep the tone engaging and informative
6. Use appropriate HTML formatting and styling
7. Make it mobile-responsive
8. Include a call-to-action section

Format the newsletter in HTML with proper styling.""",
            episode_number=episode_number,
            narrative_brief=narrative_brief,
            tool_content=tool_content,
            privacy_content=privacy_content,
            community_content=community_content
        )

        # Get OpenAI client
        client = get_openai_client()
        
        # Generate newsletter using GPT-4
        response = client.chat.completions.create(
            model=os.getenv('MODEL_NEWSLETTER', 'gpt-4'),
            messages=[
                {"role": "system", "content": "You are a professional newsletter writer and HTML developer."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=2000
        )
        
        newsletter_html = response.choices[0].message.content
        
        # Save newsletter
        os.makedirs('output', exist_ok=True)
        newsletter_path = 'output/newsletter_draft.html'
        
        with open(newsletter_path, 'w', encoding='utf-8') as f:
            f.write(newsletter_html)
            
        logger.info("Successfully generated newsletter content")
        return newsletter_path
        
    except Exception as e:
        logger.error(f"Error generating newsletter content: {str(e)}")
        raise

if __name__ == '__main__':
    # Test the newsletter generator
    try:
        # Read news data
        with open('data/latest_mcp_news.json', 'r') as f:
            news_data = json.load(f)
            
        # Create test filenames
        date_str = datetime.now().strftime('%Y-%m-%d')
        test_filenames = {
            'tool': f"{date_str}_EP001_tool_spotlight.txt",
            'privacy': f"{date_str}_EP001_privacy_insight.txt",
            'community': f"{date_str}_EP001_community_corner.txt"
        }
        
        # Generate newsletter (using placeholder podcast link)
        result = generate_newsletter_content(
            test_filenames['tool'],
            test_filenames['privacy'],
            test_filenames['community'],
            1,  # Test episode number
            "Test Narrative Brief"
        )
        print("Newsletter generation successful!")
        
    except Exception as e:
        print(f"Error: {str(e)}")