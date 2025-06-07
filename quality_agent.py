import os
import json
import logging
from typing import Dict, Any
from openai import OpenAI
from dotenv import load_dotenv

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('quality.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

def run_quality_check(content_package: Dict[str, Any], episode_number: int) -> Dict[str, Any]:
    """
    Perform a quality check on the content package before publication.
    
    Args:
        content_package: Dictionary containing script, newsletter, and social posts
        episode_number: Current episode number
        
    Returns:
        Dictionary containing pass/fail status and feedback
    """
    try:
        logger.info(f"Starting quality check for episode {episode_number}")
        
        # Prepare the content package as a string
        content_package_str = json.dumps(content_package, indent=2)
        
        # Prepare the prompt
        prompt = f"""You are an editorial quality assurance agent for the 'Vibe Dev' podcast, episode {episode_number}.
Please review the following content package (podcast script, newsletter, social posts).

Check for the following:
1. **Consistency:** Is the tone and style consistent across all pieces?
2. **Brand Alignment:** Is the content professional, informative, and aligned with teaching AI tools and protocols?
3. **Factual Sanity Check:** Does it correctly reference episode number {episode_number}? Are there any glaring self-contradictions or nonsensical statements?

Respond in JSON format with two keys:
- "pass": a boolean (true if it passes, false if there are issues).
- "feedback": a string explaining any issues found or confirming it looks good.

Content Package:
{content_package_str}"""

        # Call GPT-4 for review
        response = client.chat.completions.create(
            model=os.getenv('MODEL_QUALITY', 'gpt-4'),
            messages=[
                {"role": "system", "content": "You are a thorough and professional content quality assurance agent."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,  # Lower temperature for more consistent output
            response_format={"type": "json_object"}  # Ensure JSON response
        )
        
        # Parse the response
        result = json.loads(response.choices[0].message.content)
        
        # Log the result
        if result['pass']:
            logger.info(f"Quality check passed for episode {episode_number}")
            logger.info(f"Feedback: {result['feedback']}")
        else:
            logger.warning(f"Quality check failed for episode {episode_number}")
            logger.warning(f"Feedback: {result['feedback']}")
        
        return result
        
    except Exception as e:
        logger.error(f"Error in quality check: {str(e)}")
        return {
            "pass": False,
            "feedback": f"Error during quality check: {str(e)}"
        }

if __name__ == "__main__":
    # Test the quality check with sample content
    test_package = {
        "script": "Sample podcast script content...",
        "newsletter_html": "<html>Sample newsletter content...</html>",
        "social_posts": ["Sample social post 1", "Sample social post 2"]
    }
    
    result = run_quality_check(test_package, 1)
    print(json.dumps(result, indent=2)) 