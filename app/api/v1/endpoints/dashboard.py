"""
Endpoints Dashboard - Vue d'ensemble du portefeuille client
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.core.dependencies import get_current_active_client
from app.models.models import Client
from app.schemas.dashboard import (
    DashboardOverviewResponse,
    TransactionsRecentesResponse,
    InvestissementsActifsResponse,
    StatistiquesMensuellesResponse,
    DashboardComplet
)
from app.services.dashboard_service import DashboardService
from typing import Optional

router = APIRouter()


@router.get("/overview", response_model=DashboardOverviewResponse)
def get_dashboard_overview(
    compte_id: Optional[int] = Query(None, description="ID du compte spécifique (optionnel)"),
    current_client: Client = Depends(get_current_active_client),
    db: Session = Depends(get_db)
):
    """
    Vue d'ensemble du portefeuille

    Retourne la valeur totale, le rendement, le nombre de souscriptions actives
    pour tous les comptes du client ou un compte spécifique.

    **Corresponds à l'écran Dashboard principal avec:**
    - Valeur totale: 50 000,00 $US
    - Rendement total: +2 600,00 $US (5.2%)
    - Souscriptions actives: 2
    """
    try:
        overview = DashboardService.get_overview(
            db=db,
            client_id=current_client.ClientID,
            compte_id=compte_id
        )
        return DashboardOverviewResponse(**overview)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la récupération du dashboard: {str(e)}"
        )


@router.get("/transactions/recentes", response_model=TransactionsRecentesResponse)
def get_transactions_recentes(
    compte_id: Optional[int] = Query(None, description="ID du compte spécifique (optionnel)"),
    limit: int = Query(3, ge=1, le=10, description="Nombre de transactions à retourner"),
    current_client: Client = Depends(get_current_active_client),
    db: Session = Depends(get_db)
):
    """
    Dernières transactions

    Retourne les N dernières transactions du client.

    **Corresponds à la section "Dernières transactions" du dashboard:**
    - Virement entrant salaire: 5000,00 $US
    - Souscription OBL-BRH-2025-001: -20000,00 $US
    - Retrait en ligne: -1000,00 $US (En Attente Validation)
    """
    try:
        transactions = DashboardService.get_transactions_recentes(
            db=db,
            client_id=current_client.ClientID,
            compte_id=compte_id,
            limit=limit
        )

        return TransactionsRecentesResponse(
            total=len(transactions),
            transactions=transactions
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la récupération des transactions: {str(e)}"
        )


@router.get("/investissements", response_model=InvestissementsActifsResponse)
def get_investissements_actifs(
    compte_id: Optional[int] = Query(None, description="ID du compte spécifique (optionnel)"),
    current_client: Client = Depends(get_current_active_client),
    db: Session = Depends(get_db)
):
    """
    Investissements actifs (aperçu)

    Retourne la liste des investissements actifs avec progression vers maturité.

    **Corresponds à la section "Investissements Actifs" du dashboard:**
    - Obligation BRH 5.5% 2025
    - Montant: 20 000,00 $US
    - Maturité: 14/06/2025
    - Progression: 75%
    """
    try:
        investissements = DashboardService.get_investissements_actifs(
            db=db,
            client_id=current_client.ClientID,
            compte_id=compte_id
        )

        return InvestissementsActifsResponse(
            total=len(investissements),
            investissements=investissements
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la récupération des investissements: {str(e)}"
        )


@router.get("/statistiques/mensuelles", response_model=StatistiquesMensuellesResponse)
def get_statistiques_mensuelles(
    compte_id: Optional[int] = Query(None, description="ID du compte spécifique (optionnel)"),
    mois: int = Query(12, ge=1, le=24, description="Nombre de mois"),
    current_client: Client = Depends(get_current_active_client),
    db: Session = Depends(get_db)
):
    """
    Statistiques mensuelles pour le graphique

    Retourne la valeur du portefeuille pour les N derniers mois.

    **Corresponds au graphique à barres du dashboard:**
    - Janvier: 45 000,00 $US
    - Février: 45 300,00 $US
    - Mars: 46 200,00 $US
    - Avril: 47 800,00 $US
    - Mai: 49 100,00 $US
    - Juin: 50 500,00 $US
    """
    try:
        statistiques = DashboardService.get_statistiques_mensuelles(
            db=db,
            client_id=current_client.ClientID,
            compte_id=compte_id,
            mois=mois
        )

        return StatistiquesMensuellesResponse(periodes=statistiques)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la récupération des statistiques: {str(e)}"
        )


@router.get("/complet", response_model=DashboardComplet)
def get_dashboard_complet(
    compte_id: Optional[int] = Query(None, description="ID du compte spécifique (optionnel)"),
    current_client: Client = Depends(get_current_active_client),
    db: Session = Depends(get_db)
):
    """
    Dashboard complet - Toutes les sections en un seul appel

    Optimisé pour charger tout le dashboard d'un coup.
    Retourne:
    - Vue d'ensemble (overview)
    - Dernières transactions (3)
    - Investissements actifs
    - Statistiques mensuelles (12 mois)
    """
    try:
        dashboard = DashboardService.get_dashboard_complet(
            db=db,
            client_id=current_client.ClientID,
            compte_id=compte_id
        )

        return DashboardComplet(**dashboard)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la récupération du dashboard complet: {str(e)}"
        )
