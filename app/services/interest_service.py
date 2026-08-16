"""Generation et consultation des paiements de coupons."""

from calendar import monthrange
from datetime import date
from decimal import Decimal, ROUND_HALF_UP

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models.models import AccountRole, InterestPayment, Subscription, Transaction
from app.services.portfolio_service import audit, require_account_access


FREQUENCY_MONTHS = {"MENSUEL": 1, "TRIMESTRIEL": 3, "SEMESTRIEL": 6, "ANNUEL": 12}


def _add_months(value: date, months: int) -> date:
    month_index = value.month - 1 + months
    year = value.year + month_index // 12
    month = month_index % 12 + 1
    day = min(value.day, monthrange(year, month)[1])
    return date(year, month, day)


class InterestService:
    @staticmethod
    def generate_due_payments(db: Session, as_of: date, client_id: int | None = None) -> list[InterestPayment]:
        query = select(Subscription).where(Subscription.status == "ACTIVE").options(joinedload(Subscription.instrument), joinedload(Subscription.account))
        if client_id is not None:
            query = query.join(AccountRole, AccountRole.account_id == Subscription.account_id).where(AccountRole.client_id == client_id, AccountRole.is_active.is_(True))
        subscriptions = list(db.scalars(query).unique())
        created: list[InterestPayment] = []
        for subscription in subscriptions:
            months = FREQUENCY_MONTHS.get(subscription.instrument.interest_frequency.upper(), 12)
            due_date = _add_months(subscription.subscribed_at.date(), months)
            coupon_amount = (Decimal(subscription.invested_amount) * Decimal(subscription.subscription_yield) / Decimal("100") / (Decimal("12") / Decimal(months))).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            while due_date <= as_of and due_date <= subscription.effective_maturity_date:
                existing = db.scalar(select(InterestPayment.id).where(InterestPayment.subscription_id == subscription.id, InterestPayment.payment_date == due_date))
                if not existing:
                    payment = InterestPayment(subscription_id=subscription.id, payment_date=due_date, amount=coupon_amount, status="EN_ATTENTE")
                    db.add(payment)
                    db.flush()
                    transaction = Transaction(
                        transaction_type="PAIEMENT_INTERET",
                        destination_account_id=subscription.account_id,
                        amount=coupon_amount,
                        currency=subscription.instrument.currency,
                        description=f"Coupon {subscription.instrument.code} - {due_date.isoformat()}",
                        status="PENDING_APPROVAL",
                        is_automatic=True,
                        subscription_id=subscription.id,
                    )
                    db.add(transaction)
                    db.flush()
                    payment.transaction_id = transaction.id
                    audit(db, client_id, "INTEREST_PAYMENT_CREATED", "interest_payment", payment.id, {"subscription_id": subscription.id, "amount": str(coupon_amount)})
                    created.append(payment)
                due_date = _add_months(due_date, months)
        db.commit()
        return created

    @staticmethod
    def list_for_client(db: Session, client_id: int, subscription_id: int | None = None) -> list[InterestPayment]:
        account_ids = select(AccountRole.account_id).where(AccountRole.client_id == client_id, AccountRole.is_active.is_(True))
        query = select(InterestPayment).join(InterestPayment.subscription).where(Subscription.account_id.in_(account_ids)).options(joinedload(InterestPayment.subscription).joinedload(Subscription.instrument)).order_by(InterestPayment.payment_date.desc())
        if subscription_id is not None:
            query = query.where(InterestPayment.subscription_id == subscription_id)
        return list(db.scalars(query).unique())

    @staticmethod
    def get_for_client(db: Session, payment_id: int, client_id: int) -> InterestPayment | None:
        payment = db.scalar(select(InterestPayment).where(InterestPayment.id == payment_id).options(joinedload(InterestPayment.subscription)))
        if payment:
            require_account_access(db, payment.subscription.account_id, client_id)
        return payment
