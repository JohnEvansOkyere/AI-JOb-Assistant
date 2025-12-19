"""
Input Validation and Sanitization Utilities
Provides validation and sanitization for user inputs to prevent XSS and other attacks
"""

import re
from typing import Optional
from email_validator import validate_email, EmailNotValidError
import structlog

logger = structlog.get_logger()

# Patterns for validation
PHONE_PATTERN = re.compile(r'^\+?[\d\s\-\(\)]{7,20}$')
URL_PATTERN = re.compile(
    r'^https?://'  # http:// or https://
    r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
    r'localhost|'  # localhost...
    r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
    r'(?::\d+)?'  # optional port
    r'(?:/?|[/?]\S+)$', re.IGNORECASE
)


def sanitize_html(text: Optional[str]) -> str:
    """
    Basic HTML sanitization to prevent XSS attacks
    Note: For production, consider using a library like bleach
    
    Args:
        text: Input text that may contain HTML
        
    Returns:
        Sanitized text with dangerous HTML removed
    """
    if not text:
        return ""
    
    # Remove script tags and their content
    text = re.sub(r'<script[^>]*>.*?</script>', '', text, flags=re.IGNORECASE | re.DOTALL)
    
    # Remove event handlers (onclick, onerror, etc.)
    text = re.sub(r'\s*on\w+\s*=\s*["\'][^"\']*["\']', '', text, flags=re.IGNORECASE)
    
    # Remove javascript: protocol
    text = re.sub(r'javascript:', '', text, flags=re.IGNORECASE)
    
    # Remove data: protocol (can be used for XSS)
    text = re.sub(r'data:text/html', '', text, flags=re.IGNORECASE)
    
    return text.strip()


def validate_email_address(email: str) -> str:
    """
    Validate email address format
    
    Args:
        email: Email address to validate
        
    Returns:
        Validated email address
        
    Raises:
        ValueError: If email is invalid
    """
    if not email or not isinstance(email, str):
        raise ValueError("Email address is required")
    
    email = email.strip().lower()
    
    try:
        # Use email-validator library for proper validation
        validated = validate_email(email, check_deliverability=False)
        return validated.email
    except EmailNotValidError as e:
        raise ValueError(f"Invalid email address: {str(e)}")


def validate_phone_number(phone: Optional[str]) -> Optional[str]:
    """
    Validate phone number format
    
    Args:
        phone: Phone number to validate
        
    Returns:
        Validated phone number or None if empty
        
    Raises:
        ValueError: If phone number format is invalid
    """
    if not phone:
        return None
    
    phone = phone.strip()
    
    if not PHONE_PATTERN.match(phone):
        raise ValueError("Invalid phone number format. Please use international format (e.g., +1234567890)")
    
    return phone


def validate_url(url: Optional[str]) -> Optional[str]:
    """
    Validate URL format
    
    Args:
        url: URL to validate
        
    Returns:
        Validated URL or None if empty
        
    Raises:
        ValueError: If URL format is invalid
    """
    if not url:
        return None
    
    url = url.strip()
    
    # Add https:// if no protocol specified
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
    
    if not URL_PATTERN.match(url):
        raise ValueError("Invalid URL format")
    
    return url


def sanitize_text_input(text: Optional[str], max_length: Optional[int] = None) -> str:
    """
    Sanitize general text input
    
    Args:
        text: Input text
        max_length: Maximum allowed length
        
    Returns:
        Sanitized text
    """
    if not text:
        return ""
    
    # Remove null bytes
    text = text.replace("\x00", "")
    
    # Strip whitespace
    text = text.strip()
    
    # Limit length if specified
    if max_length and len(text) > max_length:
        text = text[:max_length]
        logger.warning("Text input truncated", original_length=len(text), max_length=max_length)
    
    return text

