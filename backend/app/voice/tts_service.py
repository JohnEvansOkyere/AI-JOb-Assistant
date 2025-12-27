"""
Text-to-Speech Service
Implements TTS using ElevenLabs API
"""

from typing import Protocol
from app.config import settings
import structlog

logger = structlog.get_logger()


class TTSProvider(Protocol):
    """Protocol for Text-to-Speech providers"""
    async def synthesize(self, text: str) -> bytes:
        """
        Convert text to speech audio
        
        Args:
            text: Text to synthesize
        
        Returns:
            Audio bytes (MP3 format)
        """
        ...


class ElevenLabsTTS:
    """
    ElevenLabs TTS integration
    Uses ElevenLabs API for text-to-speech synthesis
    """
    
    def __init__(self):
        """Initialize ElevenLabs TTS with API key and voice ID"""
        if not settings.elevenlabs_api_key:
            raise ValueError(
                "ElevenLabs API key not configured. Set ELEVENLABS_API_KEY environment variable."
            )
        
        if not settings.elevenlabs_voice_id:
            raise ValueError(
                "ElevenLabs Voice ID not configured. Set ELEVENLABS_VOICE_ID environment variable."
            )
        
        try:
            from elevenlabs import generate, set_api_key
            
            # Set API key for ElevenLabs SDK
            set_api_key(settings.elevenlabs_api_key)
            self.generate_func = generate
            self.voice_id = settings.elevenlabs_voice_id
        except ImportError:
            raise ImportError("ElevenLabs package not installed. Run: pip install elevenlabs")
        except Exception as e:
            logger.error("Failed to initialize ElevenLabs", error=str(e))
            raise ValueError(f"Failed to initialize ElevenLabs: {str(e)}")
    
    async def synthesize(self, text: str) -> bytes:
        """
        Convert text to speech audio using ElevenLabs API
        
        Args:
            text: Text to synthesize to speech
        
        Returns:
            Audio bytes (MP3 format)
        
        Raises:
            ValueError: If text is empty or API call fails
        """
        try:
            # Validate input
            if not text or len(text.strip()) == 0:
                raise ValueError("Text cannot be empty")
            
            # Limit text length (ElevenLabs has limits based on plan)
            max_chars = 5000  # Conservative limit (most plans support more)
            if len(text) > max_chars:
                logger.warning(
                    "Text exceeds recommended length, truncating",
                    original_length=len(text),
                    max_length=max_chars
                )
                text = text[:max_chars]
            
            logger.info(
                "Calling ElevenLabs API for TTS",
                text_length=len(text),
                voice_id=self.voice_id
            )
            
            # Generate speech using ElevenLabs API
            # The generate() function returns audio bytes (MP3 format)
            audio_bytes = self.generate_func(
                text=text,
                voice=self.voice_id,
                model="eleven_multilingual_v2"  # Use multilingual model for better language support
            )
            
            # Convert generator/stream to bytes if needed
            if hasattr(audio_bytes, '__iter__') and not isinstance(audio_bytes, (bytes, bytearray)):
                # If it's a generator/stream, read all chunks
                audio_chunks = list(audio_bytes)
                audio_bytes = b''.join(
                    chunk if isinstance(chunk, bytes) else bytes(chunk)
                    for chunk in audio_chunks
                )
            
            logger.info(
                "ElevenLabs TTS synthesis successful",
                text_length=len(text),
                audio_size=len(audio_bytes)
            )
            
            return audio_bytes
            
        except Exception as e:
            logger.error(
                "ElevenLabs TTS synthesis failed",
                error=str(e),
                error_type=type(e).__name__,
                text_length=len(text) if text else 0
            )
            raise ValueError(f"Failed to synthesize speech: {str(e)}")


def get_tts_provider() -> TTSProvider:
    """
    Get TTS provider instance
    
    Returns:
        TTSProvider instance (currently only ElevenLabs supported)
    
    Raises:
        ValueError: If ElevenLabs is not configured
    """
    return ElevenLabsTTS()

