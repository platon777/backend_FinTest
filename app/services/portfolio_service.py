import json
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.models import Account, AccountRole, AuditLog, Client


OPERATING_ROLES = {"TITULAIRE_PRINCIPAL", "TITULAIRE_SECONDAIRE", "MANDATAIRE", "ADMINISTRATEUR"}


def get_account_for_client(db: Session, account_id: int, client_id: int, for_update: bool = False) -> Account | None:
    query = (
        select(Account)
        .join(AccountRole, AccountRole.account_id == Account.id)
        .where(Account.id == account_id, AccountRole.client_id == client_id, AccountRole.is_active.is_(True))
        .options(selectinload(Account.roles))
    )
    if for_update:
        query = query.with_for_update()
    return db.scalar(query)


def get_role(db: Session, account_id: int, client_id: int) -> str | None:
    return db.scalar(select(AccountRole.role).where(AccountRole.account_id == account_id, AccountRole.client_id == client_id, AccountRole.is_active.is_(True)))


def require_account_access(db: Session, account_id: int, client_id: int, operation: bool = False) -> Account:
    account = get_account_for_client(db, account_id, client_id)
    if not account:
        raise PermissionError("Accès refusé à ce compte")
    if account.status != "ACTIF":
        raise ValueError("Le compte est fermé ou suspendu")
    if operation and get_role(db, account_id, client_id) not in OPERATING_ROLES:
        raise PermissionError("Le rôle ne permet pas cette opération")
    return account


def audit(db: Session, client_id: int | None, action: str, entity_type: str, entity_id: int | str | None, metadata: dict | None = None) -> None:
    db.add(AuditLog(client_id=client_id, action=action, entity_type=entity_type, entity_id=str(entity_id) if entity_id is not None else None, metadata_json=json.dumps(metadata or {}, default=str)))


def account_out(account: Account, role: str | None = None) -> dict:
    return {
        "id": account.id,
        "account_number": account.account_number,
        "account_type": account.account_type,
        "currency": account.currency,
        "balance": account.balance,
        "available_balance": account.available_balance,
        "status": account.status,
        "role": role,
    }


def create_account(db: Session, client_id: int, account_type: str, currency: str) -> Account:
    client = db.get(Client, client_id)
    if not client or client.status != "ACTIF":
        raise ValueError("Client inactif ou introuvable")
    account = Account(account_number=f"{account_type[:3]}-{datetime.now().year}-{client_id:05d}-{len(client.account_roles) + 1:02d}", account_type=account_type, currency=currency.upper(), balance=0, available_balance=0, status="ACTIF")
    account.roles.append(AccountRole(client_id=client_id, role="TITULAIRE_PRINCIPAL", is_active=True))
    db.add(account)
    db.flush()
    audit(db, client_id, "ACCOUNT_CREATED", "account", account.id, {"currency": account.currency, "type": account.account_type})
    db.commit()
    db.refresh(account)
    return account
