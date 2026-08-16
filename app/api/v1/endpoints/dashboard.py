from decimal import Decimal

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.v1.endpoints.serializers import account_dict, subscription_dict, transaction_dict
from app.core.dependencies import get_current_active_client
from app.db.database import get_db
from app.models.models import Account, AccountRole, Client, Subscription, Transaction

router = APIRouter()


def client_accounts(db: Session, client_id: int) -> list[Account]:
    return list(db.scalars(select(Account).join(AccountRole, AccountRole.account_id == Account.id).where(AccountRole.client_id == client_id, AccountRole.is_active.is_(True))).unique())


@router.get("/overview")
def overview(client: Client = Depends(get_current_active_client), db: Session = Depends(get_db)):
    accounts = client_accounts(db, client.id)
    subscriptions = list(db.scalars(select(Subscription).where(Subscription.account_id.in_([item.id for item in accounts]), Subscription.status == "ACTIVE")))
    total_invested = sum((Decimal(item.invested_amount) for item in subscriptions), Decimal("0"))
    total_value = sum((Decimal(item.current_value) for item in subscriptions), Decimal("0"))
    total_return = total_value - total_invested
    percentage = (total_return / total_invested * 100) if total_invested else Decimal("0")
    # Les soldes peuvent exister dans plusieurs devises. Pour les métriques
    # de portefeuille, utiliser la devise des positions plutôt que l'ordre
    # arbitraire des comptes; les liquidités détaillées restent exposées par
    # devise dans la liste des comptes.
    currency = next((item.instrument.currency for item in subscriptions if item.instrument), accounts[0].currency if accounts else "USD")
    return {
        "total_value": total_value, "total_invested": total_invested, "total_return": total_return,
        "return_percentage": percentage.quantize(Decimal("0.01")), "active_subscriptions": len(subscriptions),
        "accounts": [account_dict(item, db.scalar(select(AccountRole.role).where(AccountRole.account_id == item.id, AccountRole.client_id == client.id, AccountRole.is_active.is_(True)))) for item in accounts],
        "currency": currency,
        "valeur_totale": total_value, "rendement_total": total_return, "pourcentage_rendement": percentage.quantize(Decimal("0.01")),
    }


@router.get("/transactions/recentes")
def recent_transactions(limit: int = Query(default=5, ge=1, le=20), client: Client = Depends(get_current_active_client), db: Session = Depends(get_db)):
    account_ids = select(AccountRole.account_id).where(AccountRole.client_id == client.id, AccountRole.is_active.is_(True))
    rows = db.scalars(select(Transaction).where((Transaction.source_account_id.in_(account_ids)) | (Transaction.destination_account_id.in_(account_ids))).order_by(Transaction.created_at.desc()).limit(limit)).all()
    result = [transaction_dict(item, db) for item in rows]
    return {"total": len(result), "transactions": result}


@router.get("/investissements")
def active_investments(client: Client = Depends(get_current_active_client), db: Session = Depends(get_db)):
    account_ids = select(AccountRole.account_id).where(AccountRole.client_id == client.id, AccountRole.is_active.is_(True))
    rows = db.scalars(select(Subscription).where(Subscription.account_id.in_(account_ids), Subscription.status == "ACTIVE").order_by(Subscription.effective_maturity_date)).all()
    result = [subscription_dict(item) for item in rows]
    return {"total": len(result), "investissements": result, "investments": result}


@router.get("/statistiques/mensuelles")
def monthly_statistics(mois: int = Query(default=6, ge=1, le=24), client: Client = Depends(get_current_active_client), db: Session = Depends(get_db)):
    accounts = client_accounts(db, client.id)
    subscriptions = list(db.scalars(select(Subscription).where(Subscription.account_id.in_([item.id for item in accounts])))) if accounts else []
    value = sum((Decimal(item.current_value) for item in subscriptions), Decimal("0"))
    result = [{"mois": index + 1, "valeur_portefeuille": value, "nombre_souscriptions": len(subscriptions)} for index in range(mois)]
    return {"periodes": result}


@router.get("/complet")
def complete_dashboard(client: Client = Depends(get_current_active_client), db: Session = Depends(get_db)):
    return {
        "overview": overview(client, db),
        "transactions_recentes": recent_transactions(5, client, db),
        "investissements_actifs": active_investments(client, db),
        "statistiques_mensuelles": monthly_statistics(6, client, db),
    }
