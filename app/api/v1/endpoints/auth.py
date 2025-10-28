"""
Endpoints d'authentification - VERSION SIMPLE
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.schemas.auth import (
    RegisterRequest, RegisterResponse,
    LoginRequest, LoginResponse, TokenResponse,
    RefreshTokenRequest, ClientInfo,
    ErrorResponse
)
from app.services.auth_service import AuthService
from app.core.config import settings

router = APIRouter()


@router.post("/register", response_model=RegisterResponse)
def register(
    request: RegisterRequest,
    db: Session = Depends(get_db)
):
    """
    Inscription d'un nouveau client

    - **client_type**: INDIVIDUEL ou INSTITUTIONNEL
    - **email**: Email unique
    - **password**: Mot de passe (min 6 caractères)

    Pour INDIVIDUEL: prenom, nom, date_naissance, numero_piece_identite
    Pour INSTITUTIONNEL: nom_entreprise, numero_registre_commerce, nom_representant_legal
    """
    try:
        client = AuthService.register_client(
            db=db,
            client_type=request.client_type,
            email=request.email,
            password=request.password,
            prenom=request.prenom,
            nom=request.nom,
            date_naissance=request.date_naissance,
            numero_piece_identite=request.numero_piece_identite,
            nom_entreprise=request.nom_entreprise,
            numero_registre_commerce=request.numero_registre_commerce,
            nom_representant_legal=request.nom_representant_legal
        )

        return RegisterResponse(
            success=True,
            message="Inscription réussie",
            client_id=client.ClientID,
            email=request.email
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de l'inscription: {str(e)}"
        )


@router.post("/login", response_model=LoginResponse)
def login(
    request: LoginRequest,
    http_request: Request,
    db: Session = Depends(get_db)
):
    """
    Connexion d'un client

    Retourne un access_token (valide 30 min) et un refresh_token (valide 7 jours)
    """
    try:
        # Récupérer l'IP du client
        ip_address = http_request.client.host if http_request.client else None

        result = AuthService.login(
            db=db,
            email=request.email,
            password=request.password,
            ip_address=ip_address
        )

        # Préparer les infos client
        client = result["client"]
        auth = result["auth"]

        client_info = ClientInfo(
            client_id=client.ClientID,
            email=auth.Email,
            client_type=client.ClientType
        )

        # Ajouter nom/prenom ou nom entreprise
        if hasattr(client, 'individuel') and client.individuel:
            client_info.prenom = client.individuel.Prenom
            client_info.nom = client.individuel.Nom
        elif hasattr(client, 'institutionnel') and client.institutionnel:
            client_info.nom_entreprise = client.institutionnel.NomEntreprise

        tokens = TokenResponse(
            access_token=result["access_token"],
            refresh_token=result["refresh_token"],
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )

        return LoginResponse(
            success=True,
            message="Connexion réussie",
            tokens=tokens,
            client=client_info
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la connexion: {str(e)}"
        )


@router.post("/refresh", response_model=TokenResponse)
def refresh_token(
    request: RefreshTokenRequest,
    db: Session = Depends(get_db)
):
    """
    Rafraîchir l'access token avec le refresh token
    """
    try:
        result = AuthService.refresh_access_token(
            db=db,
            refresh_token_str=request.refresh_token
        )

        return TokenResponse(
            access_token=result["access_token"],
            refresh_token=result["refresh_token"],
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors du rafraîchissement: {str(e)}"
        )


@router.post("/logout")
def logout(
    request: RefreshTokenRequest,
    db: Session = Depends(get_db)
):
    """
    Déconnexion - révoque le refresh token
    """
    try:
        AuthService.logout(db=db, refresh_token_str=request.refresh_token)

        return {
            "success": True,
            "message": "Déconnexion réussie"
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la déconnexion: {str(e)}"
        )
