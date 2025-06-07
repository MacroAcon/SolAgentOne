import os
import logging
import requests
import openai
from typing import Optional
from dotenv import load_dotenv
from io import BytesIO

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configure OpenAI
openai.api_key = os.getenv('OPENAI_API_KEY')

# Configure Imgur
IMGUR_CLIENT_ID = os.getenv('IMGUR_CLIENT_ID')
IMGUR_UPLOAD_URL = 'https://api.imgur.com/3/image'

def generate_image(prompt: str) -> Optional[str]:
    """
    Generate an image using DALL-E 3 based on the provided prompt.
    Returns the URL of the generated image or None if generation fails.
    """
    try:
        logger.info(f"Generating image with prompt: {prompt}")
        
        # Create a more detailed prompt for DALL-E
        enhanced_prompt = f"""Create a professional, modern tech newsletter header image that represents: {prompt}
        Style: Clean, minimalist, tech-focused, suitable for a developer newsletter.
        Format: Landscape orientation, 1200x600 pixels.
        Colors: Use a professional color palette with blues and whites.
        No text or words in the image."""
        
        response = openai.images.generate(
            model=os.getenv('MODEL_IMAGE', 'dall-e-3'),
            prompt=enhanced_prompt,
            size="1024x1024",
            quality="standard",
            n=1
        )
        
        image_url = response.data[0].url
        logger.info("Successfully generated image with DALL-E 3")
        return image_url
        
    except Exception as e:
        logger.error(f"Error generating image with DALL-E: {str(e)}")
        return None

def upload_image_to_imgur(image_url: str) -> Optional[str]:
    """
    Download the image from the provided URL and upload it to Imgur.
    Returns the direct image link from Imgur or None if upload fails.
    """
    try:
        logger.info("Downloading image from DALL-E URL")
        
        # Download the image
        response = requests.get(image_url)
        response.raise_for_status()
        
        # Prepare the image data for Imgur upload
        image_data = BytesIO(response.content)
        
        # Upload to Imgur
        logger.info("Uploading image to Imgur")
        headers = {'Authorization': f'Client-ID {IMGUR_CLIENT_ID}'}
        files = {'image': image_data}
        
        response = requests.post(IMGUR_UPLOAD_URL, headers=headers, files=files)
        response.raise_for_status()
        
        # Get the direct image link
        imgur_data = response.json()
        if imgur_data['success']:
            direct_link = imgur_data['data']['link']
            logger.info("Successfully uploaded image to Imgur")
            return direct_link
        else:
            logger.error(f"Imgur API returned success=false: {imgur_data}")
            return None
            
    except Exception as e:
        logger.error(f"Error uploading image to Imgur: {str(e)}")
        return None

def create_newsletter_image(headline: str) -> Optional[str]:
    """
    Main function to generate and upload a newsletter header image.
    Takes a headline as input and returns the final Imgur image URL.
    """
    try:
        logger.info(f"Creating newsletter image for headline: {headline}")
        
        # Generate the image
        image_url = generate_image(headline)
        if not image_url:
            logger.error("Failed to generate image with DALL-E")
            return None
            
        # Upload to Imgur
        imgur_url = upload_image_to_imgur(image_url)
        if not imgur_url:
            logger.error("Failed to upload image to Imgur")
            return None
            
        logger.info("Successfully created and uploaded newsletter image")
        return imgur_url
        
    except Exception as e:
        logger.error(f"Error in create_newsletter_image: {str(e)}")
        return None

if __name__ == '__main__':
    # Test the image generator
    test_headline = "OpenAI Releases GPT-4 Turbo with Enhanced Capabilities"
    try:
        image_url = create_newsletter_image(test_headline)
        if image_url:
            print(f"Successfully created newsletter image: {image_url}")
        else:
            print("Failed to create newsletter image")
    except Exception as e:
        print(f"Error: {str(e)}") 