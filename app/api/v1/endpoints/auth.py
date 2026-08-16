from fastapi import APIRouter, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.database import get_db
from app.models.models import Account, Client
from app.schemas.api import ClientInfo, LoginRequest, LoginResponse, RefreshRequest, RegisterRequest, RegisterResponse, TokenResponse
from app.services.auth_service import AuthService

from fastapi import Depends

router = APIRouter()


def client_info(client: Client) -> dict:
    individual = client.individual_profile
    institutional = client.institutional_profile
    return {
        "client_id": client.id, "email": client.auth.email, "client_type": client.client_type,
        "prenom": individual.first_name if individual else None,
        "nom": individual.last_name if individual else None,
        "nom_entreprise": institutional.company_name if institutional else None,
    }


@router.post("/register", response_model=RegisterResponse, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    try:
        client = AuthService.register_client(db, payload)
        account = db.scalar(select(Account).where(Account.roles.any(client_id=client.id)))
        return RegisterResponse(success=True, message="Inscription réussie", client_id=client.id, email=client.auth.email, account_number=account.account_number)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/login", response_model=LoginResponse)
def login(payload: LoginRequest, request: Request, db: Session = Depends(get_db)):
    try:
        result = AuthService.login(db, payload.email, payload.password, request.client.host if request.client else None)
        return LoginResponse(message="Connexion réussie", tokens=TokenResponse(access_token=result["access_token"], refresh_token=result["refresh_token"], expires_in=result["expires_in"]), client=ClientInfo.model_validate(client_info(result["client"])))
    except ValueError as exc:
        raise HTTPException(status_code=401, detail=str(exc), headers={"WWW-Authenticate": "Bearer"}) from exc


@router.post("/refresh", response_model=TokenResponse)
def refresh(payload: RefreshRequest, request: Request, db: Session = Depends(get_db)):
    try:
        result = AuthService.refresh(db, payload.refresh_token, request.client.host if request.client else None)
        return TokenResponse(access_token=result["access_token"], refresh_token=result["refresh_token"], expires_in=result["expires_in"])
    except ValueError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc


@router.post("/logout")
def logout(payload: RefreshRequest, db: Session = Depends(get_db)):
    AuthService.logout(db, payload.refresh_token)
    return {"success": True, "message": "Déconnexion réussie"}
