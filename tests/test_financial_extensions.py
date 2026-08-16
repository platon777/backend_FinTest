from datetime import date, datetime, timezone
from decimal import Decimal

from app.models.models import AccountingEntry, Subscription, Transaction
from app.services.interest_service import InterestService
from app.services.investment_metrics import annualized_return
from app.services.transaction_service import TransactionService


def test_tma_is_annualized_from_dated_cashflows():
    result = annualized_return(Decimal("1000"), Decimal("1100"), date(2025, 1, 1), date(2026, 1, 1))
    assert Decimal("9.99") <= result <= Decimal("10.01")


def test_coupon_generation_is_idempotent_and_checker_execution_updates_payment(client_app, demo_data, db_session):
    subscription = Subscription(
        account_id=demo_data["account"].id,
        instrument_id=demo_data["instrument"].id,
        invested_amount=Decimal("1000"),
        units=Decimal("1"),
        subscribed_at=datetime(2025, 1, 1, tzinfo=timezone.utc),
        effective_maturity_date=date(2028, 1, 1),
        subscription_yield=Decimal("5.5000"),
        current_value=Decimal("1000"),
        accrued_interest=Decimal("0"),
        status="ACTIVE",
    )
    db_session.add(subscription)
    db_session.commit()

    first = InterestService.generate_due_payments(db_session, date(2026, 8, 16), demo_data["first"].id)
    second = InterestService.generate_due_payments(db_session, date(2026, 8, 16), demo_data["first"].id)

    assert len(first) == 1
    assert second == []
    payment = first[0]
    transaction_id = payment.transaction_id
    executed = TransactionService.approve(db_session, transaction_id, demo_data["second"].id)
    db_session.refresh(payment)
    db_session.refresh(demo_data["account"])
    assert executed.status == "EXECUTED"
    assert payment.status == "PAYE"
    assert demo_data["account"].balance == Decimal("1055.00")


def test_reversal_creates_compensating_transaction_and_new_posting_version(client_app, demo_data, db_session):
    def login(email):
        response = client_app.post("/api/v1/auth/login", json={"email": email, "password": "Password!123"})
        assert response.status_code == 200
        return {"Authorization": f"Bearer {response.json()['tokens']['access_token']}"}

    first_headers = login("first@profin.ht")
    second_headers = login("second@profin.ht")
    created = client_app.post(
        "/api/v1/transactions/",
        headers=first_headers,
        json={"transaction_type": "DEPOT", "amount": "100", "currency": "USD", "destination_account_id": demo_data["account"].id},
    )
    assert created.status_code == 201, created.text
    transaction_id = created.json()["transaction"]["id"]
    approved = client_app.post(f"/api/v1/transactions/{transaction_id}/approve", headers=second_headers)
    assert approved.status_code == 200, approved.text

    requested = client_app.post(f"/api/v1/transactions/{transaction_id}/reverse", headers=second_headers, json={"reason": "Correction de saisie"})
    assert requested.status_code == 201, requested.text
    reversal_id = requested.json()["transaction"]["id"]
    executed = client_app.post(f"/api/v1/transactions/{reversal_id}/approve", headers=first_headers)
    assert executed.status_code == 200, executed.text

    db_session.expire_all()
    original = db_session.get(Transaction, transaction_id)
    reversal = db_session.get(Transaction, reversal_id)
    entries = db_session.query(AccountingEntry).filter(AccountingEntry.transaction_id == reversal_id).all()
    account = db_session.get(type(demo_data["account"]), demo_data["account"].id)
    assert reversal.status == "EXECUTED"
    assert original.version == 2
    assert original.reversed_at is not None
    assert reversal.version == 2
    assert all(entry.is_reversal and entry.posting_version == 2 for entry in entries)
    assert sum(entry.amount for entry in entries if entry.direction == "DEBIT") == sum(entry.amount for entry in entries if entry.direction == "CREDIT")
    assert account.balance == Decimal("1000.00")
