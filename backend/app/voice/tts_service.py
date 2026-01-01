"""
Text-to-Speech Service
Implements TTS using ElevenLabs API
"""

import time
from typing import Protocol, Optional
from uuid import UUID
from app.config import settings
from app.services.ai_usage_logger import AIUsageLogger
from app.services.cost_calculator import CostCalculator
import structlog

logger = structlog.get_logger()


class TTSProvider(Protocol):
    """Protocol for Text-to-Speech providers"""
    async def synthesize(
        self,
        text: str,
        recruiter_id: Optional[UUID] = None,
        interview_id: Optional[UUID] = None,
        job_description_id: Optional[UUID] = None,
        candidate_id: Optional[UUID] = None
    ) -> bytes:
        """
        Convert text to speech audio
        
        Args:
            text: Text to synthesize
            recruiter_id: Optional recruiter ID for logging
            interview_id: Optional interview ID for logging
            job_description_id: Optional job description ID for logging
            candidate_id: Optional candidate ID for logging
        
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
    
    async def synthesize(
        self,
        text: str,
        recruiter_id: Optional[UUID] = None,
        interview_id: Optional[UUID] = None,
        job_description_id: Optional[UUID] = None,
        candidate_id: Optional[UUID] = None
    ) -> bytes:
        """
        Convert text to speech audio using ElevenLabs API
        
        Args:
            text: Text to synthesize to speech
            recruiter_id: Optional recruiter ID for logging
            interview_id: Optional interview ID for logging
            job_description_id: Optional job description ID for logging
            candidate_id: Optional candidate ID for logging
        
        Returns:
            Audio bytes (MP3 format)
        
        Raises:
            ValueError: If text is empty or API call fails
        """
        start_time = time.time()
        status = "success"
        error_message = None
        audio_bytes = None
        characters_used = 0
        
        try:
            # Validate input
            if not text or len(text.strip()) == 0:
                raise ValueError("Text cannot be empty")
            
            # Limit text length (ElevenLabs has limits based on plan)
            max_chars = 5000  # Conservative limit (most plans support more)
            original_length = len(text)
            if original_length > max_chars:
                logger.warning(
                    "Text exceeds recommended length, truncating",
                    original_length=original_length,
                    max_length=max_chars
                )
                text = text[:max_chars]
            
            characters_used = len(text)  # Use actual characters sent
            
            logger.info(
                "Calling ElevenLabs API for TTS",
                text_length=characters_used,
                voice_id=self.voice_id
            )
            
            # Generate speech using ElevenLabs API
            # The generate() function may return audio bytes or a generator/stream
            audio_result = self.generate_func(
                text=text,
                voice=self.voice_id,
                model="eleven_multilingual_v2"  # Use multilingual model for better language support
            )
            
            # Convert generator/stream to bytes if needed
            # ElevenLabs can return either bytes directly or an iterable generator
            if isinstance(audio_result, bytes):
                audio_bytes = audio_result
            elif isinstance(audio_result, bytearray):
                audio_bytes = bytes(audio_result)
            elif hasattr(audio_result, '__iter__'):
                # If it's a generator/stream, read all chunks
                audio_chunks = []
                for chunk in audio_result:
                    if isinstance(chunk, bytes):
                        audio_chunks.append(chunk)
                    elif isinstance(chunk, bytearray):
                        audio_chunks.append(bytes(chunk))
                    else:
                        try:
                            audio_chunks.append(bytes(chunk))
                        except (TypeError, ValueError) as e:
                            raise ValueError(f"Unable to convert audio chunk to bytes: {type(chunk)} - {e}")
                audio_bytes = b''.join(audio_chunks)
            else:
                raise TypeError(f"Unexpected audio type from ElevenLabs: {type(audio_result)}")
            
            # Validate we got actual audio data
            if not audio_bytes or len(audio_bytes) == 0:
                raise ValueError("ElevenLabs returned empty audio data")
            
            logger.info(
                "ElevenLabs TTS synthesis successful",
                text_length=characters_used,
                audio_size=len(audio_bytes)
            )
            
            return audio_bytes
            
        except Exception as e:
            status = "error"
            error_message = str(e)
            logger.error(
                "ElevenLabs TTS synthesis failed",
                error=error_message,
                error_type=type(e).__name__,
                text_length=characters_used
            )
            raise ValueError(f"Failed to synthesize speech: {str(e)}")
        finally:
            # Log usage (fire and forget - don't block on logging)
            if recruiter_id or interview_id:
                try:
                    latency_ms = int((time.time() - start_time) * 1000)
                    estimated_cost = float(CostCalculator.calculate_elevenlabs_cost(characters_used))
                    
                    await AIUsageLogger.log_usage(
                        provider_name="elevenlabs",
                        feature_name="tts_synthesis",
                        recruiter_id=recruiter_id,
                        interview_id=interview_id,
                        job_description_id=job_description_id,
                        candidate_id=candidate_id,
                        model_name="eleven_multilingual_v2",
                        characters_used=characters_used,
                        estimated_cost_usd=estimated_cost,
                        latency_ms=latency_ms,
                        status=status,
                        error_message=error_message,
                    )
                except Exception as log_error:
                    # Don't fail the main operation if logging fails
                    logger.warning("Failed to log TTS usage", error=str(log_error))


def get_tts_provider() -> TTSProvider:
    """
    Get TTS provider instance
    
    Returns:
        TTSProvider instance (currently only ElevenLabs supported)
    
    Raises:
        ValueError: If ElevenLabs is not configured
    """
    return ElevenLabsTTS()

