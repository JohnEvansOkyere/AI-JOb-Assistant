"""
Cost Calculator Service
Calculates estimated costs for AI service usage
"""

from typing import Optional
from app.config import settings
from decimal import Decimal, ROUND_HALF_UP


class CostCalculator:
    """Service for calculating AI service costs"""
    
    # OpenAI pricing (as of 2024, in USD per 1K tokens)
    # Pricing varies by model - these are approximate
    OPENAI_PRICING = {
        "gpt-4o": {"prompt": 0.005, "completion": 0.015},  # $5/$15 per 1M tokens
        "gpt-4o-mini": {"prompt": 0.00015, "completion": 0.0006},  # $0.15/$0.60 per 1M tokens
        "gpt-4": {"prompt": 0.03, "completion": 0.06},  # $30/$60 per 1M tokens
        "gpt-3.5-turbo": {"prompt": 0.0005, "completion": 0.0015},  # $0.50/$1.50 per 1M tokens
        "default": {"prompt": 0.001, "completion": 0.002},  # Conservative default
    }
    
    # ElevenLabs pricing (as of 2024, in USD per character)
    # Pricing varies by plan - using standard plan pricing
    ELEVENLABS_CHARACTER_COST = 0.000018  # $0.018 per 1000 characters (~$18 per 1M characters)
    
    # Whisper pricing (OpenAI, in USD per minute)
    WHISPER_COST_PER_MINUTE = 0.006  # $0.006 per minute (~$0.36 per hour)
    
    # Deepgram pricing (in USD per minute)
    DEEPGRAM_COST_PER_MINUTE = 0.0044  # ~$0.0044 per minute (as of 2024)
    
    # Groq and Gemini are typically free or very low cost for most use cases
    # Setting minimal costs for tracking purposes
    GROQ_COST_PER_1K_TOKENS = 0.0001  # Very low cost estimate
    GEMINI_COST_PER_1K_TOKENS = 0.0005  # Low cost estimate
    
    @staticmethod
    def calculate_openai_cost(
        model_name: str,
        prompt_tokens: int,
        completion_tokens: int
    ) -> Decimal:
        """
        Calculate OpenAI API cost
        
        Args:
            model_name: Model name
            prompt_tokens: Number of prompt tokens
            completion_tokens: Number of completion tokens
            
        Returns:
            Estimated cost in USD
        """
        # Get pricing for model or use default
        pricing = CostCalculator.OPENAI_PRICING.get(
            model_name.lower(),
            CostCalculator.OPENAI_PRICING["default"]
        )
        
        # Calculate cost: (tokens / 1000) * price_per_1k
        prompt_cost = Decimal(prompt_tokens) / 1000 * Decimal(str(pricing["prompt"]))
        completion_cost = Decimal(completion_tokens) / 1000 * Decimal(str(pricing["completion"]))
        
        total_cost = prompt_cost + completion_cost
        
        # Round to 6 decimal places
        return total_cost.quantize(Decimal('0.000001'), rounding=ROUND_HALF_UP)
    
    @staticmethod
    def calculate_elevenlabs_cost(characters: int) -> Decimal:
        """
        Calculate ElevenLabs TTS cost
        
        Args:
            characters: Number of characters in text
            
        Returns:
            Estimated cost in USD
        """
        cost = Decimal(characters) * Decimal(str(CostCalculator.ELEVENLABS_CHARACTER_COST))
        return cost.quantize(Decimal('0.000001'), rounding=ROUND_HALF_UP)
    
    @staticmethod
    def calculate_whisper_cost(audio_duration_seconds: float) -> Decimal:
        """
        Calculate OpenAI Whisper STT cost
        
        Args:
            audio_duration_seconds: Audio duration in seconds
            
        Returns:
            Estimated cost in USD
        """
        minutes = Decimal(str(audio_duration_seconds)) / 60
        cost = minutes * Decimal(str(CostCalculator.WHISPER_COST_PER_MINUTE))
        return cost.quantize(Decimal('0.000001'), rounding=ROUND_HALF_UP)
    
    @staticmethod
    def calculate_deepgram_cost(audio_duration_seconds: float) -> Decimal:
        """
        Calculate Deepgram STT cost
        
        Args:
            audio_duration_seconds: Audio duration in seconds
            
        Returns:
            Estimated cost in USD
        """
        minutes = Decimal(str(audio_duration_seconds)) / 60
        cost = minutes * Decimal(str(CostCalculator.DEEPGRAM_COST_PER_MINUTE))
        return cost.quantize(Decimal('0.000001'), rounding=ROUND_HALF_UP)
    
    @staticmethod
    def calculate_groq_cost(total_tokens: int) -> Decimal:
        """
        Calculate Groq API cost (typically very low/free)
        
        Args:
            total_tokens: Total tokens used
            
        Returns:
            Estimated cost in USD
        """
        cost = Decimal(total_tokens) / 1000 * Decimal(str(CostCalculator.GROQ_COST_PER_1K_TOKENS))
        return cost.quantize(Decimal('0.000001'), rounding=ROUND_HALF_UP)
    
    @staticmethod
    def calculate_gemini_cost(total_tokens: int) -> Decimal:
        """
        Calculate Gemini API cost
        
        Args:
            total_tokens: Total tokens used
            
        Returns:
            Estimated cost in USD
        """
        cost = Decimal(total_tokens) / 1000 * Decimal(str(CostCalculator.GEMINI_COST_PER_1K_TOKENS))
        return cost.quantize(Decimal('0.000001'), rounding=ROUND_HALF_UP)
    
    @staticmethod
    def calculate_cost(
        provider_name: str,
        model_name: Optional[str] = None,
        prompt_tokens: Optional[int] = None,
        completion_tokens: Optional[int] = None,
        total_tokens: Optional[int] = None,
        characters: Optional[int] = None,
        audio_duration_seconds: Optional[float] = None,
    ) -> Decimal:
        """
        Calculate cost for any AI provider
        
        Args:
            provider_name: Provider name (openai, groq, gemini, elevenlabs, whisper, deepgram)
            model_name: Model name (for OpenAI/Groq/Gemini)
            prompt_tokens: Prompt tokens (for LLM providers)
            completion_tokens: Completion tokens (for LLM providers)
            total_tokens: Total tokens (if prompt/completion not available)
            characters: Characters used (for ElevenLabs TTS)
            audio_duration_seconds: Audio duration (for STT providers)
            
        Returns:
            Estimated cost in USD
        """
        provider_lower = provider_name.lower()
        
        if provider_lower == "openai":
            if not model_name:
                model_name = settings.openai_model
            if prompt_tokens and completion_tokens:
                return CostCalculator.calculate_openai_cost(model_name, prompt_tokens, completion_tokens)
            elif total_tokens:
                # Estimate 50/50 split if only total tokens available
                return CostCalculator.calculate_openai_cost(
                    model_name,
                    total_tokens // 2,
                    total_tokens // 2
                )
            else:
                return Decimal('0')
        
        elif provider_lower == "elevenlabs":
            if characters:
                return CostCalculator.calculate_elevenlabs_cost(characters)
            return Decimal('0')
        
        elif provider_lower == "whisper":
            if audio_duration_seconds:
                return CostCalculator.calculate_whisper_cost(audio_duration_seconds)
            return Decimal('0')
        
        elif provider_lower == "deepgram":
            if audio_duration_seconds:
                return CostCalculator.calculate_deepgram_cost(audio_duration_seconds)
            return Decimal('0')
        
        elif provider_lower == "groq":
            if total_tokens:
                return CostCalculator.calculate_groq_cost(total_tokens)
            return Decimal('0')
        
        elif provider_lower == "gemini":
            if total_tokens:
                return CostCalculator.calculate_gemini_cost(total_tokens)
            return Decimal('0')
        
        else:
            # Unknown provider - return 0 cost
            return Decimal('0')

