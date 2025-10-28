"""
Schémas Pydantic pour les Transactions
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Literal
from datetime import datetime
from decimal import Decimal


# ============================================================================
# TRANSACTIONS
# ============================================================================

class TransactionBase(BaseModel):
    """Base pour les transactions"""
    TypeTransaction: str = Field(..., pattern="^(DEPOT|RETRAIT|SOUSCRIPTION|RACHAT|PAIEMENT_INTERET|REMBOURSEMENT_MATURITE|TRANSFERT)$")
    Montant: Decimal = Field(..., gt=0)
    Devise: str = Field(..., max_length=3)
    Description: Optional[str] = None


class TransactionDepot(TransactionBase):
    """Dépôt sur un compte"""
    TypeTransaction: Literal["DEPOT"] = "DEPOT"
    CompteDestination: int = Field(..., description="Compte où déposer l'argent")


class TransactionRetrait(TransactionBase):
    """Retrait d'un compte"""
    TypeTransaction: Literal["RETRAIT"] = "RETRAIT"
    CompteSource: int = Field(..., description="Compte d'où retirer l'argent")


class TransactionTransfert(TransactionBase):
    """Transfert entre deux comptes"""
    TypeTransaction: Literal["TRANSFERT"] = "TRANSFERT"
    CompteSource: int = Field(..., description="Compte source")
    CompteDestination: int = Field(..., description="Compte destination")


class TransactionSouscription(TransactionBase):
    """Transaction de souscription à un instrument"""
    TypeTransaction: Literal["SOUSCRIPTION"] = "SOUSCRIPTION"
    CompteSource: int = Field(..., description="Compte d'où prélever les fonds")
    SouscriptionID: Optional[int] = None


class TransactionRachat(TransactionBase):
    """Transaction de rachat d'une souscription"""
    TypeTransaction: Literal["RACHAT"] = "RACHAT"
    CompteDestination: int = Field(..., description="Compte où créditer les fonds")
    SouscriptionID: int = Field(..., description="Souscription à racheter")


class TransactionCreate(BaseModel):
    """Création générique d'une transaction"""
    TypeTransaction: str = Field(..., pattern="^(DEPOT|RETRAIT|SOUSCRIPTION|RACHAT|PAIEMENT_INTERET|REMBOURSEMENT_MATURITE|TRANSFERT)$")
    CompteSource: Optional[int] = None
    CompteDestination: Optional[int] = None
    Montant: Decimal = Field(..., gt=0)
    Devise: str = Field(..., max_length=3)
    Description: Optional[str] = None
    SouscriptionID: Optional[int] = None
    EstAutomatique: bool = False


class TransactionUpdate(BaseModel):
    """Mise à jour d'une transaction"""
    StatutTransaction: str = Field(..., pattern="^(EN_ATTENTE|EXECUTEE|ECHOUEE|ANNULEE)$")
    DateExecution: Optional[datetime] = None
    Description: Optional[str] = None


class TransactionResponse(BaseModel):
    """Réponse avec les informations d'une transaction"""
    TransactionID: int
    TypeTransaction: str
    CompteSource: Optional[int] = None
    CompteDestination: Optional[int] = None
    Montant: Decimal
    Devise: str
    Description: Optional[str] = None
    StatutTransaction: str
    DateCreation: datetime
    DateExecution: Optional[datetime] = None
    EstAutomatique: bool
    SouscriptionID: Optional[int] = None

    class Config:
        from_attributes = True


class TransactionDetail(TransactionResponse):
    """Détails complets d'une transaction"""
    compte_source_numero: Optional[str] = None
    compte_destination_numero: Optional[str] = None


# ============================================================================
# RÉPONSES SPÉCIFIQUES
# ============================================================================

class TransactionsListResponse(BaseModel):
    """Liste des transactions"""
    total: int
    transactions: List[TransactionDetail]


class TransactionCreateResponse(BaseModel):
    """Réponse après création d'une transaction"""
    success: bool
    message: str
    transaction: TransactionResponse


class TransactionExecuteResponse(BaseModel):
    """Réponse après exécution d'une transaction"""
    success: bool
    message: str
    transaction: TransactionResponse
    nouveau_solde_source: Optional[Decimal] = None
    nouveau_solde_destination: Optional[Decimal] = None


class HistoriqueTransactionsResponse(BaseModel):
    """Historique des transactions d'un compte"""
    compte_id: int
    compte_numero: str
    total: int
    transactions: List[TransactionDetail]
