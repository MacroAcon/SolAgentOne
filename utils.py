import os
import json
from typing import Dict, Any

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

def format_prompt(prompt: str, **kwargs) -> str:
    """
    Format a prompt string with the provided keyword arguments.
    
    Args:
        prompt: The prompt template string
        **kwargs: Keyword arguments to format the prompt
        
    Returns:
        Formatted prompt string
    """
    try:
        return prompt.format(**kwargs)
    except KeyError as e:
        raise ValueError(f"Missing required prompt variable: {str(e)}")
    except Exception as e:
        raise ValueError(f"Error formatting prompt: {str(e)}")

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