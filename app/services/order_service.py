from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models.models import (
    Account,
    AccountRole,
    AccountingEntry,
    InvestmentOrder,
    Instrument,
    OrderWorkflowStep,
    Subscription,
    Transaction,
)
from app.services.portfolio_service import audit, require_account_access


ORDER_STEPS = (
    ("CONFORMITE", "CONFORMITE"),
    ("BACK_OFFICE", "BACK_OFFICE"),
    ("CHECKER", "SUPERVISEUR"),
)
OPEN_ORDER_STATUSES = {"SUBMITTED", "COMPLIANCE_REVIEW", "BACK_OFFICE_REVIEW", "READY_FOR_CHECKER"}


class InvestmentOrderService:
    @staticmethod
    def create(db: Session, client_id: int, account_id: int, instrument_id: int, amount: Decimal, units: Decimal | None = None, client_comment: str | None = None) -> InvestmentOrder:
        account = require_account_access(db, account_id, client_id, operation=True)
        instrument = db.scalar(select(Instrument).where(Instrument.id == instrument_id).with_for_update())
        if not instrument or instrument.status != "DISPONIBLE":
            raise ValueError("Instrument indisponible")
        if account.currency != instrument.currency:
            raise ValueError("La devise du compte et de l'instrument doit être identique")
        if amount < instrument.minimum_amount:
            raise ValueError(f"Le montant minimum est {instrument.minimum_amount} {instrument.currency}")
        if account.available_balance < amount:
            raise ValueError("Solde disponible insuffisant pour l'ordre")
        calculated_units = units or (amount / instrument.nominal_value)
        if calculated_units <= 0:
            raise ValueError("Le nombre d'unités doit être positif")

        # L'argent n'est pas débité à la soumission : il est seulement réservé
        # via available_balance. Le débit du solde comptable intervient à
        # l'exécution finale après validation des trois étapes.
        account.available_balance -= amount
        order = InvestmentOrder(
            client_id=client_id,
            account_id=account_id,
            instrument_id=instrument_id,
            amount=amount,
            units=calculated_units,
            currency=account.currency,
            status="SUBMITTED",
            client_comment=client_comment,
            submitted_by_client_id=client_id,
        )
        db.add(order)
        db.flush()
        db.add_all([OrderWorkflowStep(order_id=order.id, step_code=code, actor_profile=profile) for code, profile in ORDER_STEPS])
        audit(db, client_id, "INVESTMENT_ORDER_SUBMITTED", "investment_order", order.id, {"instrument": instrument.code, "amount": str(amount)})
        db.commit()
        return InvestmentOrderService.get(db, order.id, client_id)

    @staticmethod
    def get(db: Session, order_id: int, client_id: int) -> InvestmentOrder:
        order = db.scalar(
            select(InvestmentOrder)
            .where(InvestmentOrder.id == order_id)
            .options(joinedload(InvestmentOrder.instrument), joinedload(InvestmentOrder.account))
        )
        if not order:
            raise ValueError("Ordre introuvable")
        require_account_access(db, order.account_id, client_id)
        return order

    @staticmethod
    def list_for_client(db: Session, client_id: int) -> list[InvestmentOrder]:
        account_ids = select(AccountRole.account_id).where(AccountRole.client_id == client_id, AccountRole.is_active.is_(True))
        # Un ordre est visible au titulaire/mandataire du compte partagé,
        # pas uniquement à la personne qui l'a soumis.
        query = (
            select(InvestmentOrder)
            .where(InvestmentOrder.account_id.in_(account_ids))
            .options(joinedload(InvestmentOrder.instrument), joinedload(InvestmentOrder.account), joinedload(InvestmentOrder.steps))
            .order_by(InvestmentOrder.created_at.desc())
        )
        return list(db.scalars(query).unique())

    @staticmethod
    def review_step(db: Session, order_id: int, checker_id: int, step_code: str, decision: str, notes: str | None = None) -> InvestmentOrder:
        if step_code not in {code for code, _ in ORDER_STEPS}:
            raise ValueError("Étape de workflow inconnue")
        order = db.scalar(select(InvestmentOrder).where(InvestmentOrder.id == order_id).with_for_update())
        if not order:
            raise ValueError("Ordre introuvable")
        require_account_access(db, order.account_id, checker_id, operation=True)
        if order.submitted_by_client_id == checker_id:
            raise PermissionError("Le maker ne peut pas valider son propre ordre")
        if order.status not in OPEN_ORDER_STATUSES:
            raise ValueError("L'ordre n'est plus ouvert")
        step = db.scalar(select(OrderWorkflowStep).where(OrderWorkflowStep.order_id == order_id, OrderWorkflowStep.step_code == step_code).with_for_update())
        if not step or step.status != "PENDING":
            raise ValueError("Cette étape n'est pas en attente")
        if decision == "REJECT":
            return InvestmentOrderService._reject(db, order, step, checker_id, notes or "Ordre rejeté à l'étape de contrôle")
        if decision != "APPROVE":
            raise ValueError("Décision attendue : APPROVE ou REJECT")

        # Le contrôle suit l'ordre des étapes ; une étape ne peut pas être
        # approuvée avant la précédente.
        index = [code for code, _ in ORDER_STEPS].index(step_code)
        if index and db.scalar(select(OrderWorkflowStep.status).where(OrderWorkflowStep.order_id == order_id, OrderWorkflowStep.step_code == ORDER_STEPS[index - 1][0])) != "APPROVED":
            raise ValueError("L'étape précédente doit être approuvée")
        step.status = "APPROVED"
        step.notes = notes
        step.completed_at = datetime.now(timezone.utc)
        approved = db.scalars(select(OrderWorkflowStep).where(OrderWorkflowStep.order_id == order_id)).all()
        if all(item.status == "APPROVED" for item in approved):
            InvestmentOrderService._execute(db, order, checker_id)
        elif step_code == "CONFORMITE":
            order.status = "BACK_OFFICE_REVIEW"
        elif step_code == "BACK_OFFICE":
            order.status = "READY_FOR_CHECKER"
        audit(db, checker_id, "INVESTMENT_ORDER_STEP_APPROVED", "investment_order", order.id, {"step": step_code})
        db.commit()
        return InvestmentOrderService.get(db, order.id, checker_id)

    @staticmethod
    def _reject(db: Session, order: InvestmentOrder, step: OrderWorkflowStep, checker_id: int, reason: str) -> InvestmentOrder:
        step.status = "REJECTED"
        step.notes = reason
        step.completed_at = datetime.now(timezone.utc)
        order.status = "REJECTED"
        order.checked_by_client_id = checker_id
        order.rejection_reason = reason
        account = db.scalar(select(Account).where(Account.id == order.account_id).with_for_update())
        account.available_balance += order.amount
        audit(db, checker_id, "INVESTMENT_ORDER_REJECTED", "investment_order", order.id, {"step": step.step_code, "reason": reason})
        db.commit()
        return InvestmentOrderService.get(db, order.id, checker_id)

    @staticmethod
    def _execute(db: Session, order: InvestmentOrder, checker_id: int) -> None:
        account = db.scalar(select(Account).where(Account.id == order.account_id).with_for_update())
        instrument = db.scalar(select(Instrument).where(Instrument.id == order.instrument_id).with_for_update())
        if not account or not instrument or account.available_balance < 0:
            raise ValueError("Compte ou instrument indisponible")
        account.balance -= order.amount
        subscription = Subscription(
            account_id=order.account_id,
            instrument_id=order.instrument_id,
            invested_amount=order.amount,
            units=order.units or (order.amount / instrument.nominal_value),
            effective_maturity_date=instrument.maturity_date,
            subscription_yield=instrument.annual_yield,
            current_value=order.amount,
            accrued_interest=0,
            status="ACTIVE",
        )
        db.add(subscription)
        db.flush()
        transaction = Transaction(
            transaction_type="SOUSCRIPTION",
            source_account_id=order.account_id,
            amount=order.amount,
            currency=order.currency,
            description=f"Souscription {instrument.code} - ordre {order.id}",
            status="EXECUTED",
            executed_at=datetime.now(timezone.utc),
            subscription_id=subscription.id,
            created_by_client_id=order.submitted_by_client_id,
            approved_by_client_id=checker_id,
        )
        db.add(transaction)
        db.flush()
        db.add_all([
            AccountingEntry(transaction_id=transaction.id, account_code=f"CLIENT_{account.id}", direction="CREDIT", amount=order.amount, currency=order.currency),
            AccountingEntry(transaction_id=transaction.id, account_code=f"INVESTMENT_{instrument.code}", direction="DEBIT", amount=order.amount, currency=order.currency),
        ])
        order.status = "EXECUTED"
        order.checked_by_client_id = checker_id
        order.executed_transaction_id = transaction.id
        order.executed_subscription_id = subscription.id
        audit(db, checker_id, "INVESTMENT_ORDER_EXECUTED", "investment_order", order.id, {"transaction_id": transaction.id, "subscription_id": subscription.id})

    @staticmethod
    def cancel(db: Session, order_id: int, client_id: int) -> InvestmentOrder:
        order = db.scalar(select(InvestmentOrder).where(InvestmentOrder.id == order_id).with_for_update())
        if not order:
            raise ValueError("Ordre introuvable")
        if order.submitted_by_client_id != client_id:
            raise PermissionError("Seul le client à l'origine de l'ordre peut l'annuler")
        if order.status not in OPEN_ORDER_STATUSES:
            raise ValueError("L'ordre ne peut plus être annulé")
        from app.models.models import Account

        account = db.scalar(select(Account).where(Account.id == order.account_id).with_for_update())
        account.available_balance += order.amount
        order.status = "CANCELLED"
        audit(db, client_id, "INVESTMENT_ORDER_CANCELLED", "investment_order", order.id)
        db.commit()
        return InvestmentOrderService.get(db, order.id, client_id)
