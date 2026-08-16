from app.models.models import Account, Instrument, InvestmentOrder, Subscription, Transaction


def account_dict(account: Account, role: str | None = None) -> dict:
    return {
        "id": account.id, "account_number": account.account_number, "account_type": account.account_type,
        "currency": account.currency, "balance": account.balance, "available_balance": account.available_balance,
        "status": account.status, "role": role,
    }


def instrument_dict(instrument: Instrument) -> dict:
    return {
        "id": instrument.id, "code": instrument.code, "name": instrument.name, "description": instrument.description,
        "issuer": instrument.issuer, "annual_yield": instrument.annual_yield, "issue_date": instrument.issue_date,
        "maturity_date": instrument.maturity_date, "nominal_value": instrument.nominal_value,
        "minimum_amount": instrument.minimum_amount, "currency": instrument.currency,
        "interest_frequency": instrument.interest_frequency, "status": instrument.status,
        "instrument_type": instrument.instrument_type.name if instrument.instrument_type else None,
    }


def subscription_dict(subscription: Subscription) -> dict:
    return {
        "id": subscription.id, "account_id": subscription.account_id, "instrument_id": subscription.instrument_id,
        "invested_amount": subscription.invested_amount, "units": subscription.units, "subscribed_at": subscription.subscribed_at,
        "effective_maturity_date": subscription.effective_maturity_date, "subscription_yield": subscription.subscription_yield,
        "current_value": subscription.current_value, "accrued_interest": subscription.accrued_interest,
        "status": subscription.status, "instrument_name": subscription.instrument.name if subscription.instrument else None,
        "instrument_code": subscription.instrument.code if subscription.instrument else None,
        "currency": subscription.instrument.currency if subscription.instrument else None,
    }


def transaction_dict(transaction: Transaction, db) -> dict:
    source = db.get(Account, transaction.source_account_id) if transaction.source_account_id else None
    destination = db.get(Account, transaction.destination_account_id) if transaction.destination_account_id else None
    return {
        "id": transaction.id, "transaction_type": transaction.transaction_type, "source_account_id": transaction.source_account_id,
        "destination_account_id": transaction.destination_account_id, "amount": transaction.amount, "currency": transaction.currency,
        "description": transaction.description, "status": transaction.status, "created_at": transaction.created_at,
        "executed_at": transaction.executed_at, "is_automatic": transaction.is_automatic, "subscription_id": transaction.subscription_id,
        "created_by_client_id": transaction.created_by_client_id, "approved_by_client_id": transaction.approved_by_client_id,
        "rejection_reason": transaction.rejection_reason,
        "source_account_number": source.account_number if source else None,
        "destination_account_number": destination.account_number if destination else None,
    }


def order_dict(order: InvestmentOrder) -> dict:
    return {
        "id": order.id,
        "client_id": order.client_id,
        "account_id": order.account_id,
        "instrument_id": order.instrument_id,
        "order_type": order.order_type,
        "amount": order.amount,
        "units": order.units,
        "currency": order.currency,
        "status": order.status,
        "client_comment": order.client_comment,
        "rejection_reason": order.rejection_reason,
        "created_at": order.created_at,
        "updated_at": order.updated_at,
        "submitted_by_client_id": order.submitted_by_client_id,
        "checked_by_client_id": order.checked_by_client_id,
        "executed_transaction_id": order.executed_transaction_id,
        "executed_subscription_id": order.executed_subscription_id,
        "instrument_name": order.instrument.name if order.instrument else None,
        "instrument_code": order.instrument.code if order.instrument else None,
        "account_number": order.account.account_number if order.account else None,
        "steps": [
            {"step_code": step.step_code, "status": step.status, "actor_profile": step.actor_profile, "notes": step.notes, "completed_at": step.completed_at}
            for step in order.steps
        ],
    }
