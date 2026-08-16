from decimal import Decimal

from datetime import date

from app.models.models import AccountingEntry, Instrument, Subscription, Transaction
from app.services.subscription_service import SubscriptionService
from app.services.transaction_service import TransactionService


def login(client, email):
    response = client.post("/api/v1/auth/login", json={"email": email, "password": "Password!123"})
    assert response.status_code == 200, response.text
    return response.json()


def auth_headers(login_response):
    return {"Authorization": f"Bearer {login_response['tokens']['access_token']}"}


def test_registration_login_and_refresh_rotation(client_app):
    registration = client_app.post("/api/v1/auth/register", json={
        "client_type": "INDIVIDUEL", "email": "new@profin.ht", "password": "Password!123",
        "prenom": "Nadia", "nom": "Pierre", "date_naissance": "1992-02-10",
        "numero_piece_identite": "CIN-NEW-001", "adresse_ligne1": "1 Rue Test", "ville": "Port-au-Prince",
    })
    assert registration.status_code == 201, registration.text
    logged = login(client_app, "new@profin.ht")
    refreshed = client_app.post("/api/v1/auth/refresh", json={"refresh_token": logged["tokens"]["refresh_token"]})
    assert refreshed.status_code == 200
    reused = client_app.post("/api/v1/auth/refresh", json={"refresh_token": logged["tokens"]["refresh_token"]})
    assert reused.status_code == 401


def test_transaction_is_pending_then_checker_executes_and_access_is_scoped(client_app, demo_data):
    first = login(client_app, "first@profin.ht")
    second = login(client_app, "second@profin.ht")
    pending = client_app.post("/api/v1/transactions/", headers=auth_headers(first), json={
        "transaction_type": "RETRAIT", "amount": "200", "currency": "USD", "source_account_id": demo_data["account"].id,
        "description": "Retrait de démonstration",
    })
    assert pending.status_code == 201, pending.text
    transaction_id = pending.json()["transaction"]["id"]
    assert pending.json()["transaction"]["status"] == "PENDING_APPROVAL"

    approved = client_app.post(f"/api/v1/transactions/{transaction_id}/approve", headers=auth_headers(second))
    assert approved.status_code == 200, approved.text
    assert approved.json()["transaction"]["status"] == "EXECUTED"
    assert demo_data["account"].available_balance == Decimal("800.00")

    forbidden = client_app.post("/api/v1/transactions/", headers=auth_headers(second), json={
        "transaction_type": "RETRAIT", "amount": "10", "currency": "USD", "source_account_id": demo_data["private_account"].id,
    })
    assert forbidden.status_code == 403


def test_subscription_debits_cash_and_creates_position(db_session, demo_data):
    subscription = SubscriptionService.create(db_session, demo_data["first"].id, demo_data["account"].id, demo_data["instrument"].id, Decimal("500"))
    assert subscription.status == "ACTIVE"
    db_session.refresh(demo_data["account"])
    assert demo_data["account"].available_balance == Decimal("500.00")
    assert db_session.query(Subscription).count() == 1
    assert db_session.query(Transaction).filter(Transaction.transaction_type == "SOUSCRIPTION").count() == 1


def test_insufficient_balance_does_not_mutate_account(db_session, demo_data):
    try:
        SubscriptionService.create(db_session, demo_data["first"].id, demo_data["account"].id, demo_data["instrument"].id, Decimal("2000"))
    except ValueError:
        pass
    db_session.refresh(demo_data["account"])
    assert demo_data["account"].available_balance == Decimal("1000.00")


def test_deposit_updates_balances_and_creates_balanced_ledger(client_app, demo_data, db_session):
    first = login(client_app, "first@profin.ht")
    second = login(client_app, "second@profin.ht")
    pending = client_app.post("/api/v1/transactions/", headers=auth_headers(first), json={
        "transaction_type": "DEPOT", "amount": "300", "currency": "USD", "destination_account_id": demo_data["account"].id,
    })
    assert pending.status_code == 201
    transaction_id = pending.json()["transaction"]["id"]
    approved = client_app.post(f"/api/v1/transactions/{transaction_id}/approve", headers=auth_headers(second))
    assert approved.status_code == 200, approved.text
    db_session.refresh(demo_data["account"])
    assert demo_data["account"].balance == Decimal("1300.00")
    entries = db_session.query(AccountingEntry).filter(AccountingEntry.transaction_id == transaction_id).all()
    assert len(entries) == 2
    assert sum(item.amount for item in entries if item.direction == "DEBIT") == sum(item.amount for item in entries if item.direction == "CREDIT")


def test_transfer_rejects_currency_mismatch_without_mutating_accounts(client_app, demo_data, db_session):
    first = login(client_app, "first@profin.ht")
    second = login(client_app, "second@profin.ht")
    source_id = demo_data["account"].id
    destination_id = demo_data["htg_account"].id
    pending = client_app.post("/api/v1/transactions/", headers=auth_headers(first), json={
        "transaction_type": "TRANSFERT", "amount": "200", "currency": "USD", "source_account_id": source_id,
        "destination_account_id": destination_id,
    })
    assert pending.status_code == 201
    approved = client_app.post(f"/api/v1/transactions/{pending.json()['transaction']['id']}/approve", headers=auth_headers(second))
    assert approved.status_code == 400
    db_session.expire_all()
    assert db_session.get(type(demo_data["account"]), source_id).available_balance == Decimal("1000.00")
    assert db_session.get(type(demo_data["htg_account"]), destination_id).available_balance == Decimal("10000.00")


def test_transfer_conserves_money_and_credits_destination(client_app, demo_data, db_session):
    first = login(client_app, "first@profin.ht")
    second = login(client_app, "second@profin.ht")
    pending = client_app.post("/api/v1/transactions/", headers=auth_headers(first), json={
        "transaction_type": "TRANSFERT", "amount": "250", "currency": "USD",
        "source_account_id": demo_data["account"].id, "destination_account_id": demo_data["transfer_destination"].id,
    })
    assert pending.status_code == 201, pending.text
    approved = client_app.post(f"/api/v1/transactions/{pending.json()['transaction']['id']}/approve", headers=auth_headers(second))
    assert approved.status_code == 200, approved.text
    db_session.expire_all()
    source = db_session.get(type(demo_data["account"]), demo_data["account"].id)
    destination = db_session.get(type(demo_data["transfer_destination"]), demo_data["transfer_destination"].id)
    assert source.available_balance == Decimal("750.00")
    assert destination.available_balance == Decimal("750.00")
    assert source.available_balance + destination.available_balance == Decimal("1500.00")


def test_checker_can_reject_pending_transaction_without_mutating_balance(client_app, demo_data, db_session):
    first = login(client_app, "first@profin.ht")
    second = login(client_app, "second@profin.ht")
    pending = client_app.post("/api/v1/transactions/", headers=auth_headers(first), json={
        "transaction_type": "RETRAIT", "amount": "100", "currency": "USD", "source_account_id": demo_data["account"].id,
    })
    assert pending.status_code == 201
    rejected = client_app.post(f"/api/v1/transactions/{pending.json()['transaction']['id']}/reject", headers=auth_headers(second), json={"reason": "Pièce justificative manquante"})
    assert rejected.status_code == 200, rejected.text
    assert rejected.json()["transaction"]["status"] == "REJECTED"
    assert rejected.json()["transaction"]["rejection_reason"] == "Pièce justificative manquante"
    db_session.refresh(demo_data["account"])
    assert demo_data["account"].available_balance == Decimal("1000.00")


def test_checker_cannot_approve_own_transaction(client_app, demo_data):
    first = login(client_app, "first@profin.ht")
    pending = client_app.post("/api/v1/transactions/", headers=auth_headers(first), json={
        "transaction_type": "RETRAIT", "amount": "100", "currency": "USD", "source_account_id": demo_data["account"].id,
    })
    assert pending.status_code == 201
    response = client_app.post(f"/api/v1/transactions/{pending.json()['transaction']['id']}/approve", headers=auth_headers(first))
    assert response.status_code == 403


def test_redeem_restores_cash_and_closes_position(db_session, demo_data):
    subscription = SubscriptionService.create(db_session, demo_data["first"].id, demo_data["account"].id, demo_data["instrument"].id, Decimal("500"))
    redeemed = SubscriptionService.redeem(db_session, subscription.id, demo_data["first"].id)
    assert redeemed.status == "RACHETEE"
    db_session.refresh(demo_data["account"])
    assert demo_data["account"].available_balance == Decimal("1000.00")


def test_open_account_is_scoped_to_authenticated_client(client_app, demo_data, db_session):
    first = login(client_app, "first@profin.ht")
    response = client_app.post("/api/v1/comptes/", headers=auth_headers(first), json={"account_type": "EPARGNE", "currency": "EUR"})
    assert response.status_code == 201, response.text
    assert response.json()["account"]["currency"] == "EUR"


def test_maturity_generates_pending_repayment_then_checker_executes_it(db_session, demo_data):
    demo_data["instrument"].maturity_date = date(2020, 1, 1)
    db_session.flush()
    subscription = SubscriptionService.create(db_session, demo_data["first"].id, demo_data["account"].id, demo_data["instrument"].id, Decimal("500"))
    generated = SubscriptionService.generate_maturity_transactions(db_session, date(2026, 8, 15), demo_data["first"].id)
    assert len(generated) == 1
    assert generated[0].is_automatic is True
    assert generated[0].status == "PENDING_APPROVAL"
    executed = TransactionService.approve(db_session, generated[0].id, demo_data["second"].id)
    assert executed.status == "EXECUTED"
    db_session.refresh(subscription)
    db_session.refresh(demo_data["account"])
    assert subscription.status == "MATURE"
    assert demo_data["account"].available_balance == Decimal("1000.00")
