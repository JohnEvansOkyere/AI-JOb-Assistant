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
        self._last_usage = None  # Store last API usage info
        try:
            from openai import OpenAI
            import httpx
            import os
            
            # Create a custom httpx client that explicitly doesn't use proxies
            # This prevents httpx from reading proxy environment variables and passing them to OpenAI
            # We need to create the httpx client in a way that doesn't read proxy env vars
            original_proxies = {}
            proxy_vars = ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy', 'ALL_PROXY', 'all_proxy']
            
            # Temporarily remove proxy environment variables
            for var in proxy_vars:
                if var in os.environ:
                    original_proxies[var] = os.environ.pop(var)
            
            try:
                # Create httpx client without reading proxy environment variables
                # trust_env=False prevents httpx from reading HTTP_PROXY, HTTPS_PROXY, etc.
                http_client = httpx.Client(
                    timeout=60.0,
                    follow_redirects=True,
                    trust_env=False  # Don't read proxy env vars
                )
                
                # Initialize OpenAI client with custom http_client
                # This bypasses httpx's automatic proxy detection from environment
                self.client = OpenAI(
                    api_key=settings.openai_api_key,
                    http_client=http_client
                )
                self.model = settings.openai_model
            finally:
                # Restore proxy environment variables
                for var, value in original_proxies.items():
                    os.environ[var] = value
        except ImportError:
            raise ImportError("OpenAI package not installed. Run: pip install openai")
        except TypeError as e:
            if "proxies" in str(e) or "unexpected keyword" in str(e).lower():
                logger.error("OpenAI client initialization error", error=str(e))
                # Fallback: try without custom http_client
                try:
                    logger.warning("Retrying OpenAI client without custom http_client")
                    self.client = OpenAI(api_key=settings.openai_api_key)
                    self.model = settings.openai_model
                except Exception as e2:
                    raise ValueError(f"Failed to initialize OpenAI client. This may be due to library version incompatibility. Error: {str(e2)}")
            else:
                raise
        except Exception as e:
            logger.error("Failed to initialize OpenAI client", error=str(e))
            raise ValueError(f"Failed to initialize OpenAI client: {str(e)}")
    
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
            
            # Store usage info for logging
            if hasattr(response, 'usage') and response.usage:
                self._last_usage = {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                }
            
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
            
            # Reset usage info
            self._last_usage = None
            
            for chunk in stream:
                # OpenAI provides usage info in the final chunk (when stream ends)
                if hasattr(chunk, 'usage') and chunk.usage:
                    self._last_usage = {
                        "prompt_tokens": chunk.usage.prompt_tokens,
                        "completion_tokens": chunk.usage.completion_tokens,
                        "total_tokens": chunk.usage.total_tokens
                    }
                
                # Yield content chunks
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
        self._last_usage = None  # Store last API usage info
        try:
            from groq import Groq
            import httpx
            import os
            
            # Temporarily remove proxy environment variables
            # Groq client reads these and tries to pass them as proxies parameter
            original_proxies = {}
            proxy_vars = ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy', 'ALL_PROXY', 'all_proxy']
            
            for var in proxy_vars:
                if var in os.environ:
                    original_proxies[var] = os.environ.pop(var)
            
            try:
                # Try with custom http_client first (if Groq supports it)
                # trust_env=False prevents httpx from reading proxy env vars
                try:
                    http_client = httpx.Client(
                        timeout=60.0,
                        follow_redirects=True,
                        trust_env=False  # Don't read proxy env vars
                    )
                    self.client = Groq(
                        api_key=settings.groq_api_key,
                        http_client=http_client
                    )
                except TypeError:
                    # If Groq doesn't accept http_client parameter, initialize without it
                    # The proxy env vars are already removed, so this should work
                    self.client = Groq(api_key=settings.groq_api_key)
                
                self.model = settings.groq_model
            finally:
                # Restore proxy environment variables
                for var, value in original_proxies.items():
                    os.environ[var] = value
        except ImportError:
            raise ImportError("Groq package not installed. Run: pip install groq")
        except TypeError as e:
            if "proxies" in str(e) or "unexpected keyword" in str(e).lower():
                logger.error("Groq client initialization error", error=str(e))
                raise ValueError(f"Failed to initialize Groq client. This may be due to library version incompatibility. Error: {str(e)}")
            else:
                raise
        except Exception as e:
            logger.error("Failed to initialize Groq client", error=str(e))
            raise ValueError(f"Failed to initialize Groq client: {str(e)}")
    
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
            
            # Store usage info for logging
            if hasattr(response, 'usage') and response.usage:
                self._last_usage = {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                }
            
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
            
            # Reset usage info
            self._last_usage = None
            
            for chunk in stream:
                # Groq provides usage info in the final chunk (when stream ends)
                if hasattr(chunk, 'usage') and chunk.usage:
                    self._last_usage = {
                        "prompt_tokens": chunk.usage.prompt_tokens if hasattr(chunk.usage, 'prompt_tokens') else None,
                        "completion_tokens": chunk.usage.completion_tokens if hasattr(chunk.usage, 'completion_tokens') else None,
                        "total_tokens": chunk.usage.total_tokens if hasattr(chunk.usage, 'total_tokens') else None
                    }
                
                # Yield content chunks
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
        self._last_usage = None  # Store last API usage info (Gemini doesn't expose usage directly)
        try:
            import google.generativeai as genai
            genai.configure(api_key=settings.gemini_api_key)
            # Try the configured model name, fallback to gemini-pro if it fails
            model_name = settings.gemini_model
            try:
                self.model = genai.GenerativeModel(model_name)
                # Test if model is accessible
                self.model_name = model_name
            except Exception:
                # Fallback to gemini-pro if the configured model doesn't work
                logger.warning(f"Model {model_name} not available, falling back to gemini-pro")
                self.model = genai.GenerativeModel("gemini-pro")
                self.model_name = "gemini-pro"
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
            # If model not found error, try to reinitialize with gemini-pro as fallback
            error_str = str(e)
            if "404" in error_str and "not found" in error_str.lower() and self.model_name != "gemini-pro":
                logger.warning(
                    f"Model {self.model_name} not available, falling back to gemini-pro",
                    original_error=error_str
                )
                try:
                    import google.generativeai as genai
                    fallback_model = genai.GenerativeModel("gemini-pro")
                    response = fallback_model.generate_content(
                        full_prompt,
                        generation_config={
                            "max_output_tokens": max_tokens,
                            "temperature": temperature
                        }
                    )
                    # Update the model for future use
                    self.model = fallback_model
                    self.model_name = "gemini-pro"
                    return response.text
                except Exception as fallback_error:
                    logger.error("Gemini fallback model also failed", error=str(fallback_error))
                    raise
            logger.error("Gemini API error", error=error_str)
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
            
            # Reset usage info
            self._last_usage = None
            
            for chunk in response:
                # Gemini may provide usage info in some chunks
                # Check for usage_metadata (structure may vary by Gemini version)
                if hasattr(chunk, 'usage_metadata') and chunk.usage_metadata:
                    self._last_usage = {
                        "prompt_tokens": chunk.usage_metadata.prompt_token_count if hasattr(chunk.usage_metadata, 'prompt_token_count') else None,
                        "completion_tokens": chunk.usage_metadata.candidates_token_count if hasattr(chunk.usage_metadata, 'candidates_token_count') else None,
                        "total_tokens": None
                    }
                    if self._last_usage["prompt_tokens"] and self._last_usage["completion_tokens"]:
                        self._last_usage["total_tokens"] = self._last_usage["prompt_tokens"] + self._last_usage["completion_tokens"]
                
                # Yield text chunks
                if chunk.text:
                    yield chunk.text
        except Exception as e:
            logger.error("Gemini streaming error", error=str(e))
            raise
    
    def get_token_count(self, text: str) -> int:
        """Estimate token count"""
        return len(text) // 4


class GrokProvider(AIProvider):
    """Grok (x.ai) provider - OpenAI compatible API"""
    
    def __init__(self):
        if not settings.grok_api_key:
            raise ValueError("Grok API key not configured")
        self._last_usage = None  # Store last API usage info
        try:
            from openai import OpenAI
            import httpx
            import os
            
            # Create a custom httpx client that explicitly doesn't use proxies
            original_proxies = {}
            proxy_vars = ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy', 'ALL_PROXY', 'all_proxy']
            
            # Temporarily remove proxy environment variables
            for var in proxy_vars:
                if var in os.environ:
                    original_proxies[var] = os.environ.pop(var)
            
            try:
                # Create httpx client without reading proxy environment variables
                http_client = httpx.Client(
                    timeout=60.0,
                    follow_redirects=True,
                    trust_env=False  # Don't read proxy env vars
                )
                
                # Initialize OpenAI client with Grok's API endpoint
                # Grok uses OpenAI-compatible API at api.x.ai
                self.client = OpenAI(
                    api_key=settings.grok_api_key,
                    base_url="https://api.x.ai/v1",
                    http_client=http_client
                )
                self.model = settings.grok_model
            finally:
                # Restore proxy environment variables
                for var, value in original_proxies.items():
                    os.environ[var] = value
        except ImportError:
            raise ImportError("OpenAI package not installed. Run: pip install openai")
        except Exception as e:
            logger.error("Failed to initialize Grok client", error=str(e))
            raise ValueError(f"Failed to initialize Grok client: {str(e)}")
    
    async def generate_completion(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: float = 0.7
    ) -> str:
        """Generate completion using Grok"""
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
            
            # Store usage info for logging
            if hasattr(response, 'usage') and response.usage:
                self._last_usage = {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                }
            
            return response.choices[0].message.content
        except Exception as e:
            logger.error("Grok API error", error=str(e))
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
            
            # Reset usage info
            self._last_usage = None
            
            for chunk in stream:
                # Grok (x.ai) provides usage info in the final chunk (similar to OpenAI)
                if hasattr(chunk, 'usage') and chunk.usage:
                    self._last_usage = {
                        "prompt_tokens": chunk.usage.prompt_tokens if hasattr(chunk.usage, 'prompt_tokens') else None,
                        "completion_tokens": chunk.usage.completion_tokens if hasattr(chunk.usage, 'completion_tokens') else None,
                        "total_tokens": chunk.usage.total_tokens if hasattr(chunk.usage, 'total_tokens') else None
                    }
                
                # Yield content chunks
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        except Exception as e:
            logger.error("Grok streaming error", error=str(e))
            raise
    
    def get_token_count(self, text: str) -> int:
        """Estimate token count (rough: ~4 chars per token)"""
        return len(text) // 4


class AIProviderFactory:
    """Factory for creating AI providers"""
    
    @staticmethod
    def create_provider(provider_name: Optional[str] = None) -> AIProvider:
        """
        Create an AI provider instance
        
        Args:
            provider_name: Name of provider (openai, grok, groq, gemini). 
                         If None, uses primary_ai_provider from settings.
                         If the requested provider is not available, falls back to first available provider.
        
        Returns:
            AIProvider instance
        
        Raises:
            ValueError: If no providers are configured or invalid provider name
        """
        available_providers = AIProviderFactory.get_available_providers()
        
        if not available_providers:
            raise ValueError("No AI providers are configured. Please set at least one API key (OPENAI_API_KEY, GROK_API_KEY, GROQ_API_KEY, or GEMINI_API_KEY).")
        
        # Use requested provider or primary provider from settings
        requested_provider = provider_name or settings.primary_ai_provider
        
        # Build list of providers to try: requested first, then available ones
        providers_to_try = []
        if requested_provider in available_providers:
            providers_to_try.append(requested_provider)
        # Add other available providers as fallbacks
        for provider in available_providers:
            if provider != requested_provider:
                providers_to_try.append(provider)
        
        # Try each provider until one successfully instantiates
        last_error = None
        for provider_name in providers_to_try:
            try:
                if provider_name == "openai":
                    return OpenAIProvider()
                elif provider_name == "grok":
                    return GrokProvider()
                elif provider_name == "groq":
                    return GroqProvider()
                elif provider_name == "gemini":
                    return GeminiProvider()
                else:
                    raise ValueError(f"Unknown AI provider: {provider_name}")
            except (ValueError, ImportError) as e:
                # Provider failed to instantiate (missing package, missing API key, etc.)
                last_error = e
                if provider_name != providers_to_try[-1]:  # Not the last provider to try
                    logger.warning(
                        "Provider failed to initialize, trying next available",
                        provider=provider_name,
                        error=str(e),
                        next_providers=providers_to_try[providers_to_try.index(provider_name) + 1:]
                    )
                continue
        
        # All providers failed
        error_msg = f"Failed to initialize any AI provider. Last error: {str(last_error)}"
        logger.error(
            "All AI providers failed to initialize",
            available_providers=available_providers,
            last_error=str(last_error)
        )
        raise ValueError(error_msg)
    
    @staticmethod
    def get_available_providers() -> List[str]:
        """Get list of available providers based on configured API keys"""
        available = []
        
        if settings.openai_api_key:
            available.append("openai")
        if settings.grok_api_key:
            available.append("grok")
        if settings.groq_api_key:
            available.append("groq")
        if settings.gemini_api_key:
            available.append("gemini")
        
        return available

