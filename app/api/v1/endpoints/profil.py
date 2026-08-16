from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_active_client
from app.db.database import get_db
from app.models.models import Client, ClientAddress, ClientContact
from app.schemas.api import ProfileUpdate

router = APIRouter()


def profile_dict(client: Client) -> dict:
    individual = client.individual_profile
    institutional = client.institutional_profile
    address = next((item for item in client.addresses if item.is_primary), client.addresses[0] if client.addresses else None)
    phone = next((item.value for item in client.contacts if item.contact_type == "TELEPHONE" and item.is_primary), None)
    return {
        "client_id": client.id, "client_type": client.client_type, "email": client.auth.email,
        "status": client.status, "risk_profile": client.risk_profile,
        "full_name": f"{individual.first_name} {individual.last_name}" if individual else institutional.company_name,
        "phone": phone,
        "address": {"line1": address.line1, "city": address.city, "postal_code": address.postal_code, "country": address.country} if address else None,
        "individual": {"first_name": individual.first_name, "last_name": individual.last_name, "birth_date": individual.birth_date, "nationality": individual.nationality, "identity_type": individual.identity_type, "identity_number": individual.identity_number, "profession": individual.profession, "income_source": individual.income_source, "estimated_annual_income": individual.estimated_annual_income} if individual else None,
        "institutional": {"company_name": institutional.company_name, "registration_number": institutional.registration_number, "legal_form": institutional.legal_form, "sector": institutional.sector, "annual_revenue": institutional.annual_revenue, "legal_representative": institutional.legal_representative} if institutional else None,
    }


@router.get("")
def get_profile(client: Client = Depends(get_current_active_client)):
    return profile_dict(client)


@router.patch("")
def update_profile(payload: ProfileUpdate, client: Client = Depends(get_current_active_client), db: Session = Depends(get_db)):
    address = next((item for item in client.addresses if item.is_primary), None)
    if payload.adresse_ligne1 or payload.ville or payload.code_postal:
        if not address:
            address = ClientAddress(client_id=client.id, line1=payload.adresse_ligne1 or "", city=payload.ville or "Port-au-Prince", postal_code=payload.code_postal, country="Haïti", is_primary=True)
            db.add(address)
        else:
            if payload.adresse_ligne1 is not None: address.line1 = payload.adresse_ligne1
            if payload.ville is not None: address.city = payload.ville
            if payload.code_postal is not None: address.postal_code = payload.code_postal
    if payload.telephone:
        contact = next((item for item in client.contacts if item.contact_type == "TELEPHONE" and item.is_primary), None)
        if not contact:
            db.add(ClientContact(client_id=client.id, contact_type="TELEPHONE", value=payload.telephone, is_primary=True))
        else:
            contact.value = payload.telephone
    db.commit()
    db.refresh(client)
    return profile_dict(client)
