from fastapi import APIRouter
from app.api.v1.endpoints import health, auth, users

api_router = APIRouter()

# Include routers
api_router.include_router(health.router, prefix="/health", tags=["Health"])
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(users.router, prefix="/users", tags=["Users"])
