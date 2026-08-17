from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.models.models import Account, AccountRole, AccountingEntry, InterestPayment, Subscription, Transaction
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
        if transaction.transaction_type == "CONTREPASSATION" and transaction.reversal_of_transaction_id:
            original = db.get(Transaction, transaction.reversal_of_transaction_id)
            relevant_account = (original.source_account_id or original.destination_account_id) if original else None
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
        if transaction.transaction_type == "CONTREPASSATION":
            return TransactionService._execute_reversal(db, transaction, actor_id)
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
        if transaction.transaction_type in {"DEPOT", "TRANSFERT", "REMBOURSEMENT_MATURITE", "PAIEMENT_INTERET"}:
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
        elif transaction.transaction_type == "PAIEMENT_INTERET":
            entries = [("INTEREST_EXPENSE", "DEBIT"), (f"CLIENT_{destination.id}", "CREDIT")]
        else:
            entries = [(f"CLIENT_{source.id}", "DEBIT"), (f"CLIENT_{destination.id}", "CREDIT")]
        for account_code, direction in entries:
            db.add(AccountingEntry(transaction_id=transaction.id, account_code=account_code, direction=direction, amount=amount, currency=transaction.currency))
        audit(db, actor_id or transaction.created_by_client_id, "TRANSACTION_EXECUTED", "transaction", transaction.id, {"status": transaction.status})
        if transaction.transaction_type == "REMBOURSEMENT_MATURITE" and transaction.subscription_id:
            subscription = db.get(Subscription, transaction.subscription_id)
            if subscription:
                subscription.status = "MATURE"
        if transaction.transaction_type == "PAIEMENT_INTERET":
            payment = db.scalar(select(InterestPayment).where(InterestPayment.transaction_id == transaction.id).with_for_update())
            if payment:
                payment.status = "PAYE"
        db.commit()
        db.refresh(transaction)
        return transaction

    @staticmethod
    def reverse(db: Session, transaction_id: int, actor_id: int, reason: str) -> Transaction:
        original = db.scalar(select(Transaction).where(Transaction.id == transaction_id).with_for_update())
        if not original:
            raise ValueError("Transaction introuvable")
        if original.status != "EXECUTED":
            raise ValueError("Seule une transaction executee peut etre contre-passee")
        if original.created_by_client_id == actor_id:
            raise PermissionError("Le maker de l'operation ne peut pas demander sa contrepassation")
        if db.scalar(select(Transaction.id).where(Transaction.reversal_of_transaction_id == original.id, Transaction.status.in_(["PENDING_APPROVAL", "APPROVED", "EXECUTED"]))):
            raise ValueError("Une contrepassation existe deja pour cette transaction")
        account_id = original.source_account_id or original.destination_account_id
        if not account_id:
            raise ValueError("Transaction sans compte rattache")
        require_account_access(db, account_id, actor_id, operation=True)
        reversal = Transaction(
            transaction_type="CONTREPASSATION",
            amount=original.amount,
            currency=original.currency,
            source_account_id=original.source_account_id,
            destination_account_id=original.destination_account_id,
            description=f"Contrepassation de la transaction {original.id}",
            status="PENDING_APPROVAL",
            reversal_of_transaction_id=original.id,
            reversal_reason=reason,
            created_by_client_id=actor_id,
        )
        db.add(reversal)
        db.flush()
        audit(db, actor_id, "TRANSACTION_REVERSAL_REQUESTED", "transaction", reversal.id, {"original_id": original.id, "reason": reason})
        db.commit()
        db.refresh(reversal)
        return reversal

    @staticmethod
    def _execute_reversal(db: Session, reversal: Transaction, actor_id: int | None) -> Transaction:
        if reversal.status not in {"APPROVED", "PENDING_APPROVAL"}:
            raise ValueError("La contrepassation ne peut pas etre executee")
        original = db.scalar(select(Transaction).where(Transaction.id == reversal.reversal_of_transaction_id).with_for_update())
        if not original or original.status != "EXECUTED":
            raise ValueError("La transaction d'origine n'est pas executee")
        source = db.scalar(select(Account).where(Account.id == original.source_account_id).with_for_update()) if original.source_account_id else None
        destination = db.scalar(select(Account).where(Account.id == original.destination_account_id).with_for_update()) if original.destination_account_id else None
        amount = Decimal(original.amount)
        if source:
            source.balance += amount
            source.available_balance += amount
        if destination:
            if destination.balance < amount or destination.available_balance < amount:
                raise ValueError("Le solde ne permet pas la contrepassation")
            destination.balance -= amount
            destination.available_balance -= amount
        reversal.status = "EXECUTED"
        reversal.approved_by_client_id = actor_id
        reversal.executed_at = datetime.now(timezone.utc)
        reversal.version = 2
        for entry in db.scalars(select(AccountingEntry).where(AccountingEntry.transaction_id == original.id)).all():
            db.add(AccountingEntry(
                transaction_id=reversal.id,
                account_code=entry.account_code,
                direction="CREDIT" if entry.direction == "DEBIT" else "DEBIT",
                amount=entry.amount,
                currency=entry.currency,
                posting_version=2,
                is_reversal=True,
            ))
        original.version += 1
        original.reversed_at = datetime.now(timezone.utc)
        if original.subscription_id and original.transaction_type == "SOUSCRIPTION":
            subscription = db.get(Subscription, original.subscription_id)
            if subscription:
                subscription.status = "REVERSED"
        audit(db, actor_id or reversal.created_by_client_id, "TRANSACTION_REVERSED", "transaction", original.id, {"reversal_id": reversal.id, "reason": reversal.reversal_reason})
        db.commit()
        db.refresh(reversal)
        return reversal

    @staticmethod
    def list_for_client(db: Session, client_id: int, limit: int = 100) -> list[Transaction]:
        account_ids = select(Account.id).join(Account.roles).where(AccountRole.client_id == client_id, AccountRole.is_active.is_(True))
        return list(db.scalars(select(Transaction).where(or_(Transaction.source_account_id.in_(account_ids), Transaction.destination_account_id.in_(account_ids))).order_by(Transaction.created_at.desc()).limit(limit)))
