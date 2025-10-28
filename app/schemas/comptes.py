"""
Schémas Pydantic pour les Comptes
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from decimal import Decimal


# ============================================================================
# COMPTES
# ============================================================================

class CompteBase(BaseModel):
    """Base pour les comptes"""
    NumeroCompte: str = Field(..., max_length=50)
    TypeCompte: str = Field(..., pattern="^(INVESTISSEMENT|CASH|EPARGNE)$")
    Devise: str = Field(default="HTG", max_length=3)
    Solde: Decimal = Field(default=0, ge=0)
    SoldeDisponible: Decimal = Field(default=0, ge=0)
    StatutCompte: str = Field(default="ACTIF", pattern="^(ACTIF|SUSPENDU|FERME)$")


class CompteCreate(CompteBase):
    """Création d'un compte"""
    ClientID: int = Field(..., description="ID du client titulaire principal")
    Role: str = Field(default="TITULAIRE_PRINCIPAL", description="Rôle du client sur ce compte")


class CompteUpdate(BaseModel):
    """Mise à jour d'un compte"""
    StatutCompte: Optional[str] = Field(None, pattern="^(ACTIF|SUSPENDU|FERME)$")
    Solde: Optional[Decimal] = Field(None, ge=0)
    SoldeDisponible: Optional[Decimal] = Field(None, ge=0)


class CompteResponse(CompteBase):
    """Réponse avec les informations d'un compte"""
    CompteID: int
    DateOuverture: datetime
    DateFermeture: Optional[datetime] = None

    class Config:
        from_attributes = True


class CompteDetail(CompteResponse):
    """Détails complets d'un compte avec les rôles"""
    roles: List['CompteRoleResponse'] = []

    class Config:
        from_attributes = True


# ============================================================================
# COMPTES ROLES (Relation Client-Compte)
# ============================================================================

class CompteRoleBase(BaseModel):
    """Base pour les rôles de compte"""
    Role: str = Field(..., pattern="^(TITULAIRE_PRINCIPAL|TITULAIRE_SECONDAIRE|MANDATAIRE|OBSERVATEUR|ADMINISTRATEUR|BENEFICIAIRE)$")
    EstActif: bool = True


class CompteRoleCreate(CompteRoleBase):
    """Ajout d'un client à un compte"""
    CompteID: int
    ClientID: int


class CompteRoleUpdate(BaseModel):
    """Mise à jour d'un rôle"""
    EstActif: Optional[bool] = None
    DateFin: Optional[datetime] = None


class CompteRoleResponse(CompteRoleBase):
    """Réponse avec les informations d'un rôle"""
    CompteRoleID: int
    CompteID: int
    ClientID: int
    DateDebut: datetime
    DateFin: Optional[datetime] = None

    class Config:
        from_attributes = True


# ============================================================================
# RÉPONSES SPÉCIFIQUES
# ============================================================================

class ComptesListResponse(BaseModel):
    """Liste des comptes d'un client"""
    total: int
    comptes: List[CompteResponse]


class CompteCreateResponse(BaseModel):
    """Réponse après création d'un compte"""
    success: bool
    message: str
    compte: CompteResponse
