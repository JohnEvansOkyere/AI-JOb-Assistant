"""
API Routes
Export all API routers
"""

from .auth import router as auth_router
from .health import router as health_router
from .job_descriptions import router as job_descriptions_router
from .job_descriptions_public import router as job_descriptions_public_router
from .cvs import router as cvs_router
from .tickets import router as tickets_router
from .interviews import router as interviews_router
from .applications import router as applications_router
from .application_forms import router as application_forms_router
from .stats import router as stats_router
from .candidates import router as candidates_router

__all__ = [
    "auth_router",
    "health_router",
    "job_descriptions_router",
    "job_descriptions_public_router",
    "cvs_router",
    "tickets_router",
    "interviews_router",
    "applications_router",
    "application_forms_router",
    "stats_router",
    "candidates_router",
]
