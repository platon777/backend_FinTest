from fastapi import APIRouter

from app.api.v1.endpoints import assistant, auth, comptes, dashboard, instruments, ordres, profil, souscriptions, transactions, users

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(users.router, prefix="/users", tags=["Users"])
api_router.include_router(profil.router, prefix="/profil", tags=["Profil KYC"])
api_router.include_router(comptes.router, prefix="/comptes", tags=["Comptes"])
api_router.include_router(instruments.router, prefix="/instruments", tags=["Instruments"])
api_router.include_router(souscriptions.router, prefix="/souscriptions", tags=["Souscriptions"])
api_router.include_router(transactions.router, prefix="/transactions", tags=["Transactions"])
api_router.include_router(ordres.router, prefix="/ordres", tags=["Ordres d'investissement"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["Dashboard"])
api_router.include_router(assistant.router, prefix="/assistant", tags=["Assistant IA"])
