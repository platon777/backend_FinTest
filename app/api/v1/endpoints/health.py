from fastapi import APIRouter
from datetime import datetime
from app.core.config import settings

router = APIRouter()


@router.get("/")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "app_name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.APP_ENV,
        "timestamp": datetime.utcnow().isoformat(),
    }


@router.get("/ready")
async def readiness_check():
    """Readiness check endpoint."""
    # Add checks for database, redis, etc.
    return {
        "status": "ready",
        "checks": {
            "database": "not_configured",
            "redis": "not_configured",
        }
    }


@router.get("/live")
async def liveness_check():
    """Liveness check endpoint."""
    return {
        "status": "alive",
        "timestamp": datetime.utcnow().isoformat(),
    }
