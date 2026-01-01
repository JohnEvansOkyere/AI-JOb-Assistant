"""
AI Providers Wrapper
Wraps AI provider calls with usage logging and cost tracking
"""

import time
from typing import Optional, Dict, Any
from uuid import UUID
from decimal import Decimal
from app.ai.providers import AIProvider
from app.services.ai_usage_logger import AIUsageLogger
from app.services.cost_calculator import CostCalculator
from app.services.usage_limit_checker import UsageLimitChecker
import structlog

logger = structlog.get_logger()


class LoggedAIProvider:
    """
    Wrapper around AIProvider that logs all usage
    """
    
    def __init__(self, provider: AIProvider, provider_name: str):
        self.provider = provider
        self.provider_name = provider_name
    
    async def generate_completion(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: float = 0.7,
        # Logging context
        recruiter_id: Optional[UUID] = None,
        interview_id: Optional[UUID] = None,
        job_description_id: Optional[UUID] = None,
        candidate_id: Optional[UUID] = None,
        feature_name: str = "ai_completion",
        prompt_version: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Generate completion with logging
        """
        start_time = time.time()
        status = "success"
        error_message = None
        result = None
        prompt_tokens = None
        completion_tokens = None
        total_tokens = None
        
        try:
            # Estimate cost before making the call to check limits
            # This is an approximation - we'll use actual usage after the call
            if recruiter_id:
                # Estimate tokens for cost checking (rough estimate)
                full_prompt = (system_prompt or "") + "\n\n" + prompt
                estimated_prompt_tokens = self.provider.get_token_count(full_prompt)
                # Estimate completion tokens (typically 20-30% of prompt for most queries)
                estimated_completion_tokens = int(estimated_prompt_tokens * 0.25) if max_tokens else 300
                estimated_total_tokens = estimated_prompt_tokens + estimated_completion_tokens
                
                # Calculate estimated cost
                model_name = getattr(self.provider, 'model', None) or getattr(self.provider, 'model_name', None)
                estimated_cost = CostCalculator.calculate_cost(
                    provider_name=self.provider_name,
                    model_name=model_name,
                    prompt_tokens=estimated_prompt_tokens,
                    completion_tokens=estimated_completion_tokens,
                    total_tokens=estimated_total_tokens
                )
                
                # Check cost limits before making the API call
                try:
                    await UsageLimitChecker.check_all_limits(
                        recruiter_id=recruiter_id,
                        check_interview_limit=False,  # Already checked when creating interview
                        check_cost_limit=True,
                        estimated_cost=estimated_cost
                    )
                except Exception as limit_error:
                    # Check if it's a UsageLimitError
                    if hasattr(limit_error, 'limit_type'):
                        from fastapi import HTTPException, status
                        raise HTTPException(
                            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                            detail=str(limit_error)
                        )
                    raise
            
            result = await self.provider.generate_completion(
                prompt=prompt,
                system_prompt=system_prompt,
                max_tokens=max_tokens,
                temperature=temperature
            )
            
            # Try to get actual usage from provider (if available)
            if hasattr(self.provider, '_last_usage') and self.provider._last_usage:
                prompt_tokens = self.provider._last_usage.get("prompt_tokens")
                completion_tokens = self.provider._last_usage.get("completion_tokens")
                total_tokens = self.provider._last_usage.get("total_tokens")
            else:
                # Fallback to estimation if provider doesn't expose usage
                full_prompt = (system_prompt or "") + "\n\n" + prompt
                prompt_tokens = self.provider.get_token_count(full_prompt)
                completion_tokens = self.provider.get_token_count(result) if result else 0
                total_tokens = prompt_tokens + completion_tokens
            
        except Exception as e:
            status = "error"
            error_message = str(e)
            logger.error("AI completion failed", error=str(e), provider=self.provider_name)
            raise
        finally:
            # Calculate latency
            latency_ms = int((time.time() - start_time) * 1000)
            
            # Calculate cost
            model_name = getattr(self.provider, 'model', None) or getattr(self.provider, 'model_name', None)
            estimated_cost = float(CostCalculator.calculate_cost(
                provider_name=self.provider_name,
                model_name=model_name,
                prompt_tokens=prompt_tokens or total_tokens,
                completion_tokens=completion_tokens,
                total_tokens=total_tokens
            ))
            
            # Log usage (fire and forget - don't block on logging)
            try:
                await AIUsageLogger.log_usage(
                    provider_name=self.provider_name,
                    feature_name=feature_name,
                    recruiter_id=recruiter_id,
                    interview_id=interview_id,
                    job_description_id=job_description_id,
                    candidate_id=candidate_id,
                    model_name=model_name,
                    prompt_tokens=prompt_tokens,
                    completion_tokens=completion_tokens,
                    total_tokens=total_tokens,
                    estimated_cost_usd=estimated_cost,
                    latency_ms=latency_ms,
                    status=status,
                    error_message=error_message,
                    prompt_version=prompt_version,
                    metadata=metadata,
                )
            except Exception as log_error:
                # Don't fail the main operation if logging fails
                logger.warning("Failed to log AI usage", error=str(log_error))
        
        return result
    
    async def generate_streaming(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: float = 0.7,
        # Logging context
        recruiter_id: Optional[UUID] = None,
        interview_id: Optional[UUID] = None,
        job_description_id: Optional[UUID] = None,
        candidate_id: Optional[UUID] = None,
        feature_name: str = "ai_streaming",
        prompt_version: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """
        Generate streaming completion with proper usage logging
        
        Collects the full streamed response to accurately calculate tokens and costs,
        then logs usage after the stream completes.
        """
        start_time = time.time()
        status = "success"
        error_message = None
        full_response = ""
        prompt_tokens = None
        completion_tokens = None
        total_tokens = None
        
        # Estimate cost before making the call to check limits
        if recruiter_id:
            try:
                # Estimate tokens for cost checking
                full_prompt = (system_prompt or "") + "\n\n" + prompt
                estimated_prompt_tokens = self.provider.get_token_count(full_prompt)
                estimated_completion_tokens = int(estimated_prompt_tokens * 0.25) if max_tokens else 300
                estimated_total_tokens = estimated_prompt_tokens + estimated_completion_tokens
                
                # Calculate estimated cost
                model_name = getattr(self.provider, 'model', None) or getattr(self.provider, 'model_name', None)
                estimated_cost = CostCalculator.calculate_cost(
                    provider_name=self.provider_name,
                    model_name=model_name,
                    prompt_tokens=estimated_prompt_tokens,
                    completion_tokens=estimated_completion_tokens,
                    total_tokens=estimated_total_tokens
                )
                
                # Check cost limits before making the API call
                try:
                    await UsageLimitChecker.check_all_limits(
                        recruiter_id=recruiter_id,
                        check_interview_limit=False,
                        check_cost_limit=True,
                        estimated_cost=estimated_cost
                    )
                except Exception as limit_error:
                    if hasattr(limit_error, 'limit_type'):
                        from fastapi import HTTPException, status
                        raise HTTPException(
                            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                            detail=str(limit_error)
                        )
                    raise
            except Exception as e:
                logger.warning("Failed to check limits for streaming request", error=str(e))
                # Continue anyway - limit checking failure shouldn't block streaming
        
        try:
            # Stream response and collect chunks
            async for chunk in self.provider.generate_streaming(
                prompt=prompt,
                system_prompt=system_prompt,
                max_tokens=max_tokens,
                temperature=temperature
            ):
                # Accumulate the full response for accurate token counting
                full_response += chunk
                yield chunk
            
            # After stream completes, calculate actual usage
            # Try to get usage from provider if available (OpenAI provides this in streaming responses)
            if hasattr(self.provider, '_last_usage') and self.provider._last_usage:
                prompt_tokens = self.provider._last_usage.get("prompt_tokens")
                completion_tokens = self.provider._last_usage.get("completion_tokens")
                total_tokens = self.provider._last_usage.get("total_tokens")
            else:
                # Fallback to estimation using collected response
                full_prompt = (system_prompt or "") + "\n\n" + prompt
                prompt_tokens = self.provider.get_token_count(full_prompt)
                completion_tokens = self.provider.get_token_count(full_response)
                total_tokens = prompt_tokens + completion_tokens
            
        except Exception as e:
            status = "error"
            error_message = str(e)
            logger.error("AI streaming failed", error=str(e), provider=self.provider_name)
            raise
        finally:
            # Calculate latency
            latency_ms = int((time.time() - start_time) * 1000)
            
            # Calculate cost
            model_name = getattr(self.provider, 'model', None) or getattr(self.provider, 'model_name', None)
            estimated_cost = float(CostCalculator.calculate_cost(
                provider_name=self.provider_name,
                model_name=model_name,
                prompt_tokens=prompt_tokens or total_tokens if total_tokens else 0,
                completion_tokens=completion_tokens,
                total_tokens=total_tokens or 0
            ))
            
            # Log usage after stream completes (fire and forget)
            try:
                await AIUsageLogger.log_usage(
                    provider_name=self.provider_name,
                    feature_name=feature_name,
                    recruiter_id=recruiter_id,
                    interview_id=interview_id,
                    job_description_id=job_description_id,
                    candidate_id=candidate_id,
                    model_name=model_name,
                    prompt_tokens=prompt_tokens,
                    completion_tokens=completion_tokens,
                    total_tokens=total_tokens,
                    estimated_cost_usd=estimated_cost,
                    latency_ms=latency_ms,
                    status=status,
                    error_message=error_message,
                    prompt_version=prompt_version,
                    metadata=metadata,
                )
            except Exception as log_error:
                # Don't fail the main operation if logging fails
                logger.warning("Failed to log streaming AI usage", error=str(log_error))
    
    def get_token_count(self, text: str) -> int:
        """Pass through to provider"""
        return self.provider.get_token_count(text)

