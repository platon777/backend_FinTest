"""Rapports métier du portail client et du pilotage opérationnel."""

from collections import defaultdict
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

from sqlalchemy import or_, select
from sqlalchemy.orm import Session, joinedload

from app.models.models import (
    Account,
    AccountRole,
    InterestPayment,
    Client,
    InvestmentOrder,
    Instrument,
    OrderWorkflowStep,
    Subscription,
    Transaction,
)
from app.services.investment_metrics import annualized_return


OPEN_ORDER_STATUSES = {"SUBMITTED", "COMPLIANCE_REVIEW", "BACK_OFFICE_REVIEW", "READY_FOR_CHECKER"}
STEP_ORDER = ("CONFORMITE", "BACK_OFFICE", "CHECKER")
BACK_OFFICE_ROLES = {"MANDATAIRE", "CONFORMITE", "BACK_OFFICE", "SUPERVISEUR"}


def _money(value: Decimal | int | float | None) -> Decimal:
    return Decimal(value or 0).quantize(Decimal("0.01"))


def _month_start(value: datetime) -> date:
    return value.date().replace(day=1)


def _client_name(client: Client | None) -> str:
    if not client:
        return "Client non renseigné"
    if client.institutional_profile:
        return client.institutional_profile.company_name
    if client.individual_profile:
        return f"{client.individual_profile.first_name} {client.individual_profile.last_name}"
    return client.auth.email if client.auth else f"Client #{client.id}"


def _next_step(order: InvestmentOrder) -> str | None:
    pending = {step.step_code: step for step in order.steps if step.status == "PENDING"}
    return next((code for code in STEP_ORDER if code in pending), None)


def _account_ids(db: Session, client_id: int, roles: set[str] | None = None) -> list[int]:
    query = select(AccountRole.account_id).where(AccountRole.client_id == client_id, AccountRole.is_active.is_(True))
    if roles:
        query = query.where(AccountRole.role.in_(roles))
    return list(db.scalars(query))


def _base_currency_bucket(currency: str) -> dict:
    return {
        "currency": currency,
        "invested": Decimal("0.00"),
        "current_value": Decimal("0.00"),
        "accrued_interest": Decimal("0.00"),
        "paid_coupons": Decimal("0.00"),
        "fees": Decimal("0.00"),
        "return_amount": Decimal("0.00"),
        "return_percentage": Decimal("0.00"),
        "tma_percentage": Decimal("0.00"),
        "available_cash": Decimal("0.00"),
        "balance": Decimal("0.00"),
        "active_positions": 0,
        "reserved_orders": Decimal("0.00"),
    }


class ReportingService:
    @staticmethod
    def client_report(db: Session, client_id: int, horizon_days: int = 90, months: int = 6) -> dict:
        account_ids = _account_ids(db, client_id)
        accounts = list(db.scalars(select(Account).where(Account.id.in_(account_ids), Account.status == "ACTIF"))) if account_ids else []
        subscriptions = list(
            db.scalars(
                select(Subscription)
                .where(Subscription.account_id.in_(account_ids), Subscription.status == "ACTIVE")
                .options(joinedload(Subscription.instrument).joinedload(Instrument.instrument_type))
            )
        ) if account_ids else []
        payments = list(
            db.scalars(
                select(InterestPayment)
                .where(InterestPayment.subscription_id.in_([item.id for item in subscriptions]), InterestPayment.status == "PAYE")
            )
        ) if subscriptions else []
        paid_coupons_by_subscription: dict[int, Decimal] = defaultdict(lambda: Decimal("0.00"))
        for payment in payments:
            paid_coupons_by_subscription[payment.subscription_id] += Decimal(payment.amount)

        orders = list(
            db.scalars(
                select(InvestmentOrder)
                .where(InvestmentOrder.account_id.in_(account_ids))
                .options(joinedload(InvestmentOrder.instrument), joinedload(InvestmentOrder.account), joinedload(InvestmentOrder.steps))
                .order_by(InvestmentOrder.created_at.desc())
            ).unique()
        ) if account_ids else []

        by_currency: dict[str, dict] = {}
        for account in accounts:
            bucket = by_currency.setdefault(account.currency, _base_currency_bucket(account.currency))
            bucket["available_cash"] += Decimal(account.available_balance)
            bucket["balance"] += Decimal(account.balance)
        for subscription in subscriptions:
            currency = subscription.instrument.currency
            bucket = by_currency.setdefault(currency, _base_currency_bucket(currency))
            bucket["invested"] += Decimal(subscription.invested_amount)
            bucket["current_value"] += Decimal(subscription.current_value)
            bucket["accrued_interest"] += Decimal(subscription.accrued_interest)
            bucket["paid_coupons"] += paid_coupons_by_subscription[subscription.id]
            bucket["fees"] += Decimal(subscription.fee_amount)
            bucket["return_amount"] += Decimal(subscription.current_value) - Decimal(subscription.invested_amount)
            bucket["active_positions"] += 1
        for order in orders:
            if order.status in OPEN_ORDER_STATUSES:
                bucket = by_currency.setdefault(order.currency, _base_currency_bucket(order.currency))
                bucket["reserved_orders"] += Decimal(order.amount)
        for bucket in by_currency.values():
            bucket["return_percentage"] = (bucket["return_amount"] / bucket["invested"] * 100).quantize(Decimal("0.01")) if bucket["invested"] else Decimal("0.00")

        allocation: dict[tuple[str, str], Decimal] = defaultdict(lambda: Decimal("0.00"))
        position_rows = []
        today = date.today()
        maturity_limit = today + timedelta(days=horizon_days)
        maturities = []
        tma_by_currency: dict[str, list[tuple[Decimal, Decimal]]] = defaultdict(list)
        for subscription in subscriptions:
            type_name = subscription.instrument.instrument_type.name if subscription.instrument.instrument_type else "Autre"
            currency = subscription.instrument.currency
            allocation[(type_name, currency)] += Decimal(subscription.current_value)
            days = (subscription.effective_maturity_date - today).days
            paid_coupons = paid_coupons_by_subscription[subscription.id]
            tma = annualized_return(Decimal(subscription.invested_amount), Decimal(subscription.current_value), subscription.subscribed_at.date(), today, paid_coupons, Decimal(subscription.fee_amount))
            tma_by_currency[currency].append((Decimal(subscription.invested_amount), tma))
            position_rows.append({
                "subscription_id": subscription.id,
                "account_id": subscription.account_id,
                "instrument_code": subscription.instrument.code,
                "instrument_name": subscription.instrument.name,
                "instrument_type": type_name,
                "currency": currency,
                "invested_amount": subscription.invested_amount,
                "current_value": subscription.current_value,
                "return_amount": _money(Decimal(subscription.current_value) - Decimal(subscription.invested_amount)),
                "return_percentage": _money((Decimal(subscription.current_value) - Decimal(subscription.invested_amount)) / Decimal(subscription.invested_amount) * 100) if subscription.invested_amount else Decimal("0.00"),
                "tma_percentage": tma,
                "paid_coupons": paid_coupons,
                "fees": subscription.fee_amount,
                "maturity_date": subscription.effective_maturity_date,
                "days_to_maturity": days,
            })
            if subscription.effective_maturity_date <= maturity_limit:
                maturities.append({
                    "subscription_id": subscription.id,
                    "instrument_code": subscription.instrument.code,
                    "instrument_name": subscription.instrument.name,
                    "currency": currency,
                    "current_value": subscription.current_value,
                    "maturity_date": subscription.effective_maturity_date,
                    "days_to_maturity": max(days, 0),
                })

        for currency, values in tma_by_currency.items():
            invested_total = sum((amount for amount, _ in values), Decimal("0.00"))
            by_currency[currency]["tma_percentage"] = (sum((amount * tma for amount, tma in values), Decimal("0.00")) / invested_total).quantize(Decimal("0.01")) if invested_total else Decimal("0.00")

        pipeline: dict[str, dict] = defaultdict(lambda: {"status": "", "count": 0, "amount_by_currency": defaultdict(lambda: Decimal("0.00"))})
        for order in orders:
            row = pipeline[order.status]
            row["status"] = order.status
            row["count"] += 1
            row["amount_by_currency"][order.currency] += Decimal(order.amount)
        pipeline_rows = [
            {"status": key, "count": value["count"], "amount_by_currency": dict(value["amount_by_currency"])}
            for key, value in pipeline.items()
        ]

        since = datetime.now(timezone.utc) - timedelta(days=31 * months)
        transactions = list(
            db.scalars(
                select(Transaction)
                .where(
                    Transaction.status == "EXECUTED",
                    Transaction.created_at >= since,
                    or_(Transaction.source_account_id.in_(account_ids), Transaction.destination_account_id.in_(account_ids)),
                )
                .order_by(Transaction.created_at.asc())
            )
        ) if account_ids else []
        cashflow: dict[tuple[date, str], dict] = {}
        for transaction in transactions:
            key = (_month_start(transaction.created_at), transaction.currency)
            row = cashflow.setdefault(key, {"month": key[0], "currency": key[1], "deposits": Decimal("0.00"), "withdrawals": Decimal("0.00"), "investments": Decimal("0.00"), "maturities": Decimal("0.00"), "coupon_payments": Decimal("0.00"), "fees": Decimal("0.00")})
            amount = Decimal(transaction.amount)
            if transaction.transaction_type == "DEPOT":
                row["deposits"] += amount
            elif transaction.transaction_type in {"RETRAIT", "TRANSFERT", "SOUSCRIPTION"}:
                row["withdrawals" if transaction.transaction_type != "SOUSCRIPTION" else "investments"] += amount
            elif transaction.transaction_type == "REMBOURSEMENT_MATURITE":
                row["maturities"] += amount
            elif transaction.transaction_type == "PAIEMENT_INTERET":
                row["coupon_payments"] += amount
            elif transaction.transaction_type == "FRAIS":
                row["fees"] += amount
        cashflow_rows = []
        for row in sorted(cashflow.values(), key=lambda item: (item["month"], item["currency"])):
            row["net"] = row["deposits"] + row["maturities"] + row["coupon_payments"] - row["withdrawals"] - row["investments"] - row["fees"]
            cashflow_rows.append(row)

        alerts = []
        open_orders = [order for order in orders if order.status in OPEN_ORDER_STATUSES]
        if open_orders:
            alerts.append({"code": "ORDERS_IN_REVIEW", "severity": "warning", "title": "Ordres en cours de validation", "detail": f"{len(open_orders)} ordre(s) mobilisent un montant réservé."})
        if maturities:
            alerts.append({"code": "UPCOMING_MATURITIES", "severity": "info", "title": "Échéances à anticiper", "detail": f"{len(maturities)} position(s) arrivent à échéance sous {horizon_days} jours."})

        return {
            "as_of": today,
            "generated_at": datetime.now(timezone.utc),
            "kpis": {
                "active_positions": len(subscriptions),
                "pending_orders": len(open_orders),
                "accounts": len(accounts),
                "maturities_next_horizon": len(maturities),
            },
            "summary_by_currency": list(by_currency.values()),
            "allocation": [{"instrument_type": key[0], "currency": key[1], "current_value": value} for key, value in allocation.items()],
            "positions": position_rows,
            "order_pipeline": pipeline_rows,
            "maturities": sorted(maturities, key=lambda item: item["maturity_date"]),
            "cashflow": cashflow_rows,
            "alerts": alerts,
        }

    @staticmethod
    def backoffice_report(db: Session, client_id: int, horizon_days: int = 90, limit: int = 30) -> dict:
        account_ids = _account_ids(db, client_id, BACK_OFFICE_ROLES)
        if not account_ids:
            raise PermissionError("Ce profil ne possède pas d'habilitation back-office")
        accounts = list(db.scalars(select(Account).where(Account.id.in_(account_ids), Account.status == "ACTIF")))
        orders = list(
            db.scalars(
                select(InvestmentOrder)
                .where(InvestmentOrder.account_id.in_(account_ids), InvestmentOrder.status.in_(OPEN_ORDER_STATUSES))
                .options(joinedload(InvestmentOrder.instrument), joinedload(InvestmentOrder.account), joinedload(InvestmentOrder.steps))
                .order_by(InvestmentOrder.created_at.asc())
            ).unique()
        )
        transactions = list(
            db.scalars(
                select(Transaction)
                .where(
                    Transaction.status == "PENDING_APPROVAL",
                    or_(Transaction.source_account_id.in_(account_ids), Transaction.destination_account_id.in_(account_ids)),
                )
                .order_by(Transaction.created_at.asc())
            )
        )
        client_ids = {order.client_id for order in orders} | {item.created_by_client_id for item in transactions if item.created_by_client_id}
        clients = {client.id: client for client in db.scalars(select(Client).where(Client.id.in_(client_ids))).all()} if client_ids else {}
        today = date.today()
        workflow = {code: {"step": code, "count": 0, "amount_by_currency": defaultdict(lambda: Decimal("0.00")), "oldest_age_days": 0} for code in STEP_ORDER}
        order_queue = []
        for order in orders:
            step = _next_step(order) or "CONFORMITE"
            age = max((today - order.created_at.date()).days, 0)
            row = workflow[step]
            row["count"] += 1
            row["amount_by_currency"][order.currency] += Decimal(order.amount)
            row["oldest_age_days"] = max(row["oldest_age_days"], age)
            order_queue.append({
                "queue_type": "INVESTMENT_ORDER",
                "id": order.id,
                "client_name": _client_name(clients.get(order.client_id)),
                "account_number": order.account.account_number,
                "operation": order.instrument.name,
                "instrument_code": order.instrument.code,
                "amount": order.amount,
                "currency": order.currency,
                "status": order.status,
                "next_step": step,
                "age_days": age,
                "created_at": order.created_at,
            })
        transaction_queue = []
        for transaction in transactions:
            age = max((today - transaction.created_at.date()).days, 0)
            account = next((item for item in accounts if item.id in {transaction.source_account_id, transaction.destination_account_id}), None)
            transaction_queue.append({
                "queue_type": "TRANSACTION",
                "id": transaction.id,
                "client_name": _client_name(clients.get(transaction.created_by_client_id)),
                "account_number": account.account_number if account else None,
                "operation": transaction.transaction_type,
                "instrument_code": None,
                "amount": transaction.amount,
                "currency": transaction.currency,
                "status": transaction.status,
                "next_step": "CHECKER",
                "age_days": age,
                "created_at": transaction.created_at,
            })
        queue = sorted(order_queue + transaction_queue, key=lambda item: item["created_at"])[:limit]

        subscriptions = list(db.scalars(select(Subscription).where(Subscription.account_id.in_(account_ids), Subscription.status == "ACTIVE").options(joinedload(Subscription.instrument))))
        payments = list(db.scalars(select(InterestPayment).where(InterestPayment.subscription_id.in_([item.id for item in subscriptions]), InterestPayment.status == "PAYE"))) if subscriptions else []
        paid_coupons = sum((Decimal(item.amount) for item in payments), Decimal("0.00"))
        positions_by_currency: dict[str, Decimal] = defaultdict(lambda: Decimal("0.00"))
        fees_by_currency: dict[str, Decimal] = defaultdict(lambda: Decimal("0.00"))
        aum_by_currency: dict[str, Decimal] = defaultdict(lambda: Decimal("0.00"))
        for subscription in subscriptions:
            positions_by_currency[subscription.instrument.currency] += Decimal(subscription.current_value)
            fees_by_currency[subscription.instrument.currency] += Decimal(subscription.fee_amount)
        for account in accounts:
            aum_by_currency[account.currency] += Decimal(account.balance)
        for currency, value in positions_by_currency.items():
            aum_by_currency[currency] += value
        cutoff = datetime.now(timezone.utc) - timedelta(days=30)
        rejected_orders = db.scalar(select(InvestmentOrder.id).where(InvestmentOrder.account_id.in_(account_ids), InvestmentOrder.status == "REJECTED", InvestmentOrder.updated_at >= cutoff).order_by(InvestmentOrder.updated_at.desc()).limit(1))
        maturities = [item for item in subscriptions if item.effective_maturity_date <= today + timedelta(days=horizon_days)]
        old_items = [item for item in queue if item["age_days"] >= 2]
        exceptions = []
        if old_items:
            exceptions.append({"code": "AGING_QUEUE", "severity": "warning", "title": "File en attente depuis plus de 48 h", "detail": f"{len(old_items)} opération(s) à prioriser."})
        if rejected_orders:
            exceptions.append({"code": "RECENT_REJECTIONS", "severity": "info", "title": "Rejets récents à analyser", "detail": "Au moins un ordre a été rejeté sur les 30 derniers jours."})

        return {
            "as_of": today,
            "generated_at": datetime.now(timezone.utc),
            "scope": {"accounts": len(accounts), "account_numbers": [item.account_number for item in accounts], "roles": sorted(BACK_OFFICE_ROLES)},
            "kpis": {
                "orders_in_review": len(orders),
                "transactions_pending": len(transactions),
                "total_items_in_queue": len(orders) + len(transactions),
                "active_accounts": len(accounts),
                "active_positions": len(subscriptions),
                "maturities_next_horizon": len(maturities),
                "aum_by_currency": dict(aum_by_currency),
                "fees_by_currency": dict(fees_by_currency),
                "paid_coupons": paid_coupons,
            },
            "workflow": [{"step": key, "count": value["count"], "amount_by_currency": dict(value["amount_by_currency"]), "oldest_age_days": value["oldest_age_days"]} for key, value in workflow.items()],
            "queue": queue,
            "positions_by_currency": [{"currency": currency, "current_value": value} for currency, value in positions_by_currency.items()],
            "aum_by_currency": [{"currency": currency, "value": value} for currency, value in aum_by_currency.items()],
            "fees_by_currency": [{"currency": currency, "value": value} for currency, value in fees_by_currency.items()],
            "exceptions": exceptions,
        }

    @staticmethod
    def regulatory_report(db: Session, client_id: int, horizon_days: int = 90) -> dict:
        """Projection interne de supervision : AUM, frais, coupons et activite.

        Les montants ne sont jamais additionnes entre devises. Le rapport
        est reserve aux profils habilites sur leurs comptes mandats.
        """
        account_ids = _account_ids(db, client_id, BACK_OFFICE_ROLES)
        if not account_ids:
            raise PermissionError("Ce profil ne possede pas d'habilitation de reporting")
        accounts = list(db.scalars(select(Account).where(Account.id.in_(account_ids), Account.status == "ACTIF")))
        subscriptions = list(db.scalars(select(Subscription).where(Subscription.account_id.in_(account_ids), Subscription.status.in_(["ACTIVE", "MATURITE_EN_ATTENTE"])).options(joinedload(Subscription.instrument))))
        payment_rows = list(db.scalars(select(InterestPayment).where(InterestPayment.subscription_id.in_([item.id for item in subscriptions])).options(joinedload(InterestPayment.subscription).joinedload(Subscription.instrument)))) if subscriptions else []
        transactions = list(db.scalars(select(Transaction).where(Transaction.status == "EXECUTED", or_(Transaction.source_account_id.in_(account_ids), Transaction.destination_account_id.in_(account_ids))).order_by(Transaction.created_at.desc())))
        today = date.today()
        aum: dict[str, Decimal] = defaultdict(lambda: Decimal("0.00"))
        fees: dict[str, Decimal] = defaultdict(lambda: Decimal("0.00"))
        positions = []
        for account in accounts:
            aum[account.currency] += Decimal(account.balance)
        for subscription in subscriptions:
            currency = subscription.instrument.currency
            paid = sum((Decimal(item.amount) for item in payment_rows if item.subscription_id == subscription.id and item.status == "PAYE"), Decimal("0.00"))
            aum[currency] += Decimal(subscription.current_value)
            fees[currency] += Decimal(subscription.fee_amount)
            positions.append({
                "instrument_code": subscription.instrument.code,
                "account_id": subscription.account_id,
                "currency": currency,
                "invested_amount": subscription.invested_amount,
                "current_value": subscription.current_value,
                "accrued_interest": subscription.accrued_interest,
                "paid_coupons": paid,
                "fees": subscription.fee_amount,
                "tma_percentage": annualized_return(Decimal(subscription.invested_amount), Decimal(subscription.current_value), subscription.subscribed_at.date(), today, paid, Decimal(subscription.fee_amount)),
                "maturity_date": subscription.effective_maturity_date,
                "status": subscription.status,
            })
        for transaction in transactions:
            if transaction.transaction_type == "FRAIS":
                fees[transaction.currency] += Decimal(transaction.amount)
        by_type: dict[str, dict[str, Decimal]] = defaultdict(lambda: defaultdict(lambda: Decimal("0.00")))
        for transaction in transactions:
            by_type[transaction.transaction_type][transaction.currency] += Decimal(transaction.amount)
        pending_coupons = [item for item in payment_rows if item.status == "EN_ATTENTE"]
        upcoming = [item for item in subscriptions if item.effective_maturity_date <= today + timedelta(days=horizon_days)]
        return {
            "as_of": today,
            "generated_at": datetime.now(timezone.utc),
            "scope": {"accounts": len(accounts), "account_numbers": [item.account_number for item in accounts], "roles": sorted(BACK_OFFICE_ROLES)},
            "aum_by_currency": [{"currency": currency, "value": value} for currency, value in sorted(aum.items())],
            "fees_by_currency": [{"currency": currency, "value": value} for currency, value in sorted(fees.items())],
            "positions": positions,
            "coupon_control": {
                "pending": len(pending_coupons),
                "paid": len([item for item in payment_rows if item.status == "PAYE"]),
                "paid_amount": sum((Decimal(item.amount) for item in payment_rows if item.status == "PAYE"), Decimal("0.00")),
            },
            "maturities_next_horizon": len(upcoming),
            "activity_by_type": [{"transaction_type": key, "amount_by_currency": dict(value)} for key, value in by_type.items()],
        }
