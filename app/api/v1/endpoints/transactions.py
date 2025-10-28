"""
Endpoints pour la gestion des Transactions
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.core.dependencies import get_current_active_client
from app.models.models import Client
from app.schemas.transactions import *
from app.services.transactions_service import TransactionsService
from app.services.comptes_service import ComptesService

router = APIRouter()


@router.post("/depot", response_model=TransactionCreateResponse, status_code=status.HTTP_201_CREATED)
def creer_depot(
    data: TransactionDepot,
    current_client: Client = Depends(get_current_active_client),
    db: Session = Depends(get_db)
):
    """Créer un dépôt sur un compte"""
    try:
        # Vérifier l'accès au compte
        if not ComptesService.verifier_acces_compte(db, data.CompteDestination, current_client.ClientID):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Accès refusé à ce compte")

        transaction = TransactionsService.creer_transaction(
            db=db,
            type_transaction='DEPOT',
            montant=data.Montant,
            devise=data.Devise,
            compte_destination=data.CompteDestination,
            description=data.Description
        )

        # Exécuter immédiatement
        transaction = TransactionsService.executer_transaction(db, transaction.TransactionID)

        return TransactionCreateResponse(
            success=True,
            message="Dépôt créé avec succès",
            transaction=TransactionResponse.from_orm(transaction)
        )

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/retrait", response_model=TransactionCreateResponse, status_code=status.HTTP_201_CREATED)
def creer_retrait(
    data: TransactionRetrait,
    current_client: Client = Depends(get_current_active_client),
    db: Session = Depends(get_db)
):
    """Créer un retrait d'un compte"""
    try:
        # Vérifier l'accès au compte
        if not ComptesService.verifier_role_compte(
            db, data.CompteSource, current_client.ClientID,
            ['TITULAIRE_PRINCIPAL', 'TITULAIRE_SECONDAIRE', 'MANDATAIRE']
        ):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Accès refusé")

        transaction = TransactionsService.creer_transaction(
            db=db,
            type_transaction='RETRAIT',
            montant=data.Montant,
            devise=data.Devise,
            compte_source=data.CompteSource,
            description=data.Description
        )

        # Exécuter immédiatement
        transaction = TransactionsService.executer_transaction(db, transaction.TransactionID)

        return TransactionCreateResponse(
            success=True,
            message="Retrait créé avec succès",
            transaction=TransactionResponse.from_orm(transaction)
        )

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/transfert", response_model=TransactionCreateResponse, status_code=status.HTTP_201_CREATED)
def creer_transfert(
    data: TransactionTransfert,
    current_client: Client = Depends(get_current_active_client),
    db: Session = Depends(get_db)
):
    """Créer un transfert entre deux comptes"""
    try:
        # Vérifier l'accès au compte source
        if not ComptesService.verifier_role_compte(
            db, data.CompteSource, current_client.ClientID,
            ['TITULAIRE_PRINCIPAL', 'TITULAIRE_SECONDAIRE', 'MANDATAIRE']
        ):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Accès refusé au compte source")

        transaction = TransactionsService.creer_transaction(
            db=db,
            type_transaction='TRANSFERT',
            montant=data.Montant,
            devise=data.Devise,
            compte_source=data.CompteSource,
            compte_destination=data.CompteDestination,
            description=data.Description
        )

        # Exécuter immédiatement
        transaction = TransactionsService.executer_transaction(db, transaction.TransactionID)

        return TransactionCreateResponse(
            success=True,
            message="Transfert créé avec succès",
            transaction=TransactionResponse.from_orm(transaction)
        )

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/mes-transactions", response_model=TransactionsListResponse)
def get_mes_transactions(
    limit: int = Query(default=100, le=500),
    current_client: Client = Depends(get_current_active_client),
    db: Session = Depends(get_db)
):
    """Récupérer toutes les transactions du client"""
    try:
        transactions = TransactionsService.get_transactions_client(db, current_client.ClientID, limit)

        # Enrichir avec les numéros de compte
        transactions_detail = []
        for t in transactions:
            detail = TransactionDetail.from_orm(t)

            if t.CompteSource:
                compte_source = ComptesService.get_compte_by_id(db, t.CompteSource)
                if compte_source:
                    detail.compte_source_numero = compte_source.NumeroCompte

            if t.CompteDestination:
                compte_dest = ComptesService.get_compte_by_id(db, t.CompteDestination)
                if compte_dest:
                    detail.compte_destination_numero = compte_dest.NumeroCompte

            transactions_detail.append(detail)

        return TransactionsListResponse(
            total=len(transactions_detail),
            transactions=transactions_detail
        )

    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/compte/{compte_id}", response_model=HistoriqueTransactionsResponse)
def get_transactions_compte(
    compte_id: int,
    limit: int = Query(default=100, le=500),
    current_client: Client = Depends(get_current_active_client),
    db: Session = Depends(get_db)
):
    """Récupérer l'historique des transactions d'un compte"""
    try:
        # Vérifier l'accès au compte
        if not ComptesService.verifier_acces_compte(db, compte_id, current_client.ClientID):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Accès refusé à ce compte")

        compte = ComptesService.get_compte_by_id(db, compte_id)
        if not compte:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Compte introuvable")

        transactions = TransactionsService.get_transactions_compte(db, compte_id, limit)

        # Enrichir avec les numéros de compte
        transactions_detail = []
        for t in transactions:
            detail = TransactionDetail.from_orm(t)

            if t.CompteSource:
                compte_source = ComptesService.get_compte_by_id(db, t.CompteSource)
                if compte_source:
                    detail.compte_source_numero = compte_source.NumeroCompte

            if t.CompteDestination:
                compte_dest = ComptesService.get_compte_by_id(db, t.CompteDestination)
                if compte_dest:
                    detail.compte_destination_numero = compte_dest.NumeroCompte

            transactions_detail.append(detail)

        return HistoriqueTransactionsResponse(
            compte_id=compte_id,
            compte_numero=compte.NumeroCompte,
            total=len(transactions_detail),
            transactions=transactions_detail
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/{transaction_id}", response_model=TransactionDetail)
def get_transaction(
    transaction_id: int,
    current_client: Client = Depends(get_current_active_client),
    db: Session = Depends(get_db)
):
    """Récupérer les détails d'une transaction"""
    try:
        transaction = TransactionsService.get_transaction_by_id(db, transaction_id)
        if not transaction:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transaction introuvable")

        # Vérifier l'accès (le client doit avoir accès à au moins un des comptes)
        has_access = False
        if transaction.CompteSource:
            has_access = ComptesService.verifier_acces_compte(db, transaction.CompteSource, current_client.ClientID)
        if not has_access and transaction.CompteDestination:
            has_access = ComptesService.verifier_acces_compte(db, transaction.CompteDestination, current_client.ClientID)

        if not has_access:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Accès refusé")

        detail = TransactionDetail.from_orm(transaction)

        if transaction.CompteSource:
            compte_source = ComptesService.get_compte_by_id(db, transaction.CompteSource)
            if compte_source:
                detail.compte_source_numero = compte_source.NumeroCompte

        if transaction.CompteDestination:
            compte_dest = ComptesService.get_compte_by_id(db, transaction.CompteDestination)
            if compte_dest:
                detail.compte_destination_numero = compte_dest.NumeroCompte

        return detail

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
