"""
FastAPI Application Entry Point
Main application setup and configuration
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from app.config import settings
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

# Initialize FastAPI app
app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="AI-powered voice interview platform",
    docs_url="/docs" if settings.app_debug else None,
    redoc_url="/redoc" if settings.app_debug else None,
)

# Security headers middleware (must be before CORS)
app.add_middleware(SecurityHeadersMiddleware)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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


@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown tasks"""
    logger.info("Application shutting down")


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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.app_debug
    )

