import os
import json
import logging
from typing import List, Dict, Optional, Tuple
from datetime import datetime
from dotenv import load_dotenv
import requests
from serpapi import GoogleSearch
import time
import glob

from utils import (
    get_openai_client,
    format_prompt,
    validate_required_env_vars
)
from community_agent import get_community_topics, format_community_data

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Validate required environment variables
validate_required_env_vars(['OPENAI_API_KEY', 'SERPAPI_KEY'])

SERPAPI_KEY = os.getenv('SERPAPI_KEY')

def get_past_topics(file_path: str) -> List[str]:
    """
    Reads a log file of previously used topics/tools to avoid repetition.
    Returns a list of strings.
    If the file doesn't exist, it returns an empty list.
    """
    try:
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                return [line.strip() for line in f.readlines()]
        return []
    except Exception as e:
        logger.error(f"Error reading past topics from {file_path}: {str(e)}")
        return []

def update_past_topics(file_path: str, new_topic: str):
    """
    Appends a new topic to the log file.
    """
    try:
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, 'a') as f:
            f.write(f"{new_topic}\n")
        logger.info(f"Updated past topics in {file_path}")
    except Exception as e:
        logger.error(f"Error updating past topics in {file_path}: {str(e)}")

def get_historical_context() -> str:
    """
    Reads all transcript files from the history/transcripts/ directory
    and returns their content as a single string.
    """
    try:
        transcript_dir = 'history/transcripts'
        if not os.path.exists(transcript_dir):
            return ""
            
        all_content = []
        for transcript_file in glob.glob(f"{transcript_dir}/*_script.txt"):
            try:
                with open(transcript_file, 'r') as f:
                    content = f.read()
                    all_content.append(f"From {os.path.basename(transcript_file)}:\n{content}\n")
            except Exception as e:
                logger.error(f"Error reading transcript {transcript_file}: {str(e)}")
                
        return "\n".join(all_content)
    except Exception as e:
        logger.error(f"Error getting historical context: {str(e)}")
        return ""

def search_web(query: str, num_results: int = 5) -> List[Dict]:
    """
    Perform a web search using SerpAPI.
    Returns a list of search results with titles and snippets.
    """
    try:
        search = GoogleSearch({
            "q": query,
            "api_key": SERPAPI_KEY,
            "num": num_results
        })
        results = search.get_dict()
        
        if "organic_results" in results:
            return [
                {
                    "title": result.get("title", ""),
                    "snippet": result.get("snippet", ""),
                    "link": result.get("link", "")
                }
                for result in results["organic_results"]
            ]
        return []
    except Exception as e:
        logger.error(f"Error performing web search: {str(e)}")
        return []

def generate_content_with_gpt(
    content_type: str,
    historical_context: str,
    insights_summary: Optional[str] = None,
    community_data: Optional[str] = None,
    community_posts: Optional[List[Dict]] = None
) -> Tuple[str, List[str]]:
    """
    Generate content using GPT-4.
    
    Args:
        content_type: Type of content to generate
        historical_context: Historical context from past episodes
        insights_summary: Optional analytics insights
        community_data: Optional community topics from Reddit
        community_posts: Optional list of community post data
        
    Returns:
        Tuple of (generated content, list of featured post URLs)
    """
    try:
        # Get OpenAI client
        client = get_openai_client()
        
        # Prepare the prompt based on content type
        if content_type == "community_corner":
            prompt = format_prompt(
                """Generate a community corner segment for the MCP Updates podcast.
                
Past Episode Content:
{historical_context}

Analytics Insights:
{insights_summary}

Community Topics:
{community_data}

Requirements:
1. Focus on community discussions and trends
2. Highlight interesting projects or use cases
3. Include relevant quotes or insights from the community
4. Keep it engaging and informative
5. Avoid topics covered in past episodes
6. If you are discussing a topic that is a direct continuation of or is highly relevant to a topic covered in-depth in a previous episode, briefly mention it to connect the themes. For example: "This week we're looking at Y, which builds directly on our discussion about X back in episode 15." Use this sparingly and only when it adds significant value.
7. Length: 300-400 words
8. Identify which 1-2 Reddit posts are most relevant to your content

Format the response as a markdown document with clear sections.
At the end, include a list of the Reddit post URLs you primarily drew from, one per line, prefixed with "FEATURED_POSTS:".

Example:
FEATURED_POSTS:
https://reddit.com/r/LocalLLaMA/comments/abc123/post1
https://reddit.com/r/LocalLLaMA/comments/def456/post2""",
                historical_context=historical_context,
                insights_summary=insights_summary if insights_summary else 'No analytics data available',
                community_data=community_data if community_data else 'No community data available'
            )
            
        elif content_type == "tool_spotlight":
            prompt = format_prompt(
                """Generate a tool spotlight segment for the MCP Updates podcast.
                
Past Episode Content:
{historical_context}

Analytics Insights:
{insights_summary}

Community Topics:
{community_data}

Requirements:
1. Focus on a specific MCP tool or technology
2. Explain its key features and use cases
3. Include practical examples
4. Keep it engaging and informative
5. Avoid topics covered in past episodes
6. If you are discussing a tool that is a direct continuation of or is highly relevant to a tool covered in-depth in a previous episode, briefly mention it to connect the themes. For example: "This week we're looking at Y, which builds directly on our discussion about X back in episode 15." Use this sparingly and only when it adds significant value.
7. Length: 300-400 words

Format the response as a markdown document with clear sections.""",
                historical_context=historical_context,
                insights_summary=insights_summary if insights_summary else 'No analytics data available',
                community_data=community_data if community_data else 'No community data available'
            )
            
        else:  # privacy_insight
            prompt = format_prompt(
                """Generate a privacy insight segment for the MCP Updates podcast.
                
Past Episode Content:
{historical_context}

Analytics Insights:
{insights_summary}

Community Topics:
{community_data}

Requirements:
1. Focus on privacy implications and considerations
2. Include real-world examples and case studies
3. Provide actionable insights
4. Keep it engaging and informative
5. Avoid topics covered in past episodes
6. If you are discussing a privacy topic that is a direct continuation of or is highly relevant to a topic covered in-depth in a previous episode, briefly mention it to connect the themes. For example: "This week we're looking at Y, which builds directly on our discussion about X back in episode 15." Use this sparingly and only when it adds significant value.
7. Length: 300-400 words

Format the response as a markdown document with clear sections.""",
                historical_context=historical_context,
                insights_summary=insights_summary if insights_summary else 'No analytics data available',
                community_data=community_data if community_data else 'No community data available'
            )

        # Generate content using GPT-4
        response = client.chat.completions.create(
            model=os.getenv('MODEL_RESEARCHER', 'gpt-4'),
            messages=[
                {"role": "system", "content": "You are a technical writer specializing in MCP and privacy topics."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=1000
        )
        
        content = response.choices[0].message.content
        
        # Extract featured posts if this is community corner
        featured_posts = []
        if content_type == "community_corner":
            lines = content.split('\n')
            for line in lines:
                if line.startswith('FEATURED_POSTS:'):
                    # Get the next 1-2 lines as post URLs
                    for next_line in lines[lines.index(line) + 1:]:
                        if next_line.strip() and not next_line.startswith('FEATURED_POSTS:'):
                            featured_posts.append(next_line.strip())
                        if len(featured_posts) >= 2:  # Limit to 2 posts
                            break
                    break
            # Remove the FEATURED_POSTS section from the content
            content = '\n'.join(line for line in lines if not line.startswith('FEATURED_POSTS:'))
        
        return content, featured_posts
        
    except Exception as e:
        logger.error(f"Error generating {content_type} content: {str(e)}")
        raise

def research_and_write_content(episode_number: int, insights_summary: Optional[str] = None) -> Dict[str, str]:
    """
    Research and write content for the podcast episode.
    
    Args:
        episode_number: Current episode number
        insights_summary: Optional analytics insights summary
        
    Returns:
        Dictionary containing paths to generated content files and featured post URLs
    """
    try:
        # Get historical context
        historical_context = get_historical_context()
        
        # Get community topics
        community_topics = get_community_topics()
        community_data = format_community_data(community_topics)
        
        # Generate content for each section
        content_files = {}
        featured_posts = []
        
        for content_type in ['tool_spotlight', 'privacy_insight', 'community_corner']:
            content, posts = generate_content_with_gpt(
                content_type,
                historical_context,
                insights_summary,
                community_data
            )
            
            if posts:
                featured_posts.extend(posts)
            
            # Save content to file
            date_str = datetime.now().strftime('%Y-%m-%d')
            filename = f"{date_str}_EP{episode_number:03d}_{content_type}.txt"
            os.makedirs('data/content', exist_ok=True)
            
            with open(f"data/content/{filename}", 'w', encoding='utf-8') as f:
                f.write(content)
            
            content_files[content_type] = f"data/content/{filename}"
        
        # Add featured posts to the return value
        content_files['featured_posts'] = featured_posts
        
        return content_files
        
    except Exception as e:
        logger.error(f"Error in research_and_write_content: {str(e)}")
        raise

if __name__ == '__main__':
    # Test the researcher
    try:
        result = research_and_write_content(1)
        print("Content generation successful!")
        print(f"Generated files: {result}")
    except Exception as e:
        print(f"Error: {str(e)}")