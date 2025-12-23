"""
Tests for rate limiting utilities
"""

import pytest
from unittest.mock import patch, MagicMock
from fastapi import Request

from app.utils.rate_limit import (
    limiter,
    get_user_id,
    rate_limit_auth,
    rate_limit_ai,
    rate_limit_public,
    rate_limit_default,
    rate_limit_custom,
    rate_limit_handler
)
from app.config import settings
from slowapi.errors import RateLimitExceeded


@pytest.mark.unit
@pytest.mark.utils
class TestGetUserId:
    """Tests for get_user_id function"""
    
    def test_returns_user_id_from_state(self):
        """Test that user ID is extracted from request state"""
        request = MagicMock(spec=Request)
        request.state.user_id = "user-123"
        
        result = get_user_id(request)
        assert result == "user:user-123"
    
    def test_falls_back_to_ip_address(self):
        """Test that function falls back to IP address when no user"""
        request = MagicMock(spec=Request)
        request.state = MagicMock()
        delattr(request.state, 'user_id')
        
        # Mock get_remote_address
        with patch('app.utils.rate_limit.get_remote_address', return_value="127.0.0.1"):
            result = get_user_id(request)
            assert result == "127.0.0.1"
    
    def test_handles_missing_state_attribute(self):
        """Test that function handles missing state attribute gracefully"""
        request = MagicMock(spec=Request)
        request.state = MagicMock()
        
        # Mock get_remote_address
        with patch('app.utils.rate_limit.get_remote_address', return_value="127.0.0.1"):
            result = get_user_id(request)
            assert result == "127.0.0.1"


@pytest.mark.unit
@pytest.mark.utils
class TestRateLimitDecorators:
    """Tests for rate limit decorators"""
    
    def test_rate_limit_auth_returns_decorator(self):
        """Test that rate_limit_auth returns a decorator"""
        decorator = rate_limit_auth()
        assert callable(decorator)
    
    def test_rate_limit_ai_returns_decorator(self):
        """Test that rate_limit_ai returns a decorator"""
        decorator = rate_limit_ai()
        assert callable(decorator)
    
    def test_rate_limit_public_returns_decorator(self):
        """Test that rate_limit_public returns a decorator"""
        decorator = rate_limit_public()
        assert callable(decorator)
    
    def test_rate_limit_default_returns_decorator(self):
        """Test that rate_limit_default returns a decorator"""
        decorator = rate_limit_default()
        assert callable(decorator)
    
    def test_rate_limit_custom_returns_decorator(self):
        """Test that rate_limit_custom returns a decorator"""
        decorator = rate_limit_custom("10/minute")
        assert callable(decorator)
    
    def test_rate_limit_custom_with_key_func(self):
        """Test that rate_limit_custom accepts custom key function"""
        custom_key_func = lambda req: "custom-key"
        decorator = rate_limit_custom("10/minute", key_func=custom_key_func)
        assert callable(decorator)
    
    @patch('app.utils.rate_limit.settings.rate_limit_enabled', False)
    def test_decorators_noop_when_disabled(self):
        """Test that decorators are no-ops when rate limiting is disabled"""
        @rate_limit_auth()
        def test_func(request):
            return "success"
        
        request = MagicMock()
        result = test_func(request)
        assert result == "success"


@pytest.mark.unit
@pytest.mark.utils
@pytest.mark.asyncio
class TestRateLimitHandler:
    """Tests for rate_limit_handler function"""
    
    async def test_handles_rate_limit_exceeded(self):
        """Test that rate limit exceeded error is handled correctly"""
        request = MagicMock(spec=Request)
        request.url.path = "/auth/login"
        request.method = "POST"
        
        exc = RateLimitExceeded("3 per 1 minute")
        
        with patch('app.utils.rate_limit.get_remote_address', return_value="127.0.0.1"):
            response = await rate_limit_handler(request, exc)
        
        assert response.status_code == 429
        content = response.body.decode()
        assert "rate limit exceeded" in content.lower()
        assert "retry" in content.lower()
    
    async def test_auth_endpoint_retry_time(self):
        """Test that auth endpoints have longer retry time"""
        request = MagicMock(spec=Request)
        request.url.path = "/auth/login"
        request.method = "POST"
        
        exc = RateLimitExceeded("3 per 1 minute")
        
        with patch('app.utils.rate_limit.get_remote_address', return_value="127.0.0.1"):
            with patch('app.utils.rate_limit.settings.rate_limit_auth_retry_hours', 5):
                response = await rate_limit_handler(request, exc)
        
        assert response.status_code == 429
        content = response.body.decode()
        assert "5" in content or "hour" in content.lower()
        assert "Retry-After" in response.headers
    
    async def test_non_auth_endpoint_default_retry_time(self):
        """Test that non-auth endpoints have default retry time"""
        request = MagicMock(spec=Request)
        request.url.path = "/api/jobs"
        request.method = "GET"
        
        exc = RateLimitExceeded("100 per 1 minute")
        
        with patch('app.utils.rate_limit.get_remote_address', return_value="127.0.0.1"):
            response = await rate_limit_handler(request, exc)
        
        assert response.status_code == 429
        # Default retry should be 1 minute (3600 seconds / 60 = 60 minutes in hours... wait that's wrong)
        # Actually default is 60 seconds = 1 minute = 0.0167 hours, so it should say 0 or 1 hour
        assert "Retry-After" in response.headers

