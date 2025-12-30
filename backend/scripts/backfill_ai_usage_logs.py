"""
Backfill AI Usage Logs
Estimates and creates AI usage logs for existing interviews
This provides historical data for the admin dashboard
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from uuid import UUID
from datetime import datetime
from app.database import db
from app.services.cost_calculator import CostCalculator
from app.config import settings
import structlog

logger = structlog.get_logger()


async def backfill_usage_logs():
    """
    Backfill AI usage logs for existing interviews
    Estimates usage based on interview data
    """
    try:
        # Get all completed interviews
        interviews_response = (
            db.service_client.table("interviews")
            .select("id, job_description_id, candidate_id, created_at, interview_mode, duration_seconds")
            .eq("status", "completed")
            .execute()
        )
        
        interviews = interviews_response.data or []
        logger.info(f"Found {len(interviews)} completed interviews to backfill")
        
        backfilled_count = 0
        
        for interview in interviews:
            try:
                interview_id = UUID(interview["id"])
                job_description_id = UUID(interview["job_description_id"])
                candidate_id = UUID(interview["candidate_id"])
                interview_mode = interview.get("interview_mode", "text")
                created_at = interview.get("created_at")
                
                # Get recruiter_id from job_description
                job_response = (
                    db.service_client.table("job_descriptions")
                    .select("recruiter_id")
                    .eq("id", str(job_description_id))
                    .execute()
                )
                
                if not job_response.data:
                    logger.warning(f"Job not found for interview {interview_id}")
                    continue
                
                recruiter_id = UUID(job_response.data[0]["recruiter_id"])
                
                # Get questions and responses to estimate usage
                questions_response = (
                    db.service_client.table("interview_questions")
                    .select("id, question_text, order_index")
                    .eq("interview_id", str(interview_id))
                    .order("order_index")
                    .execute()
                )
                questions = questions_response.data or []
                
                responses_response = (
                    db.service_client.table("interview_responses")
                    .select("id, response_text")
                    .eq("interview_id", str(interview_id))
                    .execute()
                )
                responses = responses_response.data or []
                
                # Estimate OpenAI tokens for question generation
                # Rough estimate: 500 tokens per question (prompt + completion)
                total_questions = len(questions)
                if total_questions > 0:
                    estimated_tokens_per_question = 500
                    total_tokens = total_questions * estimated_tokens_per_question
                    
                    # Log question generation (one log entry for all questions)
                    cost = float(CostCalculator.calculate_cost(
                        provider_name="openai",
                        model_name=settings.openai_model,
                        total_tokens=total_tokens
                    ))
                    
                    await log_usage(
                        provider_name="openai",
                        feature_name="question_generation",
                        recruiter_id=recruiter_id,
                        interview_id=interview_id,
                        job_description_id=job_description_id,
                        candidate_id=candidate_id,
                        model_name=settings.openai_model,
                        total_tokens=total_tokens,
                        estimated_cost_usd=cost,
                        created_at=created_at
                    )
                
                # Estimate OpenAI tokens for response analysis
                # Rough estimate: 300 tokens per response analysis
                for response in responses:
                    response_tokens = 300
                    cost = float(CostCalculator.calculate_cost(
                        provider_name="openai",
                        model_name=settings.openai_model,
                        total_tokens=response_tokens
                    ))
                    
                    await log_usage(
                        provider_name="openai",
                        feature_name="response_analysis",
                        recruiter_id=recruiter_id,
                        interview_id=interview_id,
                        job_description_id=job_description_id,
                        candidate_id=candidate_id,
                        model_name=settings.openai_model,
                        total_tokens=response_tokens,
                        estimated_cost_usd=cost,
                        created_at=created_at
                    )
                
                # Estimate ElevenLabs TTS usage for voice interviews
                if interview_mode == "voice" and total_questions > 0:
                    # Estimate: average 100 characters per question
                    total_characters = total_questions * 100
                    cost = float(CostCalculator.calculate_elevenlabs_cost(total_characters))
                    
                    await log_usage(
                        provider_name="elevenlabs",
                        feature_name="tts_synthesis",
                        recruiter_id=recruiter_id,
                        interview_id=interview_id,
                        job_description_id=job_description_id,
                        candidate_id=candidate_id,
                        model_name="eleven_multilingual_v2",
                        characters_used=total_characters,
                        estimated_cost_usd=cost,
                        created_at=created_at
                    )
                    
                    # Estimate Whisper STT usage
                    # Estimate: 30 seconds per response
                    duration_seconds = interview.get("duration_seconds", len(responses) * 30)
                    if duration_seconds:
                        cost = float(CostCalculator.calculate_whisper_cost(duration_seconds))
                        
                        await log_usage(
                            provider_name="whisper",
                            feature_name="stt_transcription",
                            recruiter_id=recruiter_id,
                            interview_id=interview_id,
                            job_description_id=job_description_id,
                            candidate_id=candidate_id,
                            audio_duration_seconds=duration_seconds,
                            estimated_cost_usd=cost,
                            created_at=created_at
                        )
                
                # Check if there's a detailed analysis
                analysis_response = (
                    db.service_client.table("detailed_interview_analysis")
                    .select("id, created_at")
                    .eq("interview_id", str(interview_id))
                    .execute()
                )
                
                if analysis_response.data:
                    # Estimate tokens for comprehensive analysis: 2000 tokens
                    analysis_tokens = 2000
                    cost = float(CostCalculator.calculate_cost(
                        provider_name="openai",
                        model_name=settings.openai_model,
                        total_tokens=analysis_tokens
                    ))
                    
                    analysis_created_at = analysis_response.data[0].get("created_at", created_at)
                    
                    await log_usage(
                        provider_name="openai",
                        feature_name="interview_analysis",
                        recruiter_id=recruiter_id,
                        interview_id=interview_id,
                        job_description_id=job_description_id,
                        candidate_id=candidate_id,
                        model_name=settings.openai_model,
                        total_tokens=analysis_tokens,
                        estimated_cost_usd=cost,
                        created_at=analysis_created_at
                    )
                
                backfilled_count += 1
                
                if backfilled_count % 10 == 0:
                    logger.info(f"Backfilled {backfilled_count} interviews...")
                    
            except Exception as e:
                logger.error(f"Error backfilling interview {interview.get('id')}", error=str(e))
                continue
        
        logger.info(f"Backfill complete! Processed {backfilled_count} interviews")
        
    except Exception as e:
        logger.error("Error during backfill", error=str(e))
        raise


async def log_usage(
    provider_name: str,
    feature_name: str,
    recruiter_id: UUID,
    interview_id: UUID,
    job_description_id: UUID,
    candidate_id: UUID,
    model_name: str = None,
    total_tokens: int = None,
    characters_used: int = None,
    audio_duration_seconds: float = None,
    estimated_cost_usd: float = 0.0,
    created_at: str = None
):
    """Helper to log usage"""
    try:
        log_data = {
            "recruiter_id": str(recruiter_id),
            "user_id": str(recruiter_id),
            "interview_id": str(interview_id),
            "job_description_id": str(job_description_id),
            "candidate_id": str(candidate_id),
            "provider_name": provider_name,
            "feature_name": feature_name,
            "model_name": model_name,
            "total_tokens": total_tokens,
            "characters_used": characters_used,
            "audio_duration_seconds": audio_duration_seconds,
            "estimated_cost_usd": estimated_cost_usd,
            "status": "success",
        }
        
        # Set created_at if provided
        if created_at:
            log_data["created_at"] = created_at
        
        # Remove None values
        log_data = {k: v for k, v in log_data.items() if v is not None}
        
        db.service_client.table("ai_usage_logs").insert(log_data).execute()
        
    except Exception as e:
        logger.warning(f"Failed to log usage for interview {interview_id}", error=str(e))


if __name__ == "__main__":
    asyncio.run(backfill_usage_logs())

