"""
Application Configuration
Manages environment variables and application settings
"""

from pydantic_settings import BaseSettings
from typing import List, Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # Application
    app_name: str = "AI Voice Interview Platform"
    app_env: str = "development"
    app_debug: bool = True
    secret_key: str
    allowed_origins: List[str] = ["http://localhost:3000"]
    
    # Supabase
    supabase_url: str
    supabase_key: str
    supabase_service_key: str
    database_url: Optional[str] = None
    
    # AI Models
    openai_api_key: Optional[str] = None
    openai_model: str = "gpt-4o-mini"
    
    groq_api_key: Optional[str] = None
    groq_model: str = "mixtral-8x7b-32768"  # Mixtral - fast and high quality
    # Other available Groq models:
    # - "mixtral-8x22b-instruct-32768" (larger, better quality, slower)
    # - "llama-3.3-70b-versatile" (Llama - good alternative)
    # - "llama-3.1-8b-instant" (Llama - very fast, smaller)
    # - "gemma-7b-it" (Google Gemma)
    # - "gemma2-9b-it" (Google Gemma2 - newer)
    
    gemini_api_key: Optional[str] = None
    gemini_model: str = "gemini-pro"  # Updated to use stable model name
    
    # Grok (x.ai) - OpenAI compatible API
    grok_api_key: Optional[str] = None
    grok_model: str = "grok-4-latest"
    
    # Primary AI provider (openai, grok, groq, gemini)
    primary_ai_provider: str = "openai"
    
    # Voice Services
    whisper_api_key: Optional[str] = None  # Uses OpenAI API key
    deepgram_api_key: Optional[str] = None
    stt_provider: str = "whisper"  # whisper or deepgram
    
    elevenlabs_api_key: Optional[str] = None
    elevenlabs_voice_id: Optional[str] = None
    
    # Interview Configuration
    max_interview_duration_seconds: int = 1800  # 30 minutes
    default_interview_duration_seconds: int = 1200  # 20 minutes
    max_tokens_per_interview: int = 50000
    
    # Storage
    supabase_storage_bucket_cvs: str = "cvs"
    supabase_storage_bucket_audio: str = "interview-audio"
    
    # Logging
    log_level: str = "INFO"
    
    # Email Service (Resend + SMTP)
    resend_api_key: Optional[str] = None
    email_from_address: str = "noreply@example.com"
    email_from_name: str = "AI Interview Platform"
    email_reply_to: Optional[str] = None
    
    # SMTP Configuration (for Gmail and other SMTP servers)
    smtp_enabled: bool = False
    smtp_host: Optional[str] = None  # e.g., smtp.gmail.com
    smtp_port: int = 587
    smtp_username: Optional[str] = None  # Gmail address
    smtp_password: Optional[str] = None  # Gmail App Password (not regular password)
    smtp_use_tls: bool = True
    email_provider: str = "resend"  # "resend" or "smtp"
    
    # Automatic Follow-Up Emails
    followup_emails_enabled: bool = True
    followup_reassurance_days: int = 14  # Days after application to send reassurance email
    followup_rejection_days: int = 30  # Days after application to send auto-rejection email
    followup_check_hour: int = 9  # Hour of day to run check (0-23, default 9 AM)
    followup_check_minute: int = 0  # Minute of hour to run check (0-59)
    
    # Calendar Integration
    google_calendar_client_id: Optional[str] = None
    google_calendar_client_secret: Optional[str] = None
    google_calendar_redirect_uri: Optional[str] = None
    
    # Rate Limiting
    rate_limit_enabled: bool = True
    rate_limit_storage_uri: Optional[str] = None  # Redis URI for distributed rate limiting (optional)
    
    # Rate limit defaults (requests per time window)
    # Format: "number/time_unit" where time_unit is: second, minute, hour, day
    rate_limit_default: str = "100/minute"  # Default for most endpoints
    rate_limit_auth: str = "3/minute"  # Login/register endpoints (4th request will be blocked)
    rate_limit_auth_retry_hours: int = 5  # Hours to wait before retry after auth rate limit
    rate_limit_ai: str = "10/hour"  # AI analysis endpoints (expensive!)
    rate_limit_public: str = "20/hour"  # Public application forms
    
    # Sentry Error Tracking
    sentry_dsn: Optional[str] = None  # Get from https://sentry.io
    sentry_environment: Optional[str] = None  # production, staging, development (defaults to app_env)
    sentry_traces_sample_rate: float = 1.0  # 0.0 to 1.0 (1.0 = 100% of transactions, lower for high traffic)
    sentry_profiles_sample_rate: float = 1.0  # Performance profiling sample rate
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()

