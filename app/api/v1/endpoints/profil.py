"""
Endpoints Profil - Gestion du profil client (KYC)
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.core.dependencies import get_current_active_client
from app.models.models import Client
from app.schemas.profil import (
    ProfilClientResponse,
    ProfilUpdateRequest,
    ProfilUpdateResponse
)
from app.services.profil_service import ProfilService

router = APIRouter()


@router.get("/", response_model=ProfilClientResponse)
def get_profil(
    current_client: Client = Depends(get_current_active_client),
    db: Session = Depends(get_db)
):
    """
    Récupérer le profil complet du client connecté

    **Corresponds à l'écran "Profil KYC" avec:**

    **Informations personnelles:**
    - Nom complet: Jean Dupont
    - Type de client: Individuel
    - Adresse email: jean.dupont@email.com
    - Numéro de téléphone: +33 6 12 34 56 78
    - Adresse: 123 Rue de la République, 75001 Paris, France

    **Profil investisseur:**
    - Statut: Personne physique
    - Niveau de risque accepté: Modéré
    - Horizon d'investissement: Moyen terme
    - Revenu annuel: 50k-75k USD
    """
    try:
        profil = ProfilService.get_profil_client(
            db=db,
            client_id=current_client.ClientID
        )
        return ProfilClientResponse(**profil)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la récupération du profil: {str(e)}"
        )


@router.patch("/", response_model=ProfilUpdateResponse)
def update_profil(
    data: ProfilUpdateRequest,
    current_client: Client = Depends(get_current_active_client),
    db: Session = Depends(get_db)
):
    """
    Mettre à jour le profil du client

    Permet de mettre à jour:
    - Téléphone
    - Adresse (ligne1, ligne2, ville, code postal, pays)
    - Profession (pour les clients individuels)
    - Source de revenus (pour les clients individuels)
    """
    try:
        success = ProfilService.update_profil(
            db=db,
            client_id=current_client.ClientID,
            telephone=data.telephone,
            adresse_ligne1=data.adresse_ligne1,
            adresse_ligne2=data.adresse_ligne2,
            ville=data.ville,
            code_postal=data.code_postal,
            pays=data.pays,
            profession=data.profession,
            source_revenus=data.source_revenus
        )

        if success:
            return ProfilUpdateResponse(
                success=True,
                message="Profil mis à jour avec succès"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Erreur lors de la mise à jour du profil"
            )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la mise à jour du profil: {str(e)}"
        )
