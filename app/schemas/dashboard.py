"""
Schemas Pydantic pour le Dashboard
Correspond aux vues SQL créées pour le portail client
"""
from pydantic import BaseModel, ConfigDict
from typing import List, Optional
from datetime import datetime, date
from decimal import Decimal


# ============================================================================
# DASHBOARD OVERVIEW - Vue d'ensemble du portefeuille
# ============================================================================

class CompteOverview(BaseModel):
    """Vue d'ensemble d'un compte spécifique"""
    compte_id: int
    numero_compte: str
    valeur_totale: Decimal
    rendement_total: Decimal
    pourcentage_rendement: float

    model_config = ConfigDict(from_attributes=True)


class DashboardOverviewResponse(BaseModel):
    """
    Vue d'ensemble du portefeuille client
    Source: vw_Dashboard_Overview
    """
    valeur_totale: Decimal
    rendement_total: Decimal
    pourcentage_rendement: float
    nombre_souscriptions_actives: int
    total_investi: Decimal
    devise: str
    comptes: List[CompteOverview]

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# DERNIÈRES TRANSACTIONS
# ============================================================================

class TransactionRecente(BaseModel):
    """
    Transaction récente pour le dashboard
    Source: vw_Dashboard_DernieresTransactions
    """
    transaction_id: int
    type_transaction: str
    description: Optional[str]
    montant: Decimal
    devise: str
    date_creation: datetime
    date_execution: Optional[datetime]
    statut: str
    compte_source: Optional[str]  # Numéro de compte
    compte_destination: Optional[str]  # Numéro de compte

    model_config = ConfigDict(from_attributes=True)


class TransactionsRecentesResponse(BaseModel):
    """Liste des transactions récentes"""
    total: int
    transactions: List[TransactionRecente]

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# INVESTISSEMENTS ACTIFS (Aperçu)
# ============================================================================

class InvestissementActif(BaseModel):
    """
    Investissement actif pour le dashboard
    Source: vw_Dashboard_InvestissementsActifs
    """
    souscription_id: int
    compte_id: int
    nom_instrument: str
    code_instrument: str
    montant_investi: Decimal
    valeur_actuelle: Decimal
    taux_souscription: Decimal
    date_maturite: date
    interets_accumules: Decimal
    progression_maturite: float
    statut: str

    model_config = ConfigDict(from_attributes=True)


class InvestissementsActifsResponse(BaseModel):
    """Liste des investissements actifs"""
    total: int
    investissements: List[InvestissementActif]

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# STATISTIQUES MENSUELLES (Graphique)
# ============================================================================

class StatistiqueMensuelle(BaseModel):
    """
    Statistique pour un mois donné
    Source: vw_StatistiquesMensuelles
    """
    mois: str  # Nom du mois (ex: "Janvier")
    date_mois: date  # Premier jour du mois
    valeur_portefeuille: Decimal
    nombre_souscriptions: int

    model_config = ConfigDict(from_attributes=True)


class StatistiquesMensuellesResponse(BaseModel):
    """Statistiques mensuelles pour le graphique"""
    periodes: List[StatistiqueMensuelle]

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# DASHBOARD COMPLET
# ============================================================================

class DashboardComplet(BaseModel):
    """
    Dashboard complet avec toutes les sections
    """
    overview: DashboardOverviewResponse
    transactions_recentes: TransactionsRecentesResponse
    investissements_actifs: InvestissementsActifsResponse
    statistiques_mensuelles: StatistiquesMensuellesResponse

    model_config = ConfigDict(from_attributes=True)
