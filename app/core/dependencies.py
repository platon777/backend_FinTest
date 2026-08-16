from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.models import Client
from app.services.auth_service import AuthService


bearer_scheme = HTTPBearer(auto_error=True)


def get_current_client(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> Client:
    client = AuthService.get_client_from_access_token(db, credentials.credentials)
    if client is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Jeton d'accès invalide", headers={"WWW-Authenticate": "Bearer"})
    return client


def get_current_active_client(client: Client = Depends(get_current_client)) -> Client:
    if client.status != "ACTIF" or not client.auth or not client.auth.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Client suspendu ou fermé")
    return client
