from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_active_client
from app.db.database import get_db
from app.models.models import Client

router = APIRouter()


@router.get("/me")
def get_my_profile(client: Client = Depends(get_current_active_client), db: Session = Depends(get_db)):
    individual = client.individual_profile
    institutional = client.institutional_profile
    return {
        "client_id": client.id, "client_type": client.client_type, "email": client.auth.email,
        "status": client.status, "risk_profile": client.risk_profile,
        "prenom": individual.first_name if individual else None, "nom": individual.last_name if individual else None,
        "nom_entreprise": institutional.company_name if institutional else None,
    }
