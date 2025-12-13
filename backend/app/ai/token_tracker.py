"""
Token Tracker
Tracks token usage for interviews to enforce limits
"""

from typing import Dict, Optional, Any
from app.config import settings
from app.ai.providers import AIProviderFactory
import structlog

logger = structlog.get_logger()


class TokenTracker:
    """Tracks token usage per interview"""
    
    def __init__(self):
        """Initialize token tracker"""
        self.provider = AIProviderFactory.create_provider()
        self.max_tokens = settings.max_tokens_per_interview
    
    def estimate_tokens(self, text: str) -> int:
        """
        Estimate token count for text
        
        Args:
            text: Text to estimate
        
        Returns:
            Estimated token count
        """
        return self.provider.get_token_count(text)
    
    def track_usage(
        self,
        interview_id: str,
        tokens_used: int,
        operation: str = "question_generation"
    ) -> Dict[str, Any]:
        """
        Track token usage for an interview
        
        Args:
            interview_id: Interview ID
            tokens_used: Number of tokens used
            operation: Type of operation (question_generation, response_analysis, etc.)
        
        Returns:
            Dictionary with usage info and warnings
        """
        # In a real implementation, this would store in database
        # For now, we'll just log and return warnings
        
        logger.info(
            "Token usage tracked",
            interview_id=interview_id,
            tokens_used=tokens_used,
            operation=operation,
            max_tokens=self.max_tokens
        )
        
        # Calculate percentage
        percentage = (tokens_used / self.max_tokens) * 100 if self.max_tokens > 0 else 0
        
        warning = None
        if percentage >= 90:
            warning = "Token usage is at 90% or above. Interview may need to end soon."
        elif percentage >= 75:
            warning = "Token usage is at 75% or above. Consider wrapping up soon."
        
        return {
            "tokens_used": tokens_used,
            "max_tokens": self.max_tokens,
            "percentage_used": percentage,
            "tokens_remaining": max(0, self.max_tokens - tokens_used),
            "warning": warning
        }
    
    def check_limit(self, current_usage: int, additional_tokens: int) -> bool:
        """
        Check if adding tokens would exceed limit
        
        Args:
            current_usage: Current token usage
            additional_tokens: Tokens to add
        
        Returns:
            True if within limit, False if would exceed
        """
        return (current_usage + additional_tokens) <= self.max_tokens
    
    def get_remaining_tokens(self, current_usage: int) -> int:
        """
        Get remaining tokens
        
        Args:
            current_usage: Current token usage
        
        Returns:
            Remaining tokens
        """
        return max(0, self.max_tokens - current_usage)

