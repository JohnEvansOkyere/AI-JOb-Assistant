"""
AI Usage Logger Service
Tracks all AI service usage for cost monitoring and analytics
"""

from typing import Optional, Dict, Any
from uuid import UUID
from datetime import datetime
from app.database import db
import structlog

logger = structlog.get_logger()


class AIUsageLogger:
    """Service for logging AI usage to database"""
    
    @staticmethod
    async def log_usage(
        provider_name: str,
        feature_name: str,
        recruiter_id: Optional[UUID] = None,
        interview_id: Optional[UUID] = None,
        job_description_id: Optional[UUID] = None,
        candidate_id: Optional[UUID] = None,
        model_name: Optional[str] = None,
        prompt_tokens: Optional[int] = None,
        completion_tokens: Optional[int] = None,
        total_tokens: Optional[int] = None,
        characters_used: Optional[int] = None,
        audio_duration_seconds: Optional[float] = None,
        estimated_cost_usd: float = 0.0,
        latency_ms: Optional[int] = None,
        status: str = "success",
        error_message: Optional[str] = None,
        prompt_version: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> UUID:
        """
        Log AI usage to database
        
        Args:
            provider_name: AI provider name (openai, groq, gemini, elevenlabs, whisper, deepgram)
            feature_name: Feature name (question_generation, response_analysis, tts_synthesis, etc.)
            recruiter_id: User/recruiter ID
            interview_id: Interview ID (if applicable)
            job_description_id: Job description ID (if applicable)
            candidate_id: Candidate ID (if applicable)
            model_name: Model name (e.g., gpt-4o-mini)
            prompt_tokens: Prompt tokens (for LLM providers)
            completion_tokens: Completion tokens (for LLM providers)
            total_tokens: Total tokens (for LLM providers)
            characters_used: Characters used (for TTS providers)
            audio_duration_seconds: Audio duration in seconds (for STT/TTS)
            estimated_cost_usd: Estimated cost in USD
            latency_ms: Request latency in milliseconds
            status: Status (success, failure, error)
            error_message: Error message if status is not success
            prompt_version: Prompt version identifier
            metadata: Additional metadata as JSON
            
        Returns:
            Log entry ID
        """
        try:
            log_data = {
                "recruiter_id": str(recruiter_id) if recruiter_id else None,
                "user_id": str(recruiter_id) if recruiter_id else None,  # Same as recruiter_id
                "interview_id": str(interview_id) if interview_id else None,
                "job_description_id": str(job_description_id) if job_description_id else None,
                "candidate_id": str(candidate_id) if candidate_id else None,
                "provider_name": provider_name,
                "model_name": model_name,
                "feature_name": feature_name,
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": total_tokens,
                "characters_used": characters_used,
                "audio_duration_seconds": audio_duration_seconds,
                "estimated_cost_usd": estimated_cost_usd,
                "latency_ms": latency_ms,
                "status": status,
                "error_message": error_message,
                "prompt_version": prompt_version,
                "metadata": metadata,
            }
            
            # Remove None values to let database use defaults
            log_data = {k: v for k, v in log_data.items() if v is not None}
            
            response = db.service_client.table("ai_usage_logs").insert(log_data).execute()
            
            if response.data and len(response.data) > 0:
                log_id = response.data[0]["id"]
                logger.debug(
                    "AI usage logged",
                    log_id=str(log_id),
                    provider=provider_name,
                    feature=feature_name,
                    cost_usd=estimated_cost_usd
                )
                return UUID(log_id)
            else:
                logger.warning("Failed to insert AI usage log - no data returned")
                raise ValueError("Failed to insert AI usage log")
                
        except Exception as e:
            # Don't fail the main operation if logging fails
            logger.error(
                "Failed to log AI usage",
                error=str(e),
                provider=provider_name,
                feature=feature_name
            )
            # Return a dummy UUID so the calling code doesn't break
            # In production, you might want to use a background task for logging
            raise  # Re-raise for now to catch issues during development

