"""
Endpoints pour la gestion des Instruments Financiers
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.core.dependencies import get_current_active_client
from app.models.models import Client
from app.schemas.instruments import *
from app.services.instruments_service import InstrumentsService

router = APIRouter()


@router.get("/disponibles", response_model=InstrumentsDisponiblesResponse)
def get_instruments_disponibles(
    current_client: Client = Depends(get_current_active_client),
    db: Session = Depends(get_db)
):
    """Récupérer tous les instruments disponibles pour investissement"""
    try:
        instruments = InstrumentsService.get_instruments_disponibles(db)
        return InstrumentsDisponiblesResponse(
            total=len(instruments),
            instruments=[InstrumentDetail.from_orm(i) for i in instruments]
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/", response_model=InstrumentsListResponse)
def get_all_instruments(
    statut: Optional[str] = None,
    current_client: Client = Depends(get_current_active_client),
    db: Session = Depends(get_db)
):
    """Récupérer tous les instruments"""
    try:
        instruments = InstrumentsService.get_all_instruments(db, statut)
        return InstrumentsListResponse(
            total=len(instruments),
            instruments=[InstrumentResponse.from_orm(i) for i in instruments]
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/{instrument_id}", response_model=InstrumentDetail)
def get_instrument(
    instrument_id: int,
    current_client: Client = Depends(get_current_active_client),
    db: Session = Depends(get_db)
):
    """Récupérer les détails d'un instrument"""
    try:
        instrument = InstrumentsService.get_instrument_by_id(db, instrument_id)
        if not instrument:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Instrument introuvable")

        return InstrumentDetail.from_orm(instrument)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/types/", response_model=List[TypeInstrumentResponse])
def get_types_instruments(
    current_client: Client = Depends(get_current_active_client),
    db: Session = Depends(get_db)
):
    """Récupérer tous les types d'instruments"""
    try:
        types = InstrumentsService.get_types_instruments(db)
        return [TypeInstrumentResponse.from_orm(t) for t in types]
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
