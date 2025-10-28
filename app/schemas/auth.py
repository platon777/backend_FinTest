"""
Schémas Pydantic pour l'authentification - VERSION SIMPLE
"""
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime


# ============================================================================
# INSCRIPTION
# ============================================================================

class RegisterRequest(BaseModel):
    """Inscription d'un nouveau client"""
    # Type de client
    client_type: str = Field(..., pattern="^(INDIVIDUEL|INSTITUTIONNEL)$")

    # Auth
    email: EmailStr
    password: str = Field(..., min_length=6)

    # Client individuel
    prenom: Optional[str] = None
    nom: Optional[str] = None
    date_naissance: Optional[str] = None  # Format: YYYY-MM-DD
    numero_piece_identite: Optional[str] = None

    # Client institutionnel
    nom_entreprise: Optional[str] = None
    numero_registre_commerce: Optional[str] = None
    nom_representant_legal: Optional[str] = None


class RegisterResponse(BaseModel):
    """Réponse après inscription"""
    success: bool
    message: str
    client_id: int
    email: str


# ============================================================================
# CONNEXION
# ============================================================================

class LoginRequest(BaseModel):
    """Requête de connexion"""
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    """Tokens JWT"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # En secondes


class ClientInfo(BaseModel):
    """Informations du client connecté"""
    client_id: int
    email: str
    client_type: str
    prenom: Optional[str] = None
    nom: Optional[str] = None
    nom_entreprise: Optional[str] = None

    class Config:
        from_attributes = True


class LoginResponse(BaseModel):
    """Réponse complète de connexion"""
    success: bool
    message: str
    tokens: TokenResponse
    client: ClientInfo


# ============================================================================
# REFRESH TOKEN
# ============================================================================

class RefreshTokenRequest(BaseModel):
    """Rafraîchir le token"""
    refresh_token: str


# ============================================================================
# PROFIL UTILISATEUR
# ============================================================================

class ClientProfile(BaseModel):
    """Profil complet du client"""
    client_id: int
    client_type: str
    email: str
    statut_client: str
    profil_risque: Optional[str]
    date_creation: datetime

    # Individuel
    prenom: Optional[str] = None
    nom: Optional[str] = None
    date_naissance: Optional[str] = None
    profession: Optional[str] = None

    # Institutionnel
    nom_entreprise: Optional[str] = None
    numero_registre_commerce: Optional[str] = None

    class Config:
        from_attributes = True


# ============================================================================
# ERREURS
# ============================================================================

class ErrorResponse(BaseModel):
    """Réponse d'erreur"""
    success: bool = False
    error: str
    message: str
