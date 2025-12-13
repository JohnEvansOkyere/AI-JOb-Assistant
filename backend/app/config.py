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
    groq_model: str = "llama-3.1-70b-versatile"
    
    gemini_api_key: Optional[str] = None
    gemini_model: str = "gemini-1.5-flash"
    
    # Primary AI provider (openai, groq, gemini)
    primary_ai_provider: str = "openai"
    
    # Voice Services
    whisper_api_key: Optional[str] = None  # Uses OpenAI API key
    deepgram_api_key: Optional[str] = None
    stt_provider: str = "whisper"  # whisper or deepgram
    
    elevenlabs_api_key: str
    elevenlabs_voice_id: str
    
    # Interview Configuration
    max_interview_duration_seconds: int = 1800  # 30 minutes
    default_interview_duration_seconds: int = 1200  # 20 minutes
    max_tokens_per_interview: int = 50000
    
    # Storage
    supabase_storage_bucket_cvs: str = "cvs"
    supabase_storage_bucket_audio: str = "interview-audio"
    
    # Logging
    log_level: str = "INFO"
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()

