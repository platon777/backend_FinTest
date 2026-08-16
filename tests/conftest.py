import os
from datetime import date

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.core.security import hash_password
from app.db.database import Base, get_db
from app.models.models import Account, AccountRole, Client, ClientAuthentication, Instrument, InstrumentType
from main import app


TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL", "postgresql+psycopg2://profin:profin_dev@127.0.0.1:55432/profin_test")


@pytest.fixture()
def db_session():
    """Une base PostgreSQL réelle, dédiée aux tests et réinitialisée par test."""
    test_engine = create_engine(TEST_DATABASE_URL, pool_pre_ping=True)
    connection = test_engine.connect()
    Base.metadata.drop_all(connection)
    connection.commit()
    Base.metadata.create_all(connection)
    connection.commit()
    factory = sessionmaker(bind=connection, autoflush=False, expire_on_commit=False)
    session = factory()
    try:
        yield session
    finally:
        session.close()
        connection.rollback()
        Base.metadata.drop_all(connection)
        connection.commit()
        connection.close()
        test_engine.dispose()


@pytest.fixture()
def client_app(db_session):
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture()
def demo_data(db_session):
    first = Client(client_type="INDIVIDUEL", risk_profile="MODERE", status="ACTIF")
    first.auth = ClientAuthentication(email="first@profin.ht", password_hash=hash_password("Password!123"), is_active=True)
    second = Client(client_type="INDIVIDUEL", risk_profile="MODERE", status="ACTIF")
    second.auth = ClientAuthentication(email="second@profin.ht", password_hash=hash_password("Password!123"), is_active=True)
    db_session.add_all([first, second])
    db_session.flush()
    account = Account(account_number="INV-TEST-001", account_type="INVESTISSEMENT", currency="USD", balance=1000, available_balance=1000, status="ACTIF")
    account.roles.extend([AccountRole(client=first, role="TITULAIRE_PRINCIPAL", is_active=True), AccountRole(client=second, role="MANDATAIRE", is_active=True)])
    private_account = Account(account_number="INV-TEST-002", account_type="INVESTISSEMENT", currency="USD", balance=1000, available_balance=1000, status="ACTIF")
    private_account.roles.append(AccountRole(client=first, role="TITULAIRE_PRINCIPAL", is_active=True))
    htg_account = Account(account_number="INV-TEST-003", account_type="INVESTISSEMENT", currency="HTG", balance=10000, available_balance=10000, status="ACTIF")
    htg_account.roles.extend([AccountRole(client=first, role="TITULAIRE_PRINCIPAL", is_active=True), AccountRole(client=second, role="MANDATAIRE", is_active=True)])
    transfer_destination = Account(account_number="INV-TEST-004", account_type="INVESTISSEMENT", currency="USD", balance=500, available_balance=500, status="ACTIF")
    transfer_destination.roles.extend([AccountRole(client=first, role="TITULAIRE_PRINCIPAL", is_active=True), AccountRole(client=second, role="MANDATAIRE", is_active=True)])
    instrument_type = InstrumentType(code="OBL", name="Obligation", description="Test")
    db_session.add_all([account, private_account, htg_account, transfer_destination, instrument_type])
    db_session.flush()
    instrument = Instrument(code="OBL-TEST-2028", name="Obligation test", issuer="Émetteur test", annual_yield=5.5, issue_date=date(2026, 1, 1), maturity_date=date(2028, 1, 1), nominal_value=1000, minimum_amount=500, currency="USD", interest_frequency="ANNUEL", status="DISPONIBLE", instrument_type_id=instrument_type.id)
    db_session.add(instrument)
    db_session.commit()
    return {"first": first, "second": second, "account": account, "private_account": private_account, "htg_account": htg_account, "transfer_destination": transfer_destination, "instrument": instrument}
