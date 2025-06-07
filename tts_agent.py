import os
import logging
from elevenlabs import generate, set_api_key, Voice, VoiceSettings
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('tts.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Initialize ElevenLabs API key
set_api_key(os.getenv('ELEVENLABS_API_KEY'))

def generate_audio_from_script(script_path: str, output_path: str) -> bool:
    """
    Generate audio from a podcast script using ElevenLabs TTS.
    
    Args:
        script_path: Path to the input script file
        output_path: Path where the audio file should be saved
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Create output directory if it doesn't exist
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Read the script
        logger.info(f"Reading script from {script_path}")
        with open(script_path, 'r', encoding='utf-8') as f:
            script_content = f.read()
            
        # Configure voice settings for podcast-style narration
        voice_settings = VoiceSettings(
            stability=0.5,  # Balanced stability
            similarity_boost=0.75,  # Slightly higher similarity for consistency
            style=0.0,  # Neutral style
            use_speaker_boost=True  # Enhance voice clarity
        )
        
        # Use a professional podcast voice
        voice = Voice(
            voice_id="21m00Tcm4TlvDq8ikWAM",  # Rachel - Professional female voice
            settings=voice_settings
        )
        
        # Generate audio
        logger.info("Generating audio with ElevenLabs...")
        audio = generate(
            text=script_content,
            voice=voice,
            model=os.getenv('MODEL_TTS', 'eleven_multilingual_v2')  # Latest multilingual model
        )
        
        # Save the audio file
        logger.info(f"Saving audio to {output_path}")
        with open(output_path, 'wb') as f:
            f.write(audio)
            
        logger.info("Audio generation completed successfully")
        return True
        
    except FileNotFoundError:
        logger.error(f"Script file not found: {script_path}")
        return False
    except Exception as e:
        logger.error(f"Error generating audio: {str(e)}")
        return False

if __name__ == '__main__':
    # Test the TTS agent
    script_path = 'output/episode_script.txt'
    output_path = 'audio/episode.mp3'
    
    if generate_audio_from_script(script_path, output_path):
        print("Audio generation successful!")
    else:
        print("Audio generation failed. Check tts.log for details.") 