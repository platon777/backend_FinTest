from datetime import date, datetime, timezone
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.core.config import settings
from app.models.models import AccountRole, AccountingEntry, Instrument, Subscription, Transaction
from app.services.portfolio_service import audit, require_account_access


class SubscriptionService:
    @staticmethod
    def generate_maturity_transactions(db: Session, as_of: date, client_id: int | None = None) -> list[Transaction]:
        query = select(Subscription).where(Subscription.status == "ACTIVE", Subscription.effective_maturity_date <= as_of).options(joinedload(Subscription.account), joinedload(Subscription.instrument))
        if client_id is not None:
            query = query.join(AccountRole, AccountRole.account_id == Subscription.account_id).where(AccountRole.client_id == client_id, AccountRole.is_active.is_(True))
        subscriptions = list(db.scalars(query).unique())
        created: list[Transaction] = []
        for subscription in subscriptions:
            existing = db.scalar(select(Transaction.id).where(Transaction.subscription_id == subscription.id, Transaction.transaction_type == "REMBOURSEMENT_MATURITE", Transaction.status.in_(["PENDING_APPROVAL", "APPROVED", "EXECUTED"])))
            if existing:
                continue
            transaction = Transaction(
                transaction_type="REMBOURSEMENT_MATURITE", destination_account_id=subscription.account_id,
                amount=subscription.current_value, currency=subscription.instrument.currency,
                description=f"Remboursement automatique à maturité - {subscription.instrument.code}",
                status="PENDING_APPROVAL", is_automatic=True, subscription_id=subscription.id,
            )
            db.add(transaction)
            subscription.status = "MATURITE_EN_ATTENTE"
            db.flush()
            audit(db, client_id, "MATURITY_TRANSACTION_CREATED", "transaction", transaction.id, {"subscription_id": subscription.id, "amount": str(transaction.amount)})
            created.append(transaction)
        db.commit()
        return created

    @staticmethod
    def create(db: Session, client_id: int, account_id: int, instrument_id: int, invested_amount: Decimal, units: Decimal | None = None) -> Subscription:
        account = require_account_access(db, account_id, client_id, operation=True)
        instrument = db.scalar(select(Instrument).where(Instrument.id == instrument_id).with_for_update())
        if not instrument or instrument.status != "DISPONIBLE":
            raise ValueError("Instrument indisponible")
        if account.currency != instrument.currency:
            raise ValueError("La devise du compte et de l'instrument doit être identique")
        if invested_amount < instrument.minimum_amount:
            raise ValueError(f"Le montant minimum est {instrument.minimum_amount} {instrument.currency}")
        fee_amount = (invested_amount * Decimal(instrument.entry_fee_rate) / Decimal("100")).quantize(Decimal("0.01"))
        total_debit = invested_amount + fee_amount
        if account.available_balance < total_debit:
            raise ValueError("Solde disponible insuffisant pour la souscription")
        calculated_units = units or (invested_amount / instrument.nominal_value)
        if calculated_units <= 0:
            raise ValueError("Le nombre d'unités doit être positif")

        account.balance -= total_debit
        account.available_balance -= total_debit
        subscription = Subscription(
            account_id=account.id,
            instrument_id=instrument.id,
            invested_amount=invested_amount,
            units=calculated_units,
            effective_maturity_date=instrument.maturity_date,
            subscription_yield=instrument.annual_yield,
            current_value=invested_amount,
            accrued_interest=0,
            fee_amount=fee_amount,
            status="ACTIVE",
        )
        db.add(subscription)
        db.flush()
        transaction = Transaction(
            transaction_type="SOUSCRIPTION",
            source_account_id=account.id,
            amount=invested_amount,
            currency=account.currency,
            description=f"Souscription {instrument.code}",
            status="EXECUTED" if settings.PROTOTYPE_AUTO_APPROVE_SUBSCRIPTIONS else "PENDING_APPROVAL",
            executed_at=datetime.now(timezone.utc) if settings.PROTOTYPE_AUTO_APPROVE_SUBSCRIPTIONS else None,
            subscription_id=subscription.id,
            created_by_client_id=client_id,
        )
        db.add(transaction)
        db.flush()
        if settings.PROTOTYPE_AUTO_APPROVE_SUBSCRIPTIONS:
            db.add(AccountingEntry(transaction_id=transaction.id, account_code=f"CLIENT_{account.id}", direction="CREDIT", amount=invested_amount, currency=account.currency))
            db.add(AccountingEntry(transaction_id=transaction.id, account_code=f"INVESTMENT_{instrument.code}", direction="DEBIT", amount=invested_amount, currency=account.currency))
            if fee_amount:
                fee_transaction = Transaction(transaction_type="FRAIS", source_account_id=account.id, amount=fee_amount, currency=account.currency, description=f"Frais d'entrée {instrument.code}", status="EXECUTED", executed_at=datetime.now(timezone.utc), subscription_id=subscription.id, created_by_client_id=client_id)
                db.add(fee_transaction)
                db.flush()
                db.add_all([
                    AccountingEntry(transaction_id=fee_transaction.id, account_code=f"CLIENT_{account.id}", direction="DEBIT", amount=fee_amount, currency=account.currency),
                    AccountingEntry(transaction_id=fee_transaction.id, account_code="FEE_REVENUE", direction="CREDIT", amount=fee_amount, currency=account.currency),
                ])
        audit(db, client_id, "SUBSCRIPTION_CREATED", "subscription", subscription.id, {"instrument": instrument.code, "amount": str(invested_amount)})
        db.commit()
        db.refresh(subscription)
        return subscription

    @staticmethod
    def list_for_client(db: Session, client_id: int) -> list[Subscription]:
        return list(db.scalars(
            select(Subscription)
            .join(Subscription.account)
            .join(AccountRole, AccountRole.account_id == Subscription.account_id)
            .where(AccountRole.client_id == client_id, AccountRole.is_active.is_(True))
            .options(joinedload(Subscription.instrument), joinedload(Subscription.account))
            .order_by(Subscription.subscribed_at.desc())
        ).unique())

    @staticmethod
    def get_for_client(db: Session, subscription_id: int, client_id: int) -> Subscription | None:
        subscription = db.scalar(select(Subscription).where(Subscription.id == subscription_id).options(joinedload(Subscription.instrument), joinedload(Subscription.account)))
        if subscription:
            require_account_access(db, subscription.account_id, client_id)
        return subscription

    @staticmethod
    def redeem(db: Session, subscription_id: int, client_id: int) -> Subscription:
        subscription = SubscriptionService.get_for_client(db, subscription_id, client_id)
        if not subscription:
            raise ValueError("Souscription introuvable")
        if subscription.status != "ACTIVE":
            raise ValueError("La souscription n'est pas active")
        account = require_account_access(db, subscription.account_id, client_id, operation=True)
        amount = Decimal(subscription.current_value)
        account.balance += amount
        account.available_balance += amount
        subscription.status = "RACHETEE"
        transaction = Transaction(transaction_type="RACHAT", destination_account_id=account.id, amount=amount, currency=account.currency, description=f"Rachat de la souscription {subscription.id}", status="EXECUTED", executed_at=datetime.now(timezone.utc), subscription_id=subscription.id, created_by_client_id=client_id)
        db.add(transaction)
        db.flush()
        db.add(AccountingEntry(transaction_id=transaction.id, account_code=f"INVESTMENT_{subscription.instrument.code}", direction="CREDIT", amount=amount, currency=account.currency))
        db.add(AccountingEntry(transaction_id=transaction.id, account_code=f"CLIENT_{account.id}", direction="DEBIT", amount=amount, currency=account.currency))
        audit(db, client_id, "SUBSCRIPTION_REDEEMED", "subscription", subscription.id, {"amount": str(amount)})
        db.commit()
        db.refresh(subscription)
        return subscription
