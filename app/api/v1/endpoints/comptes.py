from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.core.dependencies import get_current_active_client
from app.db.database import get_db
from app.models.models import Account, AccountRole, Client
from app.schemas.api import AccountCreate
from app.services.portfolio_service import account_out, create_account, require_account_access

router = APIRouter()


@router.post("/", status_code=201)
def open_account(payload: AccountCreate, client: Client = Depends(get_current_active_client), db: Session = Depends(get_db)):
    try:
        account = create_account(db, client.id, payload.account_type, payload.currency)
        return {"success": True, "message": "Compte créé", "account": account_out(account, "TITULAIRE_PRINCIPAL")}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/mes-comptes")
@router.get("/")
def list_accounts(client: Client = Depends(get_current_active_client), db: Session = Depends(get_db)):
    roles = db.scalars(select(AccountRole).where(AccountRole.client_id == client.id, AccountRole.is_active.is_(True)).options(joinedload(AccountRole.account))).all()
    accounts = [account_out(item.account, item.role) for item in roles]
    return {"total": len(accounts), "comptes": accounts, "accounts": accounts}


@router.get("/{account_id}")
def get_account(account_id: int, client: Client = Depends(get_current_active_client), db: Session = Depends(get_db)):
    try:
        account = require_account_access(db, account_id, client.id)
        return account_out(account, db.scalar(select(AccountRole.role).where(AccountRole.account_id == account_id, AccountRole.client_id == client.id, AccountRole.is_active.is_(True))))
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
