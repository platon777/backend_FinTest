from decimal import Decimal

from sqlalchemy import text

from app.db.reporting import REPORTING_OBJECTS, reporting_objects_down_sql
from app.services.subscription_service import SubscriptionService


def login(client, email):
    response = client.post("/api/v1/auth/login", json={"email": email, "password": "Password!123"})
    assert response.status_code == 200, response.text
    return response.json()


def headers(session):
    return {"Authorization": f"Bearer {session['tokens']['access_token']}"}


def test_client_report_is_currency_aware_and_exposes_real_business_sections(client_app, demo_data, db_session):
    SubscriptionService.create(db_session, demo_data["first"].id, demo_data["account"].id, demo_data["instrument"].id, Decimal("500"))
    session = login(client_app, "first@profin.ht")

    response = client_app.get("/api/v1/dashboard/rapports/client", headers=headers(session))

    assert response.status_code == 200, response.text
    payload = response.json()
    assert {"summary_by_currency", "allocation", "positions", "order_pipeline", "maturities", "cashflow", "alerts"} <= payload.keys()
    usd = next(item for item in payload["summary_by_currency"] if item["currency"] == "USD")
    assert Decimal(str(usd["invested"])) == Decimal("500.00")
    assert usd["active_positions"] == 1


def test_backoffice_report_is_scoped_to_mandataire_and_shows_order_queue(client_app, demo_data):
    first = login(client_app, "first@profin.ht")
    submitted = client_app.post(
        "/api/v1/ordres/",
        headers=headers(first),
        json={"account_id": demo_data["account"].id, "instrument_id": demo_data["instrument"].id, "amount": "500"},
    )
    assert submitted.status_code == 201, submitted.text

    second = login(client_app, "second@profin.ht")
    response = client_app.get("/api/v1/dashboard/rapports/back-office", headers=headers(second))
    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["kpis"]["orders_in_review"] == 1
    assert payload["workflow"][0]["step"] == "CONFORMITE"
    assert payload["queue"][0]["queue_type"] == "INVESTMENT_ORDER"

    forbidden = client_app.get("/api/v1/dashboard/rapports/back-office", headers=headers(first))
    assert forbidden.status_code == 403


def test_postgresql_reporting_views_and_function_are_installable(db_session):
    try:
        for statement in REPORTING_OBJECTS:
            db_session.execute(text(statement))
        db_session.commit()
        assert db_session.scalar(text("SELECT profin_order_next_step(NULL)")) is None
        assert db_session.scalar(text("SELECT COUNT(*) FROM vw_reporting_client_positions")) == 0
        assert db_session.scalar(text("SELECT COUNT(*) FROM vw_reporting_order_pipeline")) == 0
    finally:
        for statement in reporting_objects_down_sql():
            db_session.execute(text(statement))
        db_session.commit()
