"""
Environment Variable Validation
Validates required environment variables on application startup
"""

from typing import List, Optional
from app.config import settings
import structlog

logger = structlog.get_logger()


class EnvironmentValidationError(Exception):
    """Raised when environment validation fails"""
    pass


def validate_required_settings() -> List[str]:
    """
    Validate required environment variables
    
    Returns:
        List of validation errors (empty if all valid)
    """
    errors = []
    
    # Required settings
    required_settings = {
        "secret_key": "SECRET_KEY is required for JWT token signing",
        "supabase_url": "SUPABASE_URL is required for database connection",
        "supabase_key": "SUPABASE_KEY is required for database connection",
        "supabase_service_key": "SUPABASE_SERVICE_KEY is required for admin operations",
    }
    
    for setting_name, error_message in required_settings.items():
        value = getattr(settings, setting_name, None)
        if not value or (isinstance(value, str) and value.strip() == ""):
            errors.append(error_message)
    
    # Validate secret key length (should be at least 32 characters for security)
    if settings.secret_key and len(settings.secret_key) < 32:
        errors.append("SECRET_KEY must be at least 32 characters long for security")
    
    # Validate URLs
    if settings.supabase_url:
        if not settings.supabase_url.startswith(('http://', 'https://')):
            errors.append("SUPABASE_URL must be a valid URL starting with http:// or https://")
    
    # Validate email configuration (at least one email provider should be configured)
    if settings.email_provider == "resend":
        if not settings.resend_api_key:
            errors.append("RESEND_API_KEY is required when email_provider is 'resend'")
    elif settings.email_provider == "smtp":
        if not settings.smtp_enabled:
            errors.append("SMTP_ENABLED must be True when email_provider is 'smtp'")
        if not settings.smtp_host:
            errors.append("SMTP_HOST is required when using SMTP")
        if not settings.smtp_username:
            errors.append("SMTP_USERNAME is required when using SMTP")
        if not settings.smtp_password:
            errors.append("SMTP_PASSWORD is required when using SMTP")
    
    # Validate rate limiting configuration
    if settings.rate_limit_enabled:
        try:
            # Try to parse rate limit strings to ensure they're valid
            for limit_name in ["rate_limit_default", "rate_limit_auth", "rate_limit_ai", "rate_limit_public"]:
                limit_value = getattr(settings, limit_name, None)
                if limit_value:
                    parts = limit_value.split("/")
                    if len(parts) != 2:
                        errors.append(f"{limit_name} must be in format 'number/unit' (e.g., '100/minute')")
                    else:
                        try:
                            int(parts[0])
                        except ValueError:
                            errors.append(f"{limit_name} must start with a number")
                        if parts[1] not in ["second", "minute", "hour", "day"]:
                            errors.append(f"{limit_name} unit must be: second, minute, hour, or day")
        except Exception as e:
            errors.append(f"Error validating rate limit configuration: {str(e)}")
    
    return errors


def validate_environment() -> None:
    """
    Validate environment variables and raise exception if invalid
    
    Raises:
        EnvironmentValidationError: If validation fails
    """
    errors = validate_required_settings()
    
    if errors:
        error_message = "Environment validation failed:\n" + "\n".join(f"  - {error}" for error in errors)
        logger.error("Environment validation failed", errors=errors)
        raise EnvironmentValidationError(error_message)
    
    logger.info("Environment validation passed")

