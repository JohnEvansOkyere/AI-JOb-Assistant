"""
API Routes
Export all API routers
"""

from .auth import router as auth_router
from .health import router as health_router
from .job_descriptions import router as job_descriptions_router
from .cvs import router as cvs_router
from .tickets import router as tickets_router
from .interviews import router as interviews_router

__all__ = [
    "auth_router",
    "health_router",
    "job_descriptions_router",
    "cvs_router",
    "tickets_router",
    "interviews_router",
]
