from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.api.v1.endpoints.serializers import transaction_dict
from app.core.dependencies import get_current_active_client
from app.db.database import get_db
from app.models.models import AccountRole, Client, Transaction
from app.schemas.api import TransactionCreate, TransactionReject
from app.services.transaction_service import TransactionService

router = APIRouter()


@router.post("/", status_code=status.HTTP_201_CREATED)
def create_transaction(payload: TransactionCreate, client: Client = Depends(get_current_active_client), db: Session = Depends(get_db)):
    try:
        transaction = TransactionService.create(db, client.id, payload.transaction_type, payload.amount, payload.currency, payload.source_account_id, payload.destination_account_id, payload.description)
        return {"success": True, "message": "Transaction créée et placée en attente de validation", "transaction": transaction_dict(transaction, db)}
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/depot", status_code=status.HTTP_201_CREATED)
def create_deposit(payload: TransactionCreate, client: Client = Depends(get_current_active_client), db: Session = Depends(get_db)):
    if payload.transaction_type != "DEPOT":
        raise HTTPException(status_code=422, detail="transaction_type doit être DEPOT")
    return create_transaction(payload, client, db)


@router.post("/retrait", status_code=status.HTTP_201_CREATED)
def create_withdrawal(payload: TransactionCreate, client: Client = Depends(get_current_active_client), db: Session = Depends(get_db)):
    if payload.transaction_type != "RETRAIT":
        raise HTTPException(status_code=422, detail="transaction_type doit être RETRAIT")
    return create_transaction(payload, client, db)


@router.post("/transfert", status_code=status.HTTP_201_CREATED)
def create_transfer(payload: TransactionCreate, client: Client = Depends(get_current_active_client), db: Session = Depends(get_db)):
    if payload.transaction_type != "TRANSFERT":
        raise HTTPException(status_code=422, detail="transaction_type doit être TRANSFERT")
    return create_transaction(payload, client, db)


@router.post("/{transaction_id}/approve")
def approve_transaction(transaction_id: int, client: Client = Depends(get_current_active_client), db: Session = Depends(get_db)):
    try:
        transaction = TransactionService.approve(db, transaction_id, client.id)
        return {"success": True, "message": "Transaction validée et exécutée", "transaction": transaction_dict(transaction, db)}
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/{transaction_id}/reject")
def reject_transaction(transaction_id: int, payload: TransactionReject, client: Client = Depends(get_current_active_client), db: Session = Depends(get_db)):
    try:
        transaction = TransactionService.reject(db, transaction_id, client.id, payload.reason)
        return {"success": True, "message": "Transaction rejetée", "transaction": transaction_dict(transaction, db)}
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/mes-transactions")
def list_transactions(limit: int = Query(default=100, ge=1, le=500), client: Client = Depends(get_current_active_client), db: Session = Depends(get_db)):
    account_ids = select(AccountRole.account_id).where(AccountRole.client_id == client.id, AccountRole.is_active.is_(True))
    transactions = db.scalars(select(Transaction).where(or_(Transaction.source_account_id.in_(account_ids), Transaction.destination_account_id.in_(account_ids))).order_by(Transaction.created_at.desc()).limit(limit)).all()
    result = [transaction_dict(item, db) for item in transactions]
    return {"total": len(result), "transactions": result}


@router.get("/compte/{account_id}")
def list_account_transactions(account_id: int, limit: int = Query(default=100, ge=1, le=500), client: Client = Depends(get_current_active_client), db: Session = Depends(get_db)):
    if not db.scalar(select(AccountRole.id).where(AccountRole.account_id == account_id, AccountRole.client_id == client.id, AccountRole.is_active.is_(True))):
        raise HTTPException(status_code=403, detail="Accès refusé à ce compte")
    transactions = db.scalars(select(Transaction).where(or_(Transaction.source_account_id == account_id, Transaction.destination_account_id == account_id)).order_by(Transaction.created_at.desc()).limit(limit)).all()
    return {"compte_id": account_id, "total": len(transactions), "transactions": [transaction_dict(item, db) for item in transactions]}


@router.get("/{transaction_id}")
def get_transaction(transaction_id: int, client: Client = Depends(get_current_active_client), db: Session = Depends(get_db)):
    transaction = db.get(Transaction, transaction_id)
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction introuvable")
    account_ids = select(AccountRole.account_id).where(AccountRole.client_id == client.id, AccountRole.is_active.is_(True))
    if not ((transaction.source_account_id and transaction.source_account_id in db.scalars(account_ids).all()) or (transaction.destination_account_id and transaction.destination_account_id in db.scalars(account_ids).all())):
        raise HTTPException(status_code=403, detail="Accès refusé")
    return transaction_dict(transaction, db)
