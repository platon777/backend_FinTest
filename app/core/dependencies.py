"""
Dépendances FastAPI pour la sécurité et l'authentification
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.services.auth_service import AuthService
from app.models.models import Client

security = HTTPBearer()


def get_current_client(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> Client:
    """
    Dépendance pour récupérer le client actuel à partir du token JWT

    Usage dans un endpoint:
    ```python
    @router.get("/me")
    def get_profile(current_client: Client = Depends(get_current_client)):
        return current_client
    ```
    """
    try:
        token = credentials.credentials
        client = AuthService.get_current_client(db=db, token=token)
        return client

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur d'authentification: {str(e)}"
        )


def get_current_active_client(
    current_client: Client = Depends(get_current_client)
) -> Client:
    """
    Dépendance pour s'assurer que le client est actif

    Usage:
    ```python
    @router.get("/protected")
    def protected_route(client: Client = Depends(get_current_active_client)):
        return {"message": "Accès autorisé"}
    ```
    """
    if current_client.StatutClient != 'ACTIF':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Compte suspendu ou fermé"
        )

    return current_client
