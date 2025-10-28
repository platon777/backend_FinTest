"""
Endpoints utilisateurs protégés
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.core.dependencies import get_current_active_client
from app.models.models import Client, ClientIndividuel, ClientInstitutionnel, ClientAuthentification
from app.schemas.auth import ClientProfile

router = APIRouter()


@router.get("/me", response_model=ClientProfile)
def get_my_profile(
    current_client: Client = Depends(get_current_active_client),
    db: Session = Depends(get_db)
):
    """
    Récupérer le profil du client connecté

    Nécessite un token JWT valide dans le header Authorization
    """

    # Récupérer l'auth
    auth = db.query(ClientAuthentification).filter(
        ClientAuthentification.ClientID == current_client.ClientID
    ).first()

    # Préparer la réponse
    profile = ClientProfile(
        client_id=current_client.ClientID,
        client_type=current_client.ClientType,
        email=auth.Email,
        statut_client=current_client.StatutClient,
        profil_risque=current_client.ProfilRisque,
        date_creation=current_client.DateCreation
    )

    # Ajouter les infos spécifiques
    if current_client.ClientType == 'INDIVIDUEL':
        individuel = db.query(ClientIndividuel).filter(
            ClientIndividuel.ClientID == current_client.ClientID
        ).first()

        if individuel:
            profile.prenom = individuel.Prenom
            profile.nom = individuel.Nom
            profile.date_naissance = str(individuel.DateNaissance) if individuel.DateNaissance else None
            profile.profession = individuel.Profession

    elif current_client.ClientType == 'INSTITUTIONNEL':
        institutionnel = db.query(ClientInstitutionnel).filter(
            ClientInstitutionnel.ClientID == current_client.ClientID
        ).first()

        if institutionnel:
            profile.nom_entreprise = institutionnel.NomEntreprise
            profile.numero_registre_commerce = institutionnel.NumeroRegistreCommerce

    return profile


@router.get("/me/test")
def test_auth(
    current_client: Client = Depends(get_current_active_client)
):
    """
    Endpoint de test pour vérifier l'authentification
    """
    return {
        "success": True,
        "message": "Vous êtes authentifié!",
        "client_id": current_client.ClientID,
        "client_type": current_client.ClientType
    }
