"""
Endpoints pour la gestion des Souscriptions (Investissements)
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.core.dependencies import get_current_active_client
from app.models.models import Client
from app.schemas.souscriptions import *
from app.services.souscriptions_service import SouscriptionsService
from app.services.transactions_service import TransactionsService

router = APIRouter()


@router.post("/", response_model=SouscriptionCreateResponse, status_code=status.HTTP_201_CREATED)
def creer_souscription(
    data: SouscriptionCreate,
    current_client: Client = Depends(get_current_active_client),
    db: Session = Depends(get_db)
):
    """Créer une nouvelle souscription (investissement)"""
    try:
        souscription = SouscriptionsService.creer_souscription(
            db=db,
            compte_id=data.CompteID,
            instrument_id=data.InstrumentID,
            montant_investi=data.MontantInvesti,
            client_id=current_client.ClientID
        )

        # Créer la transaction correspondante
        transaction = TransactionsService.creer_transaction(
            db=db,
            type_transaction='SOUSCRIPTION',
            montant=data.MontantInvesti,
            devise='HTG',
            compte_source=data.CompteID,
            souscription_id=souscription.SouscriptionID,
            description=f"Souscription {souscription.SouscriptionID}"
        )

        # Exécuter la transaction immédiatement
        TransactionsService.executer_transaction(db, transaction.TransactionID)

        return SouscriptionCreateResponse(
            success=True,
            message="Souscription créée avec succès",
            souscription=SouscriptionResponse.from_orm(souscription),
            transaction_id=transaction.TransactionID
        )

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/mes-souscriptions", response_model=SouscriptionsListResponse)
def get_mes_souscriptions(
    current_client: Client = Depends(get_current_active_client),
    db: Session = Depends(get_db)
):
    """Récupérer toutes les souscriptions du client connecté"""
    try:
        souscriptions = SouscriptionsService.get_souscriptions_client(db, current_client.ClientID)

        # Enrichir avec les détails de l'instrument
        souscriptions_detail = []
        for s in souscriptions:
            detail = SouscriptionDetail.from_orm(s)
            if s.instrument:
                detail.instrument_nom = s.instrument.Nom
                detail.instrument_code = s.instrument.Code
                detail.emetteur = s.instrument.Emetteur
                detail.taux_rendement = s.instrument.TauxRendementAnnuel
            souscriptions_detail.append(detail)

        return SouscriptionsListResponse(
            total=len(souscriptions_detail),
            souscriptions=souscriptions_detail
        )

    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/portefeuille", response_model=PortefeuilleResponse)
def get_mon_portefeuille(
    current_client: Client = Depends(get_current_active_client),
    db: Session = Depends(get_db)
):
    """Récupérer le portefeuille complet du client"""
    try:
        portefeuille = SouscriptionsService.get_portefeuille_client(db, current_client.ClientID)

        # Enrichir les souscriptions
        souscriptions_detail = []
        for s in portefeuille['souscriptions']:
            detail = SouscriptionDetail.from_orm(s)
            if s.instrument:
                detail.instrument_nom = s.instrument.Nom
                detail.instrument_code = s.instrument.Code
                detail.emetteur = s.instrument.Emetteur
                detail.taux_rendement = s.instrument.TauxRendementAnnuel
            souscriptions_detail.append(detail)

        return PortefeuilleResponse(
            total_investi=portefeuille['total_investi'],
            valeur_actuelle_totale=portefeuille['valeur_actuelle_totale'],
            interets_accumules_total=portefeuille['interets_accumules_total'],
            nombre_souscriptions=portefeuille['nombre_souscriptions'],
            souscriptions=souscriptions_detail
        )

    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/{souscription_id}", response_model=SouscriptionDetail)
def get_souscription(
    souscription_id: int,
    current_client: Client = Depends(get_current_active_client),
    db: Session = Depends(get_db)
):
    """Récupérer les détails d'une souscription"""
    try:
        souscription = SouscriptionsService.get_souscription_by_id(db, souscription_id)
        if not souscription:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Souscription introuvable")

        # Vérifier l'accès via le compte
        from app.services.comptes_service import ComptesService
        if not ComptesService.verifier_acces_compte(db, souscription.CompteID, current_client.ClientID):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Accès refusé")

        detail = SouscriptionDetail.from_orm(souscription)
        if souscription.instrument:
            detail.instrument_nom = souscription.instrument.Nom
            detail.instrument_code = souscription.instrument.Code
            detail.emetteur = souscription.instrument.Emetteur
            detail.taux_rendement = souscription.instrument.TauxRendementAnnuel

        return detail

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/{souscription_id}/racheter", response_model=SouscriptionResponse)
def racheter_souscription(
    souscription_id: int,
    current_client: Client = Depends(get_current_active_client),
    db: Session = Depends(get_db)
):
    """Racheter (liquider) une souscription"""
    try:
        souscription = SouscriptionsService.racheter_souscription(
            db=db,
            souscription_id=souscription_id,
            client_id=current_client.ClientID
        )

        return SouscriptionResponse.from_orm(souscription)

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
