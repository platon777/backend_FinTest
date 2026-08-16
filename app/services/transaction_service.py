from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.models.models import Account, AccountRole, AccountingEntry, Subscription, Transaction
from app.services.portfolio_service import audit, get_account_for_client, require_account_access


class TransactionService:
    @staticmethod
    def create(db: Session, client_id: int, transaction_type: str, amount: Decimal, currency: str, source_account_id: int | None = None, destination_account_id: int | None = None, description: str | None = None) -> Transaction:
        if transaction_type == "DEPOT":
            if not destination_account_id:
                raise ValueError("Un compte destination est obligatoire")
            require_account_access(db, destination_account_id, client_id, operation=True)
        elif transaction_type == "RETRAIT":
            if not source_account_id:
                raise ValueError("Un compte source est obligatoire")
            require_account_access(db, source_account_id, client_id, operation=True)
        elif transaction_type == "TRANSFERT":
            if not source_account_id or not destination_account_id or source_account_id == destination_account_id:
                raise ValueError("Les comptes source et destination doivent être distincts")
            require_account_access(db, source_account_id, client_id, operation=True)
            require_account_access(db, destination_account_id, client_id, operation=False)
        else:
            raise ValueError("Type de transaction non supporté")

        transaction = Transaction(
            transaction_type=transaction_type,
            source_account_id=source_account_id,
            destination_account_id=destination_account_id,
            amount=amount,
            currency=currency.upper(),
            description=description,
            status="PENDING_APPROVAL",
            created_by_client_id=client_id,
        )
        db.add(transaction)
        db.flush()
        audit(db, client_id, "TRANSACTION_CREATED", "transaction", transaction.id, {"type": transaction_type, "amount": str(amount)})
        db.commit()
        db.refresh(transaction)
        return transaction

    @staticmethod
    def approve(db: Session, transaction_id: int, checker_id: int) -> Transaction:
        transaction = db.scalar(select(Transaction).where(Transaction.id == transaction_id).with_for_update())
        if not transaction:
            raise ValueError("Transaction introuvable")
        if transaction.status != "PENDING_APPROVAL":
            raise ValueError("La transaction n'est pas en attente de validation")
        if transaction.created_by_client_id == checker_id:
            raise PermissionError("Le maker ne peut pas être son propre checker")
        relevant_account = transaction.source_account_id or transaction.destination_account_id
        if not relevant_account:
            raise ValueError("Transaction sans compte")
        require_account_access(db, relevant_account, checker_id, operation=True)
        try:
            transaction.approved_by_client_id = checker_id
            transaction.status = "APPROVED"
            db.flush()
            TransactionService.execute(db, transaction, checker_id)
            return transaction
        except Exception:
            db.rollback()
            raise

    @staticmethod
    def reject(db: Session, transaction_id: int, checker_id: int, reason: str) -> Transaction:
        transaction = db.scalar(select(Transaction).where(Transaction.id == transaction_id).with_for_update())
        if not transaction:
            raise ValueError("Transaction introuvable")
        if transaction.status != "PENDING_APPROVAL":
            raise ValueError("La transaction n'est pas en attente de validation")
        if transaction.created_by_client_id == checker_id:
            raise PermissionError("Le maker ne peut pas être son propre checker")
        relevant_account = transaction.source_account_id or transaction.destination_account_id
        if not relevant_account:
            raise ValueError("Transaction sans compte")
        require_account_access(db, relevant_account, checker_id, operation=True)
        transaction.approved_by_client_id = checker_id
        transaction.rejection_reason = reason
        transaction.status = "REJECTED"
        audit(db, checker_id, "TRANSACTION_REJECTED", "transaction", transaction.id, {"reason": reason})
        db.commit()
        db.refresh(transaction)
        return transaction

    @staticmethod
    def execute(db: Session, transaction: Transaction, actor_id: int | None = None) -> Transaction:
        if transaction.status not in {"APPROVED", "PENDING_APPROVAL"}:
            raise ValueError("La transaction ne peut pas être exécutée")

        source = get_account_for_client(db, transaction.source_account_id, actor_id, for_update=True) if transaction.source_account_id and actor_id else db.scalar(select(Account).where(Account.id == transaction.source_account_id).with_for_update()) if transaction.source_account_id else None
        destination = get_account_for_client(db, transaction.destination_account_id, actor_id, for_update=True) if transaction.destination_account_id and actor_id else db.scalar(select(Account).where(Account.id == transaction.destination_account_id).with_for_update()) if transaction.destination_account_id else None
        if source and source.currency != transaction.currency:
            raise ValueError("La devise du compte source ne correspond pas à la transaction")
        if destination and destination.currency != transaction.currency:
            raise ValueError("La devise du compte destination ne correspond pas à la transaction")
        amount = Decimal(transaction.amount)

        if transaction.transaction_type in {"RETRAIT", "TRANSFERT"}:
            if not source or source.available_balance < amount:
                raise ValueError("Solde disponible insuffisant")
            source.balance -= amount
            source.available_balance -= amount
        if transaction.transaction_type in {"DEPOT", "TRANSFERT", "REMBOURSEMENT_MATURITE"}:
            if not destination:
                raise ValueError("Compte destination introuvable")
            destination.balance += amount
            destination.available_balance += amount

        transaction.status = "EXECUTED"
        transaction.executed_at = datetime.now(timezone.utc)
        if transaction.transaction_type == "DEPOT":
            entries = [("BANK_SETTLEMENT", "DEBIT"), (f"CLIENT_{destination.id}", "CREDIT")]
        elif transaction.transaction_type == "RETRAIT":
            entries = [(f"CLIENT_{source.id}", "DEBIT"), ("BANK_SETTLEMENT", "CREDIT")]
        elif transaction.transaction_type == "REMBOURSEMENT_MATURITE":
            entries = [("INVESTMENT_POSITION", "CREDIT"), (f"CLIENT_{destination.id}", "DEBIT")]
        else:
            entries = [(f"CLIENT_{source.id}", "DEBIT"), (f"CLIENT_{destination.id}", "CREDIT")]
        for account_code, direction in entries:
            db.add(AccountingEntry(transaction_id=transaction.id, account_code=account_code, direction=direction, amount=amount, currency=transaction.currency))
        audit(db, actor_id or transaction.created_by_client_id, "TRANSACTION_EXECUTED", "transaction", transaction.id, {"status": transaction.status})
        if transaction.transaction_type == "REMBOURSEMENT_MATURITE" and transaction.subscription_id:
            subscription = db.get(Subscription, transaction.subscription_id)
            if subscription:
                subscription.status = "MATURE"
        db.commit()
        db.refresh(transaction)
        return transaction

    @staticmethod
    def list_for_client(db: Session, client_id: int, limit: int = 100) -> list[Transaction]:
        account_ids = select(Account.id).join(Account.roles).where(AccountRole.client_id == client_id, AccountRole.is_active.is_(True))
        return list(db.scalars(select(Transaction).where(or_(Transaction.source_account_id.in_(account_ids), Transaction.destination_account_id.in_(account_ids))).order_by(Transaction.created_at.desc()).limit(limit)))
