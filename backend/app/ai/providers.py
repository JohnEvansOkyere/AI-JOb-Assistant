"""
AI Model Providers
Multi-provider support for AI models (OpenAI, Groq, Gemini)
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from app.config import settings
import structlog

logger = structlog.get_logger()


class AIProvider(ABC):
    """Abstract base class for AI providers"""
    
    @abstractmethod
    async def generate_completion(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: float = 0.7
    ) -> str:
        """Generate text completion"""
        pass
    
    @abstractmethod
    async def generate_streaming(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: float = 0.7
    ):
        """Generate streaming response"""
        pass
    
    @abstractmethod
    def get_token_count(self, text: str) -> int:
        """Estimate token count for text"""
        pass


class OpenAIProvider(AIProvider):
    """OpenAI GPT provider"""
    
    def __init__(self):
        if not settings.openai_api_key:
            raise ValueError("OpenAI API key not configured")
        try:
            from openai import OpenAI
            self.client = OpenAI(api_key=settings.openai_api_key)
            self.model = settings.openai_model
        except ImportError:
            raise ImportError("OpenAI package not installed. Run: pip install openai")
    
    async def generate_completion(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: float = 0.7
    ) -> str:
        """Generate completion using OpenAI"""
        try:
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature
            )
            
            return response.choices[0].message.content
        except Exception as e:
            logger.error("OpenAI API error", error=str(e))
            raise
    
    async def generate_streaming(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: float = 0.7
    ):
        """Generate streaming response"""
        try:
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            stream = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
                stream=True
            )
            
            for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        except Exception as e:
            logger.error("OpenAI streaming error", error=str(e))
            raise
    
    def get_token_count(self, text: str) -> int:
        """Estimate token count (rough: ~4 chars per token)"""
        return len(text) // 4


class GroqProvider(AIProvider):
    """Groq provider"""
    
    def __init__(self):
        if not settings.groq_api_key:
            raise ValueError("Groq API key not configured")
        try:
            from groq import Groq
            self.client = Groq(api_key=settings.groq_api_key)
            self.model = settings.groq_model
        except ImportError:
            raise ImportError("Groq package not installed. Run: pip install groq")
    
    async def generate_completion(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: float = 0.7
    ) -> str:
        """Generate completion using Groq"""
        try:
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature
            )
            
            return response.choices[0].message.content
        except Exception as e:
            logger.error("Groq API error", error=str(e))
            raise
    
    async def generate_streaming(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: float = 0.7
    ):
        """Generate streaming response"""
        try:
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            stream = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
                stream=True
            )
            
            for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        except Exception as e:
            logger.error("Groq streaming error", error=str(e))
            raise
    
    def get_token_count(self, text: str) -> int:
        """Estimate token count"""
        return len(text) // 4


class GeminiProvider(AIProvider):
    """Google Gemini provider"""
    
    def __init__(self):
        if not settings.gemini_api_key:
            raise ValueError("Gemini API key not configured")
        try:
            import google.generativeai as genai
            genai.configure(api_key=settings.gemini_api_key)
            self.model = genai.GenerativeModel(settings.gemini_model)
        except ImportError:
            raise ImportError("Google Generative AI package not installed. Run: pip install google-generativeai")
    
    async def generate_completion(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: float = 0.7
    ) -> str:
        """Generate completion using Gemini"""
        try:
            full_prompt = prompt
            if system_prompt:
                full_prompt = f"{system_prompt}\n\n{prompt}"
            
            response = self.model.generate_content(
                full_prompt,
                generation_config={
                    "max_output_tokens": max_tokens,
                    "temperature": temperature
                }
            )
            
            return response.text
        except Exception as e:
            logger.error("Gemini API error", error=str(e))
            raise
    
    async def generate_streaming(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: float = 0.7
    ):
        """Generate streaming response"""
        try:
            full_prompt = prompt
            if system_prompt:
                full_prompt = f"{system_prompt}\n\n{prompt}"
            
            response = self.model.generate_content(
                full_prompt,
                generation_config={
                    "max_output_tokens": max_tokens,
                    "temperature": temperature
                },
                stream=True
            )
            
            for chunk in response:
                if chunk.text:
                    yield chunk.text
        except Exception as e:
            logger.error("Gemini streaming error", error=str(e))
            raise
    
    def get_token_count(self, text: str) -> int:
        """Estimate token count"""
        return len(text) // 4


class AIProviderFactory:
    """Factory for creating AI providers"""
    
    @staticmethod
    def create_provider(provider_name: Optional[str] = None) -> AIProvider:
        """
        Create an AI provider instance
        
        Args:
            provider_name: Name of provider (openai, groq, gemini). 
                         If None, uses primary_ai_provider from settings
        
        Returns:
            AIProvider instance
        
        Raises:
            ValueError: If provider is not configured or invalid
        """
        provider_name = provider_name or settings.primary_ai_provider
        
        if provider_name == "openai":
            return OpenAIProvider()
        elif provider_name == "groq":
            return GroqProvider()
        elif provider_name == "gemini":
            return GeminiProvider()
        else:
            raise ValueError(f"Unknown AI provider: {provider_name}")
    
    @staticmethod
    def get_available_providers() -> List[str]:
        """Get list of available providers based on configured API keys"""
        available = []
        
        if settings.openai_api_key:
            available.append("openai")
        if settings.groq_api_key:
            available.append("groq")
        if settings.gemini_api_key:
            available.append("gemini")
        
        return available

