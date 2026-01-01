"""
Speech-to-Text Service
Implements STT using OpenAI Whisper API
"""

import time
from typing import Protocol, Optional
from uuid import UUID
from io import BytesIO
from app.config import settings
from app.voice.audio_utils import prepare_audio_for_whisper
from app.services.ai_usage_logger import AIUsageLogger
from app.services.cost_calculator import CostCalculator
import structlog

logger = structlog.get_logger()


class STTProvider(Protocol):
    """Protocol for Speech-to-Text providers"""
    async def transcribe_chunk(
        self,
        audio_bytes: bytes,
        language: Optional[str] = None,
        recruiter_id: Optional[UUID] = None,
        interview_id: Optional[UUID] = None,
        job_description_id: Optional[UUID] = None,
        candidate_id: Optional[UUID] = None
    ) -> str:
        """
        Transcribe audio bytes to text
        
        Args:
            audio_bytes: Audio file bytes (WebM, WAV, MP3, etc.)
            language: Optional language code (e.g., 'en', 'es')
            recruiter_id: Optional recruiter ID for logging
            interview_id: Optional interview ID for logging
            job_description_id: Optional job description ID for logging
            candidate_id: Optional candidate ID for logging
        
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
    
    async def transcribe_chunk(
        self,
        audio_bytes: bytes,
        language: Optional[str] = None,
        recruiter_id: Optional[UUID] = None,
        interview_id: Optional[UUID] = None,
        job_description_id: Optional[UUID] = None,
        candidate_id: Optional[UUID] = None
    ) -> str:
        """
        Transcribe audio bytes to text using OpenAI Whisper API
        
        Args:
            audio_bytes: Audio file bytes (WebM, WAV, MP3, M4A, MP4, MPEG, MPGA)
            language: Optional language code (e.g., 'en', 'es', 'fr')
                     If None, Whisper will auto-detect the language
            recruiter_id: Optional recruiter ID for logging
            interview_id: Optional interview ID for logging
            job_description_id: Optional job description ID for logging
            candidate_id: Optional candidate ID for logging
        
        Returns:
            Transcribed text
        
        Raises:
            ValueError: If audio bytes are invalid or API call fails
        """
        start_time = time.time()
        status = "success"
        error_message = None
        transcribed_text = None
        audio_duration_seconds = None
        
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
            
            # Estimate audio duration (rough: assume 64kbps encoding, ~8KB per second)
            # This is a rough estimate - actual duration would require audio parsing
            estimated_duration = len(audio_bytes) / 8000  # Rough estimate
            
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
            
            # Update duration estimate based on actual transcription
            # Whisper API doesn't return duration, so we'll use the estimate
            audio_duration_seconds = estimated_duration
            
            logger.info(
                "Whisper transcription successful",
                text_length=len(transcribed_text),
                audio_size=len(audio_bytes)
            )
            
            return transcribed_text
            
        except Exception as e:
            status = "error"
            error_message = str(e)
            logger.error("Whisper transcription failed", error=error_message, error_type=type(e).__name__)
            raise ValueError(f"Failed to transcribe audio: {str(e)}")
        finally:
            # Log usage (fire and forget - don't block on logging)
            if recruiter_id or interview_id:
                try:
                    latency_ms = int((time.time() - start_time) * 1000)
                    estimated_cost = float(CostCalculator.calculate_whisper_cost(audio_duration_seconds or 0))
                    
                    await AIUsageLogger.log_usage(
                        provider_name="whisper",
                        feature_name="stt_transcription",
                        recruiter_id=recruiter_id,
                        interview_id=interview_id,
                        job_description_id=job_description_id,
                        candidate_id=candidate_id,
                        model_name="whisper-1",
                        audio_duration_seconds=audio_duration_seconds,
                        estimated_cost_usd=estimated_cost,
                        latency_ms=latency_ms,
                        status=status,
                        error_message=error_message,
                    )
                except Exception as log_error:
                    # Don't fail the main operation if logging fails
                    logger.warning("Failed to log STT usage", error=str(log_error))


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


