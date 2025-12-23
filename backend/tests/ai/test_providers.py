"""
Tests for AI provider classes and factory
"""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from app.ai.providers import (
    AIProvider,
    OpenAIProvider,
    GroqProvider,
    GeminiProvider,
    GrokProvider,
    AIProviderFactory
)
from app.config import settings


@pytest.mark.unit
@pytest.mark.ai
class TestAIProviderFactory:
    """Tests for AIProviderFactory"""
    
    def test_get_available_providers_with_all_keys(self):
        """Test that all providers are detected when all API keys are set"""
        with patch.object(settings, 'openai_api_key', 'test-key'):
            with patch.object(settings, 'grok_api_key', 'test-key'):
                with patch.object(settings, 'groq_api_key', 'test-key'):
                    with patch.object(settings, 'gemini_api_key', 'test-key'):
                        providers = AIProviderFactory.get_available_providers()
                        assert "openai" in providers
                        assert "grok" in providers
                        assert "groq" in providers
                        assert "gemini" in providers
    
    def test_get_available_providers_with_some_keys(self):
        """Test that only configured providers are detected"""
        with patch.object(settings, 'openai_api_key', 'test-key'):
            with patch.object(settings, 'grok_api_key', None):
                with patch.object(settings, 'groq_api_key', None):
                    with patch.object(settings, 'gemini_api_key', None):
                        providers = AIProviderFactory.get_available_providers()
                        assert "openai" in providers
                        assert "grok" not in providers
                        assert "groq" not in providers
                        assert "gemini" not in providers
    
    def test_get_available_providers_no_keys(self):
        """Test that empty list is returned when no keys are set"""
        with patch.object(settings, 'openai_api_key', None):
            with patch.object(settings, 'grok_api_key', None):
                with patch.object(settings, 'groq_api_key', None):
                    with patch.object(settings, 'gemini_api_key', None):
                        providers = AIProviderFactory.get_available_providers()
                        assert providers == []
    
    @patch('app.ai.providers.OpenAIProvider')
    def test_create_provider_with_openai(self, mock_openai_provider):
        """Test creating OpenAI provider"""
        mock_instance = MagicMock()
        mock_openai_provider.return_value = mock_instance
        
        with patch.object(settings, 'openai_api_key', 'test-key'):
            with patch.object(settings, 'primary_ai_provider', 'openai'):
                provider = AIProviderFactory.create_provider("openai")
                assert provider == mock_instance
    
    def test_create_provider_raises_when_none_available(self):
        """Test that ValueError is raised when no providers are available"""
        with patch.object(AIProviderFactory, 'get_available_providers', return_value=[]):
            with pytest.raises(ValueError) as exc_info:
                AIProviderFactory.create_provider()
            assert "No AI providers are configured" in str(exc_info.value)
    
    @patch('app.ai.providers.OpenAIProvider')
    def test_create_provider_falls_back_on_failure(self, mock_openai_provider):
        """Test that factory falls back to next provider when first fails"""
        # First provider fails
        mock_openai_provider.side_effect = ValueError("API key invalid")
        
        # Mock Groq provider as fallback
        mock_groq_instance = MagicMock()
        with patch('app.ai.providers.GroqProvider', return_value=mock_groq_instance):
            with patch.object(AIProviderFactory, 'get_available_providers', return_value=["openai", "groq"]):
                with patch.object(settings, 'openai_api_key', 'test-key'):
                    with patch.object(settings, 'groq_api_key', 'test-key'):
                        with patch.object(settings, 'primary_ai_provider', 'openai'):
                            provider = AIProviderFactory.create_provider()
                            assert provider == mock_groq_instance
    
    def test_create_provider_uses_primary_when_none_specified(self):
        """Test that primary provider is used when none specified"""
        with patch.object(settings, 'primary_ai_provider', 'groq'):
            with patch.object(settings, 'groq_api_key', 'test-key'):
                with patch.object(AIProviderFactory, 'get_available_providers', return_value=["groq"]):
                    with patch('app.ai.providers.GroqProvider', return_value=MagicMock()) as mock_groq:
                        provider = AIProviderFactory.create_provider()
                        mock_groq.assert_called_once()


@pytest.mark.unit
@pytest.mark.ai
class TestOpenAIProvider:
    """Tests for OpenAIProvider"""
    
    def test_init_raises_without_api_key(self):
        """Test that initialization raises ValueError without API key"""
        with patch.object(settings, 'openai_api_key', None):
            with pytest.raises(ValueError) as exc_info:
                OpenAIProvider()
            assert "OpenAI API key not configured" in str(exc_info.value)
    
    @patch('app.ai.providers.OpenAI')
    def test_init_success_with_api_key(self, mock_openai):
        """Test successful initialization with API key"""
        mock_client = MagicMock()
        mock_openai.return_value = mock_client
        
        with patch.object(settings, 'openai_api_key', 'test-key'):
            with patch.object(settings, 'openai_model', 'gpt-4'):
                provider = OpenAIProvider()
                assert provider.model == 'gpt-4'
                assert provider.client == mock_client
    
    @pytest.mark.asyncio
    @patch('app.ai.providers.OpenAI')
    async def test_generate_completion(self, mock_openai):
        """Test generate_completion method"""
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Test response"
        
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client
        
        with patch.object(settings, 'openai_api_key', 'test-key'):
            provider = OpenAIProvider()
            result = await provider.generate_completion("Test prompt")
            assert result == "Test response"
            mock_client.chat.completions.create.assert_called_once()
    
    @pytest.mark.asyncio
    @patch('app.ai.providers.OpenAI')
    async def test_generate_completion_with_system_prompt(self, mock_openai):
        """Test generate_completion with system prompt"""
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Test response"
        
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client
        
        with patch.object(settings, 'openai_api_key', 'test-key'):
            provider = OpenAIProvider()
            result = await provider.generate_completion(
                "Test prompt",
                system_prompt="You are a helpful assistant"
            )
            assert result == "Test response"
            call_args = mock_client.chat.completions.create.call_args
            messages = call_args.kwargs['messages']
            assert len(messages) == 2
            assert messages[0]['role'] == 'system'
            assert messages[1]['role'] == 'user'
    
    @pytest.mark.asyncio
    @patch('app.ai.providers.OpenAI')
    async def test_generate_streaming(self, mock_openai):
        """Test generate_streaming method"""
        mock_chunk1 = MagicMock()
        mock_chunk1.choices = [MagicMock()]
        mock_chunk1.choices[0].delta.content = "Chunk1 "
        
        mock_chunk2 = MagicMock()
        mock_chunk2.choices = [MagicMock()]
        mock_chunk2.choices[0].delta.content = "Chunk2"
        
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = [mock_chunk1, mock_chunk2]
        mock_openai.return_value = mock_client
        
        with patch.object(settings, 'openai_api_key', 'test-key'):
            provider = OpenAIProvider()
            chunks = []
            async for chunk in provider.generate_streaming("Test prompt"):
                chunks.append(chunk)
            assert chunks == ["Chunk1 ", "Chunk2"]
    
    def test_get_token_count(self):
        """Test get_token_count method"""
        with patch.object(settings, 'openai_api_key', 'test-key'):
            with patch('app.ai.providers.OpenAI', return_value=MagicMock()):
                provider = OpenAIProvider()
                # Rough estimate: ~4 chars per token
                assert provider.get_token_count("Hello World") == 2  # 11 chars / 4 = 2


@pytest.mark.unit
@pytest.mark.ai
class TestGroqProvider:
    """Tests for GroqProvider"""
    
    def test_init_raises_without_api_key(self):
        """Test that initialization raises ValueError without API key"""
        with patch.object(settings, 'groq_api_key', None):
            with pytest.raises(ValueError) as exc_info:
                GroqProvider()
            assert "Groq API key not configured" in str(exc_info.value)
    
    @patch('app.ai.providers.Groq')
    def test_init_success_with_api_key(self, mock_groq):
        """Test successful initialization with API key"""
        mock_client = MagicMock()
        mock_groq.return_value = mock_client
        
        with patch.object(settings, 'groq_api_key', 'test-key'):
            with patch.object(settings, 'groq_model', 'mixtral-8x7b'):
                provider = GroqProvider()
                assert provider.model == 'mixtral-8x7b'
                assert provider.client == mock_client
    
    @pytest.mark.asyncio
    @patch('app.ai.providers.Groq')
    async def test_generate_completion(self, mock_groq):
        """Test generate_completion method"""
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Groq response"
        
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_groq.return_value = mock_client
        
        with patch.object(settings, 'groq_api_key', 'test-key'):
            provider = GroqProvider()
            result = await provider.generate_completion("Test prompt")
            assert result == "Groq response"


@pytest.mark.unit
@pytest.mark.ai
class TestGeminiProvider:
    """Tests for GeminiProvider"""
    
    def test_init_raises_without_api_key(self):
        """Test that initialization raises ValueError without API key"""
        with patch.object(settings, 'gemini_api_key', None):
            with pytest.raises(ValueError) as exc_info:
                GeminiProvider()
            assert "Gemini API key not configured" in str(exc_info.value)
    
    @patch('app.ai.providers.genai')
    def test_init_success_with_api_key(self, mock_genai):
        """Test successful initialization with API key"""
        mock_model = MagicMock()
        mock_genai.GenerativeModel.return_value = mock_model
        
        with patch.object(settings, 'gemini_api_key', 'test-key'):
            with patch.object(settings, 'gemini_model', 'gemini-pro'):
                provider = GeminiProvider()
                assert provider.model == mock_model
                mock_genai.configure.assert_called_once_with(api_key='test-key')
    
    @pytest.mark.asyncio
    @patch('app.ai.providers.genai')
    async def test_generate_completion(self, mock_genai):
        """Test generate_completion method"""
        mock_response = MagicMock()
        mock_response.text = "Gemini response"
        
        mock_model = MagicMock()
        mock_model.generate_content.return_value = mock_response
        mock_genai.GenerativeModel.return_value = mock_model
        
        with patch.object(settings, 'gemini_api_key', 'test-key'):
            provider = GeminiProvider()
            result = await provider.generate_completion("Test prompt")
            assert result == "Gemini response"


@pytest.mark.unit
@pytest.mark.ai
class TestGrokProvider:
    """Tests for GrokProvider"""
    
    def test_init_raises_without_api_key(self):
        """Test that initialization raises ValueError without API key"""
        with patch.object(settings, 'grok_api_key', None):
            with pytest.raises(ValueError) as exc_info:
                GrokProvider()
            assert "Grok API key not configured" in str(exc_info.value)
    
    @patch('app.ai.providers.OpenAI')
    def test_init_success_with_api_key(self, mock_openai):
        """Test successful initialization with API key"""
        mock_client = MagicMock()
        mock_openai.return_value = mock_client
        
        with patch.object(settings, 'grok_api_key', 'test-key'):
            with patch.object(settings, 'grok_model', 'grok-4-latest'):
                provider = GrokProvider()
                assert provider.model == 'grok-4-latest'
                assert provider.client == mock_client
                # Verify OpenAI client was called with Grok's base URL
                mock_openai.assert_called_once()
                call_kwargs = mock_openai.call_args.kwargs
                assert call_kwargs['base_url'] == "https://api.x.ai/v1"
                assert call_kwargs['api_key'] == 'test-key'
    
    @pytest.mark.asyncio
    @patch('app.ai.providers.OpenAI')
    async def test_generate_completion(self, mock_openai):
        """Test generate_completion method"""
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Grok response"
        
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client
        
        with patch.object(settings, 'grok_api_key', 'test-key'):
            provider = GrokProvider()
            result = await provider.generate_completion("Test prompt")
            assert result == "Grok response"

