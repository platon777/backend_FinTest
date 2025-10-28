"""
Service pour la gestion des Instruments Financiers
"""
from sqlalchemy.orm import Session
from app.models.models import TypeInstrument, Instrument
from typing import List, Optional


class InstrumentsService:
    """Service de gestion des instruments financiers"""

    @staticmethod
    def get_all_instruments(db: Session, statut: Optional[str] = None) -> List[Instrument]:
        """Récupérer tous les instruments"""
        query = db.query(Instrument)
        if statut:
            query = query.filter(Instrument.StatutInstrument == statut)
        return query.all()

    @staticmethod
    def get_instrument_by_id(db: Session, instrument_id: int) -> Optional[Instrument]:
        """Récupérer un instrument par ID"""
        return db.query(Instrument).filter(Instrument.InstrumentID == instrument_id).first()

    @staticmethod
    def get_instruments_disponibles(db: Session) -> List[Instrument]:
        """Récupérer les instruments disponibles pour souscription"""
        return db.query(Instrument).filter(
            Instrument.StatutInstrument == 'DISPONIBLE'
        ).all()

    @staticmethod
    def get_types_instruments(db: Session) -> List[TypeInstrument]:
        """Récupérer tous les types d'instruments"""
        return db.query(TypeInstrument).all()

    @staticmethod
    def creer_type_instrument(db: Session, code: str, nom: str, description: str = None) -> TypeInstrument:
        """Créer un nouveau type d'instrument"""
        existing = db.query(TypeInstrument).filter(TypeInstrument.Code == code).first()
        if existing:
            raise ValueError(f"Le type d'instrument {code} existe déjà")

        type_instrument = TypeInstrument(Code=code, Nom=nom, Description=description)
        db.add(type_instrument)
        db.commit()
        db.refresh(type_instrument)
        return type_instrument

    @staticmethod
    def creer_instrument(db: Session, **kwargs) -> Instrument:
        """Créer un nouvel instrument"""
        existing = db.query(Instrument).filter(Instrument.Code == kwargs.get('Code')).first()
        if existing:
            raise ValueError(f"L'instrument {kwargs.get('Code')} existe déjà")

        instrument = Instrument(**kwargs)
        db.add(instrument)
        db.commit()
        db.refresh(instrument)
        return instrument

    @staticmethod
    def mettre_a_jour_instrument(db: Session, instrument_id: int, **kwargs) -> Instrument:
        """Mettre à jour un instrument"""
        instrument = db.query(Instrument).filter(Instrument.InstrumentID == instrument_id).first()
        if not instrument:
            raise ValueError("Instrument introuvable")

        for key, value in kwargs.items():
            if value is not None and hasattr(instrument, key):
                setattr(instrument, key, value)

        db.commit()
        db.refresh(instrument)
        return instrument
