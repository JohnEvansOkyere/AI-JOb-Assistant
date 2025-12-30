"""
AI Logging Helper
Helper functions to wrap AI providers with logging
"""

from typing import Optional, Dict, Any
from uuid import UUID
from app.ai.providers import AIProviderFactory
from app.ai.providers_wrapper import LoggedAIProvider
from app.services.ai_usage_context import get_interview_context, get_job_context
import structlog

logger = structlog.get_logger()


async def get_logged_provider_for_interview(
    interview_id: UUID,
    provider_name: Optional[str] = None,
    feature_name: str = "ai_completion"
) -> LoggedAIProvider:
    """
    Get a LoggedAIProvider with context from interview_id
    
    Args:
        interview_id: Interview ID to get context from
        provider_name: Optional provider name
        feature_name: Feature name for logging
        
    Returns:
        LoggedAIProvider instance (partial - context is set but feature_name is dynamic)
    """
    context = await get_interview_context(interview_id)
    provider = AIProviderFactory.create_provider(provider_name)
    logged_provider = LoggedAIProvider(provider, provider_name or "openai")
    # Store context for later use
    logged_provider._context = context
    logged_provider._default_feature = feature_name
    return logged_provider


async def get_logged_provider_for_job(
    job_description_id: UUID,
    provider_name: Optional[str] = None,
    feature_name: str = "ai_completion"
) -> LoggedAIProvider:
    """
    Get a LoggedAIProvider with context from job_description_id
    
    Args:
        job_description_id: Job description ID to get context from
        provider_name: Optional provider name
        feature_name: Feature name for logging
        
    Returns:
        LoggedAIProvider instance (partial - context is set but feature_name is dynamic)
    """
    context = await get_job_context(job_description_id)
    provider = AIProviderFactory.create_provider(provider_name)
    logged_provider = LoggedAIProvider(provider, provider_name or "openai")
    # Store context for later use
    logged_provider._context = context
    logged_provider._default_feature = feature_name
    return logged_provider

