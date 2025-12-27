"""
Speech-to-Text Service
Implements STT using OpenAI Whisper API
"""

from typing import Protocol, Optional
from io import BytesIO
from app.config import settings
from app.voice.audio_utils import prepare_audio_for_whisper
import structlog

logger = structlog.get_logger()


class STTProvider(Protocol):
    """Protocol for Speech-to-Text providers"""
    async def transcribe_chunk(self, audio_bytes: bytes, language: Optional[str] = None) -> str:
        """
        Transcribe audio bytes to text
        
        Args:
            audio_bytes: Audio file bytes (WebM, WAV, MP3, etc.)
            language: Optional language code (e.g., 'en', 'es')
        
        Returns:
            Transcribed text
        """
        ...


class WhisperSTT:
    """
    OpenAI Whisper STT integration
    Uses OpenAI Whisper API for speech-to-text transcription
    """
    
    def __init__(self):
        """Initialize Whisper STT with OpenAI API key"""
        if not settings.openai_api_key:
            raise ValueError("OpenAI API key not configured. Set OPENAI_API_KEY environment variable.")
        
        try:
            from openai import OpenAI
            self.client = OpenAI(api_key=settings.openai_api_key)
        except ImportError:
            raise ImportError("OpenAI package not installed. Run: pip install openai")
        except Exception as e:
            logger.error("Failed to initialize OpenAI client for Whisper", error=str(e))
            raise ValueError(f"Failed to initialize OpenAI client: {str(e)}")
    
    async def transcribe_chunk(self, audio_bytes: bytes, language: Optional[str] = None) -> str:
        """
        Transcribe audio bytes to text using OpenAI Whisper API
        
        Args:
            audio_bytes: Audio file bytes (WebM, WAV, MP3, M4A, MP4, MPEG, MPGA)
            language: Optional language code (e.g., 'en', 'es', 'fr')
                     If None, Whisper will auto-detect the language
        
        Returns:
            Transcribed text
        
        Raises:
            ValueError: If audio bytes are invalid or API call fails
        """
        try:
            # Validate and prepare audio
            if not audio_bytes or len(audio_bytes) == 0:
                raise ValueError("Audio bytes are empty")
            
            # Check file size (Whisper API limit: 25MB)
            max_size = 25 * 1024 * 1024  # 25MB
            if len(audio_bytes) > max_size:
                raise ValueError(f"Audio file too large: {len(audio_bytes)} bytes. Maximum size: 25MB")
            
            # Prepare audio format
            audio_bytes_processed, file_extension = prepare_audio_for_whisper(audio_bytes)
            
            # Create a file-like object from bytes
            # OpenAI SDK requires a file-like object with a 'name' attribute
            audio_file = BytesIO(audio_bytes_processed)
            audio_file.name = f"audio.{file_extension}"
            
            # Call Whisper API
            # The API accepts: mp3, mp4, mpeg, mpga, m4a, wav, webm
            logger.info(
                "Calling Whisper API for transcription",
                audio_size=len(audio_bytes),
                format=file_extension,
                language=language or "auto-detect"
            )
            
            # Build request parameters
            request_params = {
                "file": audio_file,
                "model": "whisper-1",  # Whisper-1 is the only available model
            }
            
            # Add language if specified (helps with accuracy and performance)
            if language:
                request_params["language"] = language
            
            # Make API call
            # Note: The file pointer will be at the end after reading, but OpenAI SDK handles this
            response = self.client.audio.transcriptions.create(**request_params)
            
            transcribed_text = response.text
            
            logger.info(
                "Whisper transcription successful",
                text_length=len(transcribed_text),
                audio_size=len(audio_bytes)
            )
            
            return transcribed_text
            
        except Exception as e:
            logger.error("Whisper transcription failed", error=str(e), error_type=type(e).__name__)
            raise ValueError(f"Failed to transcribe audio: {str(e)}")


def get_stt_provider(provider_name: str) -> STTProvider:
    """
    Get STT provider instance
    
    Args:
        provider_name: Provider name ('whisper' or 'deepgram')
    
    Returns:
        STTProvider instance
    
    Note:
        Only Whisper is currently supported. Deepgram support removed.
    """
    provider_lower = provider_name.lower()
    
    if provider_lower == "whisper":
        return WhisperSTT()
    elif provider_lower == "deepgram":
        logger.warning("Deepgram provider requested but not implemented. Falling back to Whisper.")
        return WhisperSTT()
    else:
        logger.warning(f"Unknown STT provider: {provider_name}. Falling back to Whisper.")
        return WhisperSTT()


