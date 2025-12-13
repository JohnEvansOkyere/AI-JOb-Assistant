"""
FastAPI Application Entry Point
Main application setup and configuration
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.config import settings
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

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    """Application startup tasks"""
    logger.info("Application starting", env=settings.app_env)


@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown tasks"""
    logger.info("Application shutting down")


@app.get("/health")
async def health_check():
    """
    Health check endpoint
    
    Returns:
        Health status of the application
    """
    return JSONResponse({
        "status": "healthy",
        "version": "0.1.0",
        "environment": settings.app_env
    })


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "AI Voice Interview Platform API",
        "version": "0.1.0",
        "docs": "/docs" if settings.app_debug else "disabled"
    }


# Import and include routers (will be added in later phases)
# from app.api import auth, jobs, interviews, etc.

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.app_debug
    )

