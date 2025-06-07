import os
import json
import logging
from typing import Dict, List, Optional
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('synthesis.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

def read_content_file(file_path: str) -> str:
    """
    Read content from a file.
    
    Args:
        file_path: Path to the content file
        
    Returns:
        Content as string
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        logger.error(f"Error reading file {file_path}: {str(e)}")
        return ""

def develop_narrative_theme(
    news_items: List[Dict],
    content_files: Dict[str, str],
    community_data: str
) -> str:
    """
    Develop a narrative theme that connects all content pieces.
    
    Args:
        news_items: List of news items from scraper
        content_files: Dictionary mapping content types to file paths
        community_data: Formatted community data string
        
    Returns:
        Narrative theme as a concise string
    """
    try:
        logger.info("Developing narrative theme")
        
        # Read content from files
        tool_content = read_content_file(content_files['tool_spotlight'])
        privacy_content = read_content_file(content_files['privacy_insight'])
        community_content = read_content_file(content_files['community_corner'])
        
        # Prepare the prompt
        prompt = f"""As a content strategist, analyze the following materials and identify a compelling narrative theme that connects them:

News Items:
{json.dumps(news_items, indent=2)}

Tool Spotlight:
{tool_content}

Privacy Insight:
{privacy_content}

Community Corner:
{community_content}

Community Discussions:
{community_data}

Requirements:
1. Identify a central theme or narrative thread that connects these elements
2. Look for surprising connections or patterns
3. Focus on what makes this week's content unique
4. Consider both technical and human aspects
5. Keep the theme concise (1-2 sentences)
6. Make it engaging and thought-provoking
7. Avoid generic themes or simple summaries

Develop a narrative brief that will guide the podcast and newsletter content:"""

        # Generate theme using GPT-4
        response = client.chat.completions.create(
            model=os.getenv('MODEL_SYNTHESIS', 'gpt-4'),
            messages=[
                {"role": "system", "content": "You are a content strategist specializing in technical storytelling."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=150
        )
        
        theme = response.choices[0].message.content.strip()
        logger.info(f"Developed narrative theme: {theme}")
        return theme
        
    except Exception as e:
        logger.error(f"Error developing narrative theme: {str(e)}")
        return "Error developing narrative theme"

if __name__ == '__main__':
    # Test the synthesis agent
    test_news = [
        {
            "title": "New MCP Feature Released",
            "link": "https://example.com/news1",
            "snippet": "Major update to MCP protocol..."
        }
    ]
    
    test_content_files = {
        'tool_spotlight': 'test_tool.txt',
        'privacy_insight': 'test_privacy.txt',
        'community_corner': 'test_community.txt'
    }
    
    test_community_data = "Test community discussions..."
    
    theme = develop_narrative_theme(test_news, test_content_files, test_community_data)
    print(f"\nDeveloped Theme:\n{theme}") 