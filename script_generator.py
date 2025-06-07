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

def generate_podcast_script(
    tool_filename: str,
    privacy_filename: str,
    community_filename: str,
    episode_number: int,
    narrative_brief: str
) -> Dict[str, str]:
    """
    Generate podcast script and show notes.
    
    Args:
        tool_filename: Path to tool spotlight content
        privacy_filename: Path to privacy insight content
        community_filename: Path to community corner content
        episode_number: Current episode number
        narrative_brief: Narrative theme for the episode
        
    Returns:
        Dictionary containing paths to script and show notes files
    """
    try:
        logger.info("Generating podcast script")
        
        # Read content files
        content = read_content_files()
        tool_content = content.get('tool', '')
        privacy_content = content.get('privacy', '')
        community_content = content.get('community', '')
        
        # Get OpenAI client
        client = get_openai_client()
        
        # Prepare the prompt
        prompt = format_prompt(
            """Create a podcast script for MCP Updates Episode {episode_number}.

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
1. Use the narrative theme as the central thread throughout the episode
2. Create smooth transitions between segments that reinforce the theme
3. Include engaging introductions and conclusions
4. Add natural conversation elements and segues
5. Keep the tone professional yet conversational
6. Include timestamps for each segment
7. Add relevant sound effects or music cues
8. Length: 30-45 minutes

Format the script with clear sections and timestamps.""",
            episode_number=episode_number,
            narrative_brief=narrative_brief,
            tool_content=tool_content,
            privacy_content=privacy_content,
            community_content=community_content
        )

        # Generate script using GPT-4
        response = client.chat.completions.create(
            model=os.getenv('MODEL_SCRIPTWRITER', 'gpt-4'),
            messages=[
                {"role": "system", "content": "You are a professional podcast scriptwriter."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=2000
        )
        
        script = response.choices[0].message.content
        
        # Generate show notes
        show_notes_prompt = format_prompt(
            """Create show notes for MCP Updates Episode {episode_number}.

Narrative Theme:
{narrative_brief}

Script:
{script}

Requirements:
1. Summarize the episode's key points
2. Include relevant links and resources
3. Highlight the narrative theme
4. Add timestamps for easy navigation
5. Keep it concise and engaging
6. Format in markdown

Create the show notes:""",
            episode_number=episode_number,
            narrative_brief=narrative_brief,
            script=script
        )

        show_notes_response = client.chat.completions.create(
            model=os.getenv('MODEL_SCRIPTWRITER', 'gpt-4'),
            messages=[
                {"role": "system", "content": "You are a professional podcast show notes writer."},
                {"role": "user", "content": show_notes_prompt}
            ],
            temperature=0.7,
            max_tokens=1000
        )
        
        show_notes = show_notes_response.choices[0].message.content
        
        # Save files
        os.makedirs('output', exist_ok=True)
        script_path = 'output/episode_script.txt'
        show_notes_path = 'output/show_notes.md'
        
        with open(script_path, 'w', encoding='utf-8') as f:
            f.write(script)
            
        with open(show_notes_path, 'w', encoding='utf-8') as f:
            f.write(show_notes)
            
        logger.info("Successfully generated podcast script and show notes")
        return {
            'script': script_path,
            'show_notes': show_notes_path
        }
        
    except Exception as e:
        logger.error(f"Error generating podcast script: {str(e)}")
        raise

def get_insights_prompt(insights_summary: str) -> str:
    """
    Generate the insights prompt section.
    
    Args:
        insights_summary: Summary of last week's performance
        
    Returns:
        Formatted insights prompt
    """
    if not insights_summary:
        return ""
        
    return f"""
Here is a summary of last week's performance to help guide your script writing:
<Last Week's Insights>
{insights_summary}
</Last Week's Insights>

Use these insights to inform your script structure and content. For example:
- If certain segments performed well, maintain their style and format
- If technical explanations were well-received, maintain that level of detail
- If community content engaged well, emphasize similar aspects
"""

if __name__ == '__main__':
    # Test the script generator
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
        
        # Generate script
        result = generate_podcast_script(
            test_filenames['tool'],
            test_filenames['privacy'],
            test_filenames['community'],
            1,  # Test episode number
            "The latest developments in MCP (Machine Conversation Protocol)"  # Test narrative brief
        )
        print("Script generation successful!")
        
    except Exception as e:
        print(f"Error: {str(e)}")