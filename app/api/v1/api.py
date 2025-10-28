from fastapi import APIRouter
from app.api.v1.endpoints import auth, users, comptes, instruments, souscriptions, transactions

api_router = APIRouter()

# Include routers
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(users.router, prefix="/users", tags=["Users"])
api_router.include_router(comptes.router, prefix="/comptes", tags=["Comptes"])
api_router.include_router(instruments.router, prefix="/instruments", tags=["Instruments"])
api_router.include_router(souscriptions.router, prefix="/souscriptions", tags=["Souscriptions"])
api_router.include_router(transactions.router, prefix="/transactions", tags=["Transactions"])
