from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.v1.endpoints.serializers import order_dict
from app.core.dependencies import get_current_active_client
from app.db.database import get_db
from app.models.models import Client
from app.schemas.api import InvestmentOrderCreate, OrderStepDecision
from app.services.order_service import InvestmentOrderService

router = APIRouter()


@router.post("/", status_code=status.HTTP_201_CREATED)
def submit_order(payload: InvestmentOrderCreate, client: Client = Depends(get_current_active_client), db: Session = Depends(get_db)):
    try:
        order = InvestmentOrderService.create(db, client.id, payload.account_id, payload.instrument_id, payload.amount, payload.units, payload.client_comment)
        return {"success": True, "message": "Ordre soumis et montant réservé", "order": order_dict(order)}
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/mes-ordres")
def list_orders(limit: int = Query(default=100, ge=1, le=500), client: Client = Depends(get_current_active_client), db: Session = Depends(get_db)):
    orders = InvestmentOrderService.list_for_client(db, client.id)[:limit]
    return {"total": len(orders), "orders": [order_dict(order) for order in orders]}


@router.get("/{order_id}")
def get_order(order_id: int, client: Client = Depends(get_current_active_client), db: Session = Depends(get_db)):
    try:
        return {"order": order_dict(InvestmentOrderService.get(db, order_id, client.id))}
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/{order_id}/steps/{step_code}")
def review_order_step(order_id: int, step_code: str, payload: OrderStepDecision, client: Client = Depends(get_current_active_client), db: Session = Depends(get_db)):
    try:
        order = InvestmentOrderService.review_step(db, order_id, client.id, step_code.upper(), payload.decision, payload.notes)
        return {"success": True, "message": "Étape traitée", "order": order_dict(order)}
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/{order_id}/cancel")
def cancel_order(order_id: int, client: Client = Depends(get_current_active_client), db: Session = Depends(get_db)):
    try:
        order = InvestmentOrderService.cancel(db, order_id, client.id)
        return {"success": True, "message": "Ordre annulé et montant libéré", "order": order_dict(order)}
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
