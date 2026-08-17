import json
from collections import defaultdict
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import or_, select
from sqlalchemy.orm import Session, joinedload, selectinload

from app.models.models import Account, AccountRole, Instrument, InterestPayment, InvestmentOrder, Subscription, Transaction
from app.services.investment_metrics import annualized_return


ORDER_STATUS_EXPLANATIONS = {
    "SUBMITTED": "La demande a été soumise et attend les contrôles prévus avant la validation finale.",
    "COMPLIANCE_REVIEW": "La demande est en cours de vérification du dossier.",
    "BACK_OFFICE_REVIEW": "La demande est en cours de traitement opérationnel.",
    "READY_FOR_CHECKER": "Les premiers contrôles sont terminés et la validation finale est attendue.",
    "PENDING_APPROVAL": "L'opération attend l'approbation d'un utilisateur habilité différent de son créateur.",
    "EXECUTED": "La demande a été exécutée.",
    "REJECTED": "La demande a été rejetée; la raison affichée dans le portail doit être consultée.",
}


def _value(value):
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    return value


def build_client_context(db: Session, client_id: int) -> dict:
    """Build a minimal, authorized snapshot for the authenticated client."""
    accounts = list(
        db.scalars(
            select(Account)
            .join(AccountRole, AccountRole.account_id == Account.id)
            .where(AccountRole.client_id == client_id, AccountRole.is_active.is_(True))
            .order_by(Account.id)
        ).unique()
    )
    account_ids = [account.id for account in accounts]

    subscriptions = []
    orders = []
    transactions = []
    if account_ids:
        subscriptions = list(
            db.scalars(
                select(Subscription)
                .where(Subscription.account_id.in_(account_ids))
                .options(joinedload(Subscription.instrument).joinedload(Instrument.instrument_type))
                .order_by(Subscription.effective_maturity_date)
                .limit(20)
            )
        )
        orders = list(
            db.scalars(
                select(InvestmentOrder)
                .where(InvestmentOrder.client_id == client_id)
                .options(selectinload(InvestmentOrder.instrument), selectinload(InvestmentOrder.account), selectinload(InvestmentOrder.steps))
                .order_by(InvestmentOrder.created_at.desc())
                .limit(20)
            )
        )
        transactions = list(
            db.scalars(
                select(Transaction)
                .where(or_(Transaction.source_account_id.in_(account_ids), Transaction.destination_account_id.in_(account_ids)))
                .order_by(Transaction.created_at.desc())
                .limit(20)
            )
        )

    paid_coupons_by_subscription: dict[int, Decimal] = defaultdict(lambda: Decimal("0"))
    if subscriptions:
        payments = db.scalars(
            select(InterestPayment).where(
                InterestPayment.subscription_id.in_([item.id for item in subscriptions]),
                InterestPayment.status == "PAYE",
            )
        ).all()
        for payment in payments:
            paid_coupons_by_subscription[payment.subscription_id] += Decimal(payment.amount)

    context = {
        "accounts": [
            {
                "account_number": account.account_number,
                "type": account.account_type,
                "currency": account.currency,
                "balance": _value(account.balance),
                "available_balance": _value(account.available_balance),
                "status": account.status,
            }
            for account in accounts
        ],
        "positions": [],
        "obligations": [],
        "orders": [
            {
                "id": order.id,
                "instrument": order.instrument.name if order.instrument else None,
                "amount": _value(order.amount),
                "currency": order.currency,
                "status": order.status,
                "status_explanation": ORDER_STATUS_EXPLANATIONS.get(order.status, "Le statut doit être consulté dans le portail."),
                "steps": [{"code": step.step_code, "status": step.status} for step in order.steps],
                "created_at": _value(order.created_at),
                "account_number": order.account.account_number if order.account else None,
            }
            for order in orders
        ],
        "transactions": [
            {
                "id": transaction.id,
                "type": transaction.transaction_type,
                "amount": _value(transaction.amount),
                "currency": transaction.currency,
                "status": transaction.status,
                "created_at": _value(transaction.created_at),
                "description": transaction.description,
            }
            for transaction in transactions
        ],
    }
    today = date.today()
    for subscription in subscriptions:
        instrument = subscription.instrument
        currency = instrument.currency if instrument else "USD"
        instrument_type = instrument.instrument_type.name if instrument and instrument.instrument_type else "Instrument"
        paid_coupons = paid_coupons_by_subscription[subscription.id]
        tma = annualized_return(
            Decimal(subscription.invested_amount),
            Decimal(subscription.current_value),
            subscription.subscribed_at.date(),
            today,
            paid_coupons,
            Decimal(subscription.fee_amount),
        )
        position = {
            "instrument": instrument.name if instrument else None,
            "instrument_code": instrument.code if instrument else None,
            "instrument_type": instrument_type,
            "currency": currency,
            "invested_amount": _value(subscription.invested_amount),
            "current_value": _value(subscription.current_value),
            "return_amount": _value(Decimal(subscription.current_value) - Decimal(subscription.invested_amount)),
            "tma_percentage": _value(tma),
            "accrued_interest": _value(subscription.accrued_interest),
            "paid_coupons": _value(paid_coupons),
            "fees": _value(subscription.fee_amount),
            "maturity_date": _value(subscription.effective_maturity_date),
            "status": subscription.status,
        }
        context["positions"].append(position)
        if instrument_type.lower() == "obligation":
            context["obligations"].append(position)
    totals = defaultdict(lambda: {"invested_amount": Decimal("0"), "current_value": Decimal("0"), "accrued_interest": Decimal("0"), "fees": Decimal("0"), "tma_percentage": Decimal("0")})
    for position in context["positions"]:
        currency = position["currency"] or "USD"
        invested = Decimal(position["invested_amount"])
        totals[currency]["invested_amount"] += invested
        totals[currency]["current_value"] += Decimal(position["current_value"])
        totals[currency]["accrued_interest"] += Decimal(position["accrued_interest"])
        totals[currency]["fees"] += Decimal(position["fees"])
        totals[currency]["tma_percentage"] += invested * Decimal(position["tma_percentage"])
    for currency, values in totals.items():
        invested = values["invested_amount"]
        values["tma_percentage"] = values["tma_percentage"] / invested if invested else Decimal("0")
    context["portfolio_totals_by_currency"] = {
        currency: {key: _value(value) for key, value in values.items()}
        for currency, values in totals.items()
    }
    liquidity = defaultdict(lambda: Decimal("0"))
    for account in accounts:
        liquidity[account.currency] += Decimal(account.available_balance)
    context["available_liquidity_by_currency"] = {currency: _value(value) for currency, value in liquidity.items()}
    return json.loads(json.dumps(context, ensure_ascii=False))
