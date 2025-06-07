import os
import json
import logging
import requests
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Common API endpoints
SPOTIFY_TOKEN_URL = 'https://accounts.spotify.com/api/token'
SPOTIFY_API_BASE = 'https://api.spotify.com/v1'
SPOTIFY_PODCASTERS_API = 'https://api.spotify.com/v1/podcasters'

def setup_logging(name: str, log_file: Optional[str] = None) -> logging.Logger:
    """
    Set up logging configuration for a module.
    
    Args:
        name: Name of the logger
        log_file: Optional log file path
        
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    
    # Create formatter
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # Add file handler if specified
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    # Add stream handler
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)
    
    return logger

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
                'client_id': os.getenv('SPOTIFY_CLIENT_ID'),
                'client_secret': os.getenv('SPOTIFY_CLIENT_SECRET')
            }
        )
        response.raise_for_status()
        return response.json()['access_token']
    except Exception as e:
        raise Exception(f"Error getting Spotify access token: {str(e)}")

def get_spotify_headers() -> Dict[str, str]:
    """
    Get headers for Spotify API requests.
    
    Returns:
        Dict containing authorization headers
    """
    access_token = get_spotify_access_token()
    return {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }

def read_content_files(content_dir: str = 'data/content') -> Dict[str, Any]:
    """
    Read content files from the specified directory.
    
    Args:
        content_dir: Directory containing content files
        
    Returns:
        Dictionary containing content from all files
    """
    content = {}
    try:
        # Ensure directory exists
        os.makedirs(content_dir, exist_ok=True)
        
        # Read each content file
        for filename in os.listdir(content_dir):
            if filename.endswith('.json'):
                file_path = os.path.join(content_dir, filename)
                with open(file_path, 'r', encoding='utf-8') as f:
                    content_key = filename.replace('.json', '')
                    content[content_key] = json.load(f)
                    
        return content
    except Exception as e:
        raise Exception(f"Error reading content files: {str(e)}")

def get_openai_client():
    """
    Get an OpenAI client instance with proper configuration.
    
    Returns:
        OpenAI client instance
    """
    from openai import OpenAI
    return OpenAI()

def format_prompt(template: str, **kwargs) -> str:
    """
    Format a prompt template with the provided variables.
    
    Args:
        template: The prompt template string
        **kwargs: Variables to format into the template
        
    Returns:
        Formatted prompt string
    """
    return template.format(**kwargs)

def validate_required_env_vars(required_vars: list) -> None:
    """
    Validate that all required environment variables are set.
    
    Args:
        required_vars: List of required environment variable names
        
    Raises:
        ValueError: If any required variable is not set
    """
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    if missing_vars:
        raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")

def handle_api_error(error: Exception, logger: logging.Logger, default_return: Any = None) -> Any:
    """
    Handle API errors consistently across the application.
    
    Args:
        error: The exception that occurred
        logger: Logger instance to use
        default_return: Value to return in case of error
        
    Returns:
        The default_return value if an error occurred
    """
    if isinstance(error, requests.exceptions.RequestException):
        logger.error(f"API error: {str(error)}")
    else:
        logger.error(f"Error: {str(error)}")
    return default_return 