"""
Schémas Pydantic pour les Souscriptions (Investissements)
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime, date
from decimal import Decimal


# ============================================================================
# SOUSCRIPTIONS
# ============================================================================

class SouscriptionBase(BaseModel):
    """Base pour les souscriptions"""
    CompteID: int
    InstrumentID: int
    MontantInvesti: Decimal = Field(..., gt=0, description="Montant investi en devise du compte")
    NombreUnites: Optional[Decimal] = Field(None, gt=0)
    TauxSouscription: Optional[Decimal] = Field(None, ge=0, le=100)


class SouscriptionCreate(SouscriptionBase):
    """Création d'une souscription (investissement)"""
    pass


class SouscriptionUpdate(BaseModel):
    """Mise à jour d'une souscription"""
    ValeurActuelle: Optional[Decimal] = Field(None, ge=0)
    InteretsAccumules: Optional[Decimal] = Field(None, ge=0)
    StatutSouscription: Optional[str] = Field(None, pattern="^(ACTIVE|MATURE|RACHETEE)$")


class SouscriptionResponse(SouscriptionBase):
    """Réponse avec les informations d'une souscription"""
    SouscriptionID: int
    DateSouscription: datetime
    DateMaturiteEffective: Optional[date] = None
    ValeurActuelle: Optional[Decimal] = None
    InteretsAccumules: Decimal = 0
    StatutSouscription: str

    class Config:
        from_attributes = True


class SouscriptionDetail(SouscriptionResponse):
    """Détails complets d'une souscription"""
    instrument_nom: Optional[str] = None
    instrument_code: Optional[str] = None
    emetteur: Optional[str] = None
    taux_rendement: Optional[Decimal] = None


# ============================================================================
# PAIEMENTS D'INTÉRÊTS
# ============================================================================

class PaiementInteretBase(BaseModel):
    """Base pour les paiements d'intérêts"""
    SouscriptionID: int
    DatePaiement: datetime
    MontantInteret: Decimal = Field(..., ge=0)
    StatutPaiement: str = Field(..., pattern="^(PLANIFIE|EXECUTE|ECHOUE)$")


class PaiementInteretCreate(PaiementInteretBase):
    """Création d'un paiement d'intérêt"""
    TransactionID: Optional[int] = None


class PaiementInteretResponse(PaiementInteretBase):
    """Réponse avec un paiement d'intérêt"""
    PaiementID: int
    TransactionID: Optional[int] = None

    class Config:
        from_attributes = True


# ============================================================================
# RÉPONSES SPÉCIFIQUES
# ============================================================================

class SouscriptionsListResponse(BaseModel):
    """Liste des souscriptions"""
    total: int
    souscriptions: List[SouscriptionDetail]


class SouscriptionCreateResponse(BaseModel):
    """Réponse après création d'une souscription"""
    success: bool
    message: str
    souscription: SouscriptionResponse
    transaction_id: Optional[int] = None


class PortefeuilleResponse(BaseModel):
    """Vue du portefeuille d'un client"""
    total_investi: Decimal
    valeur_actuelle_totale: Decimal
    interets_accumules_total: Decimal
    nombre_souscriptions: int
    souscriptions: List[SouscriptionDetail]


class PaiementsInteretsListResponse(BaseModel):
    """Liste des paiements d'intérêts"""
    total: int
    paiements: List[PaiementInteretResponse]
