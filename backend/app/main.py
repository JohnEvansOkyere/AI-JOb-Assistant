"""
FastAPI Application Entry Point
Main application setup and configuration
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from app.config import settings
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from app.api import (
    auth_router,
    health_router,
    job_descriptions_router,
    job_descriptions_public_router,
    cvs_router,
    tickets_router,
    interviews_router,
    applications_router,
    application_forms_router,
    stats_router,
    candidates_router,
    rankings_router,
    voice_router,
    cv_detailed_screening_router,
    detailed_interview_analysis_router,
    emails_router,
    email_templates_router,
    branding_router,
    calendar_router,
    interview_stages_router,
    admin_router,
)
from app.utils.errors import (
    app_exception_handler,
    validation_exception_handler,
    general_exception_handler,
    AppException
)
from app.utils.rate_limit import limiter, rate_limit_handler
from app.utils.security_headers import SecurityHeadersMiddleware
from app.utils.env_validation import validate_environment, EnvironmentValidationError
from app.ai.providers import AIProviderFactory
from slowapi.errors import RateLimitExceeded
import structlog

# Configure structured logging
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.add_log_level,
        structlog.processors.JSONRenderer()
    ],
    wrapper_class=structlog.make_filtering_bound_logger(
        getattr(structlog.stdlib, settings.log_level.upper(), 20)
    ),
    context_class=dict,
    logger_factory=structlog.PrintLoggerFactory(),
    cache_logger_on_first_use=False,
)

logger = structlog.get_logger()

# Initialize Sentry Error Tracking (before creating FastAPI app)
if settings.sentry_dsn:
    sentry_sdk.init(
        dsn=settings.sentry_dsn,
        environment=settings.sentry_environment or settings.app_env,
        traces_sample_rate=settings.sentry_traces_sample_rate,
        profiles_sample_rate=settings.sentry_profiles_sample_rate,
        integrations=[
            FastApiIntegration(),
        ],
        # Don't send sensitive data by default
        send_default_pii=False,  # Set to True if you want to send user info
        # Filter out expected client errors
        ignore_errors=[
            RequestValidationError,  # These are client validation errors, not server errors
        ],
        # Set release version (optional, useful for tracking which code version caused errors)
        # release="myapp@1.0.0",  # Uncomment and set your app version
    )
    logger.info("Sentry error tracking initialized", environment=settings.sentry_environment or settings.app_env)
else:
    logger.info("Sentry error tracking disabled (no SENTRY_DSN configured)")

# Initialize FastAPI app
app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="AI-powered voice interview platform",
    docs_url="/docs" if settings.app_debug else None,
    redoc_url="/redoc" if settings.app_debug else None,
)

# CORS middleware - simple approach
# Use standard CORSMiddleware with origins from settings
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins if settings.allowed_origins else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security headers middleware (adds CORS for Vercel preview URLs)
app.add_middleware(SecurityHeadersMiddleware)

# Register exception handlers
app.add_exception_handler(AppException, app_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(RateLimitExceeded, rate_limit_handler)
app.add_exception_handler(Exception, general_exception_handler)

# Add rate limiter middleware
app.state.limiter = limiter


@app.on_event("startup")
async def startup_event():
    """Application startup tasks"""
    logger.info("Application starting", env=settings.app_env)
    logger.info("CORS allowed origins configured", origins=settings.allowed_origins)
    
    # Validate environment variables
    try:
        validate_environment()
        logger.info("Environment validation passed")
    except EnvironmentValidationError as e:
        logger.error("Environment validation failed", error=str(e))
        # In production, you might want to exit here
        # For development, we'll log and continue
        if settings.app_env == "production":
            raise
    
    # Initialize AI model/provider
    try:
        available_providers = AIProviderFactory.get_available_providers()
        if available_providers:
            primary_provider = settings.primary_ai_provider
            # Sort available providers by priority for logging
            priority_order = ["openai", "grok", "groq", "gemini"]
            ordered_available = [p for p in priority_order if p in available_providers]
            
            if primary_provider in available_providers:
                # Try to create the provider to verify it's properly configured
                provider = AIProviderFactory.create_provider(primary_provider)
                model_name = getattr(provider, 'model', 'unknown')
                logger.info(
                    "AI model initialized",
                    provider=primary_provider,
                    model=model_name,
                    available_providers=", ".join(ordered_available)
                )
            else:
                logger.warning(
                    "AI model initialization skipped - primary provider not available",
                    primary_provider=primary_provider,
                    available_providers=", ".join(available_providers)
                )
        else:
            logger.warning("AI model initialization skipped - no API keys configured")
    except Exception as e:
        logger.warning(
            "AI model initialization failed",
            error=str(e),
            provider=settings.primary_ai_provider
        )
    
    # Start scheduler for automatic follow-up emails
    try:
        from app.services.scheduler_service import start_scheduler
        start_scheduler()
    except Exception as e:
        logger.error(
            "Failed to start scheduler",
            error=str(e),
            exc_info=True
        )
        # Don't fail startup if scheduler fails - it's not critical


@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown tasks"""
    logger.info("Application shutting down")
    
    # Stop scheduler gracefully
    try:
        from app.services.scheduler_service import stop_scheduler
        stop_scheduler()
    except Exception as e:
        logger.error(
            "Error stopping scheduler",
            error=str(e),
            exc_info=True
        )


# Health check is now handled by health_router
# Keeping this for backward compatibility but it will be overridden by the router


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "AI Voice Interview Platform API",
        "version": "0.1.0",
        "docs": "/docs" if settings.app_debug else "disabled"
    }


@app.get("/cors-test")
async def cors_test(request: Request):
    """Test endpoint to verify CORS is working"""
    origin = request.headers.get("origin")
    return {
        "message": "CORS test successful",
        "origin": origin,
        "allowed_origins": settings.allowed_origins,
        "is_vercel": "vercel.app" in origin if origin else False
    }


# Include API routers
app.include_router(auth_router)
app.include_router(health_router)
app.include_router(job_descriptions_router)
app.include_router(job_descriptions_public_router)  # Public job viewing
app.include_router(cvs_router)
app.include_router(tickets_router)
app.include_router(interviews_router)
app.include_router(applications_router)
app.include_router(application_forms_router)
app.include_router(stats_router)
app.include_router(candidates_router)
app.include_router(rankings_router)
app.include_router(voice_router)
app.include_router(cv_detailed_screening_router)
app.include_router(detailed_interview_analysis_router)
app.include_router(emails_router)
app.include_router(email_templates_router)
app.include_router(branding_router)
app.include_router(calendar_router)
app.include_router(interview_stages_router)
app.include_router(admin_router)  # Admin dashboard (admin-only)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.app_debug
    )

