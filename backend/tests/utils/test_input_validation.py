"""
Tests for input validation utilities
"""

import pytest
from app.utils.input_validation import (
    sanitize_html,
    validate_email_address,
    validate_phone_number,
    validate_url,
    sanitize_text_input
)


@pytest.mark.unit
@pytest.mark.utils
class TestSanitizeHTML:
    """Tests for sanitize_html function"""
    
    def test_removes_script_tags(self):
        """Test that script tags are removed"""
        malicious = "<script>alert('XSS')</script>Hello"
        result = sanitize_html(malicious)
        assert "script" not in result.lower()
        assert "Hello" in result
    
    def test_removes_event_handlers(self):
        """Test that event handlers are removed"""
        malicious = '<div onclick="alert(\'XSS\')">Click me</div>'
        result = sanitize_html(malicious)
        assert "onclick" not in result
    
    def test_removes_javascript_protocol(self):
        """Test that javascript: protocol is removed"""
        malicious = '<a href="javascript:alert(\'XSS\')">Link</a>'
        result = sanitize_html(malicious)
        assert "javascript:" not in result.lower()
    
    def test_removes_data_protocol(self):
        """Test that data:text/html is removed"""
        malicious = '<img src="data:text/html,<script>alert(\'XSS\')</script>">'
        result = sanitize_html(malicious)
        assert "data:text/html" not in result.lower()
    
    def test_handles_none(self):
        """Test that None input returns empty string"""
        result = sanitize_html(None)
        assert result == ""
    
    def test_handles_empty_string(self):
        """Test that empty string returns empty string"""
        result = sanitize_html("")
        assert result == ""
    
    def test_preserves_safe_html(self):
        """Test that safe HTML is preserved"""
        safe = "<p>This is <strong>safe</strong> HTML</p>"
        result = sanitize_html(safe)
        assert "This is" in result
        assert "safe" in result


@pytest.mark.unit
@pytest.mark.utils
class TestValidateEmailAddress:
    """Tests for validate_email_address function"""
    
    def test_valid_email_passes(self):
        """Test that valid emails pass validation"""
        valid_emails = [
            "test@example.com",
            "user.name@example.co.uk",
            "user+tag@example.com",
            "user_name@example-domain.com"
        ]
        
        for email in valid_emails:
            result = validate_email_address(email)
            assert result == email.lower().strip()
    
    def test_invalid_email_raises_value_error(self):
        """Test that invalid emails raise ValueError"""
        invalid_emails = [
            "invalid",
            "@example.com",
            "user@",
            "user @example.com",
            "user@.com",
            "user@example",
        ]
        
        for email in invalid_emails:
            with pytest.raises(ValueError):
                validate_email_address(email)
    
    def test_none_raises_value_error(self):
        """Test that None raises ValueError"""
        with pytest.raises(ValueError):
            validate_email_address(None)
    
    def test_empty_string_raises_value_error(self):
        """Test that empty string raises ValueError"""
        with pytest.raises(ValueError):
            validate_email_address("")
    
    def test_normalizes_to_lowercase(self):
        """Test that email is normalized to lowercase"""
        email = "TEST@EXAMPLE.COM"
        result = validate_email_address(email)
        assert result == "test@example.com"
    
    def test_strips_whitespace(self):
        """Test that whitespace is stripped"""
        email = "  test@example.com  "
        result = validate_email_address(email)
        assert result == "test@example.com"


@pytest.mark.unit
@pytest.mark.utils
class TestValidatePhoneNumber:
    """Tests for validate_phone_number function"""
    
    def test_valid_phone_passes(self):
        """Test that valid phone numbers pass validation"""
        valid_phones = [
            "+1234567890",
            "+1-234-567-8900",
            "(123) 456-7890",
            "123-456-7890",
            "1234567890",
            "+44 20 1234 5678",
            "+1 (555) 123-4567"
        ]
        
        for phone in valid_phones:
            result = validate_phone_number(phone)
            assert result is not None
            assert result.strip() == phone.strip()
    
    def test_invalid_phone_raises_value_error(self):
        """Test that invalid phone numbers raise ValueError"""
        invalid_phones = [
            "123",  # Too short
            "abc123",  # Contains letters
            "123456789012345678901",  # Too long
            "+",  # Just plus sign
            "++1234567890",  # Double plus
        ]
        
        for phone in invalid_phones:
            with pytest.raises(ValueError):
                validate_phone_number(phone)
    
    def test_none_returns_none(self):
        """Test that None returns None"""
        result = validate_phone_number(None)
        assert result is None
    
    def test_empty_string_returns_none(self):
        """Test that empty string returns None"""
        result = validate_phone_number("")
        assert result is None
    
    def test_strips_whitespace(self):
        """Test that whitespace is stripped"""
        phone = "  +1234567890  "
        result = validate_phone_number(phone)
        assert result == "+1234567890"


@pytest.mark.unit
@pytest.mark.utils
class TestValidateURL:
    """Tests for validate_url function"""
    
    def test_valid_url_passes(self):
        """Test that valid URLs pass validation"""
        valid_urls = [
            "https://example.com",
            "http://example.com",
            "https://www.example.com/path",
            "http://example.com:8080/path?query=value",
            "https://subdomain.example.com"
        ]
        
        for url in valid_urls:
            result = validate_url(url)
            assert result is not None
            assert url in result or result.startswith("https://")
    
    def test_adds_https_if_no_protocol(self):
        """Test that https:// is added if no protocol"""
        url = "example.com"
        result = validate_url(url)
        assert result == "https://example.com"
    
    def test_invalid_url_raises_value_error(self):
        """Test that invalid URLs raise ValueError"""
        invalid_urls = [
            "not a url",
            "ht tp://example.com",
            "example",
            "://example.com",
        ]
        
        for url in invalid_urls:
            with pytest.raises(ValueError):
                validate_url(url)
    
    def test_none_returns_none(self):
        """Test that None returns None"""
        result = validate_url(None)
        assert result is None
    
    def test_empty_string_returns_none(self):
        """Test that empty string returns None"""
        result = validate_url("")
        assert result is None
    
    def test_strips_whitespace(self):
        """Test that whitespace is stripped"""
        url = "  https://example.com  "
        result = validate_url(url)
        assert result == "https://example.com"


@pytest.mark.unit
@pytest.mark.utils
class TestSanitizeTextInput:
    """Tests for sanitize_text_input function"""
    
    def test_removes_null_bytes(self):
        """Test that null bytes are removed"""
        text = "Hello\x00World"
        result = sanitize_text_input(text)
        assert "\x00" not in result
        assert "Hello" in result
        assert "World" in result
    
    def test_strips_whitespace(self):
        """Test that whitespace is stripped"""
        text = "  Hello World  "
        result = sanitize_text_input(text)
        assert result == "Hello World"
    
    def test_limits_length(self):
        """Test that length is limited when max_length is specified"""
        text = "A" * 100
        result = sanitize_text_input(text, max_length=50)
        assert len(result) == 50
    
    def test_no_truncation_when_under_limit(self):
        """Test that text is not truncated when under limit"""
        text = "Hello World"
        result = sanitize_text_input(text, max_length=50)
        assert result == "Hello World"
    
    def test_handles_none(self):
        """Test that None returns empty string"""
        result = sanitize_text_input(None)
        assert result == ""
    
    def test_handles_empty_string(self):
        """Test that empty string returns empty string"""
        result = sanitize_text_input("")
        assert result == ""
    
    def test_preserves_content_when_valid(self):
        """Test that valid content is preserved"""
        text = "This is valid content with numbers 123 and symbols !@#"
        result = sanitize_text_input(text)
        assert result == text

