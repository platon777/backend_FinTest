from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.core.dependencies import get_current_active_client
from app.db.database import get_db
from app.models.models import Client, Instrument
from app.api.v1.endpoints.serializers import instrument_dict

router = APIRouter()


@router.get("/")
def list_instruments(status_filter: str | None = Query(default=None, alias="status"), currency: str | None = None, client: Client = Depends(get_current_active_client), db: Session = Depends(get_db)):
    query = select(Instrument).options(joinedload(Instrument.instrument_type)).order_by(Instrument.maturity_date)
    if status_filter:
        query = query.where(Instrument.status == status_filter.upper())
    if currency:
        query = query.where(Instrument.currency == currency.upper())
    instruments = [instrument_dict(item) for item in db.scalars(query).all()]
    return {"total": len(instruments), "instruments": instruments}


@router.get("/{instrument_id}")
def get_instrument(instrument_id: int, client: Client = Depends(get_current_active_client), db: Session = Depends(get_db)):
    instrument = db.scalar(select(Instrument).where(Instrument.id == instrument_id).options(joinedload(Instrument.instrument_type)))
    if not instrument:
        raise HTTPException(status_code=404, detail="Instrument introuvable")
    return instrument_dict(instrument)
