"""
Schémas Pydantic pour les Instruments Financiers
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import date
from decimal import Decimal


# ============================================================================
# TYPES D'INSTRUMENTS
# ============================================================================

class TypeInstrumentBase(BaseModel):
    """Base pour les types d'instruments"""
    Code: str = Field(..., max_length=50)
    Nom: str = Field(..., max_length=200)
    Description: Optional[str] = None


class TypeInstrumentCreate(TypeInstrumentBase):
    """Création d'un type d'instrument"""
    pass


class TypeInstrumentResponse(TypeInstrumentBase):
    """Réponse avec un type d'instrument"""
    TypeInstrumentID: int

    class Config:
        from_attributes = True


# ============================================================================
# INSTRUMENTS
# ============================================================================

class InstrumentBase(BaseModel):
    """Base pour les instruments"""
    TypeInstrumentID: int
    Code: str = Field(..., max_length=50)
    Nom: str = Field(..., max_length=200)
    Description: Optional[str] = None
    Emetteur: Optional[str] = Field(None, max_length=200)
    TauxRendementAnnuel: Optional[Decimal] = Field(None, ge=0, le=100, description="Taux en %")
    DateEmission: Optional[date] = None
    DateMaturite: Optional[date] = None
    ValeurNominale: Optional[Decimal] = Field(None, ge=0)
    MontantMinimum: Optional[Decimal] = Field(None, ge=0)
    Devise: Optional[str] = Field(default="HTG", max_length=3)
    FrequencePaiementInterets: Optional[str] = Field(None, max_length=20)
    StatutInstrument: str = Field(default="DISPONIBLE", pattern="^(DISPONIBLE|EPUISE|EXPIRE)$")


class InstrumentCreate(InstrumentBase):
    """Création d'un instrument"""
    pass


class InstrumentUpdate(BaseModel):
    """Mise à jour d'un instrument"""
    Nom: Optional[str] = Field(None, max_length=200)
    Description: Optional[str] = None
    TauxRendementAnnuel: Optional[Decimal] = Field(None, ge=0, le=100)
    StatutInstrument: Optional[str] = Field(None, pattern="^(DISPONIBLE|EPUISE|EXPIRE)$")
    MontantMinimum: Optional[Decimal] = Field(None, ge=0)


class InstrumentResponse(InstrumentBase):
    """Réponse avec un instrument"""
    InstrumentID: int

    class Config:
        from_attributes = True


class InstrumentDetail(InstrumentResponse):
    """Détails d'un instrument avec son type"""
    type_instrument: Optional[TypeInstrumentResponse] = None

    class Config:
        from_attributes = True


# ============================================================================
# RÉPONSES SPÉCIFIQUES
# ============================================================================

class InstrumentsListResponse(BaseModel):
    """Liste des instruments disponibles"""
    total: int
    instruments: List[InstrumentResponse]


class InstrumentCreateResponse(BaseModel):
    """Réponse après création d'un instrument"""
    success: bool
    message: str
    instrument: InstrumentResponse


class InstrumentsDisponiblesResponse(BaseModel):
    """Instruments disponibles pour souscription"""
    total: int
    instruments: List[InstrumentDetail]
