from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.v1.endpoints.serializers import interest_payment_dict, subscription_dict
from app.core.dependencies import get_current_active_client
from app.db.database import get_db
from app.models.models import Client
from app.schemas.api import SubscriptionCreate
from app.services.subscription_service import SubscriptionService
from app.services.interest_service import InterestService

router = APIRouter()


@router.post("/", status_code=status.HTTP_201_CREATED)
def create_subscription(payload: SubscriptionCreate, client: Client = Depends(get_current_active_client), db: Session = Depends(get_db)):
    try:
        subscription = SubscriptionService.create(db, client.id, payload.account_id, payload.instrument_id, payload.invested_amount, payload.units)
        return {"success": True, "message": "Souscription enregistrée", "souscription": subscription_dict(subscription), "subscription": subscription_dict(subscription)}
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/mes-souscriptions")
def list_subscriptions(client: Client = Depends(get_current_active_client), db: Session = Depends(get_db)):
    subscriptions = [subscription_dict(item) for item in SubscriptionService.list_for_client(db, client.id)]
    return {"total": len(subscriptions), "souscriptions": subscriptions, "subscriptions": subscriptions}


@router.post("/maintenance/maturites")
def generate_maturities(as_of: date | None = Query(default=None), client: Client = Depends(get_current_active_client), db: Session = Depends(get_db)):
    transactions = SubscriptionService.generate_maturity_transactions(db, as_of or date.today(), client.id)
    return {"success": True, "total": len(transactions), "transactions": [transaction_dict(item, db) for item in transactions]}


@router.post("/maintenance/coupons")
def generate_coupons(as_of: date | None = Query(default=None), client: Client = Depends(get_current_active_client), db: Session = Depends(get_db)):
    payments = InterestService.generate_due_payments(db, as_of or date.today(), client.id)
    return {"success": True, "total": len(payments), "payments": [interest_payment_dict(item) for item in payments]}


@router.get("/mes-coupons")
def list_coupons(subscription_id: int | None = Query(default=None), client: Client = Depends(get_current_active_client), db: Session = Depends(get_db)):
    payments = InterestService.list_for_client(db, client.id, subscription_id)
    return {"total": len(payments), "coupons": [interest_payment_dict(item) for item in payments]}


@router.get("/{subscription_id}")
def get_subscription(subscription_id: int, client: Client = Depends(get_current_active_client), db: Session = Depends(get_db)):
    try:
        subscription = SubscriptionService.get_for_client(db, subscription_id, client.id)
        if not subscription:
            raise HTTPException(status_code=404, detail="Souscription introuvable")
        return subscription_dict(subscription)
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc


@router.post("/{subscription_id}/racheter")
def redeem_subscription(subscription_id: int, client: Client = Depends(get_current_active_client), db: Session = Depends(get_db)):
    try:
        subscription = SubscriptionService.redeem(db, subscription_id, client.id)
        return {"success": True, "message": "Souscription rachetée", "souscription": subscription_dict(subscription)}
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
