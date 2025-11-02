"""
Schemas Pydantic pour le Profil Client (KYC)
"""
from pydantic import BaseModel, ConfigDict, EmailStr
from typing import Optional
from datetime import date, datetime
from decimal import Decimal


# ============================================================================
# ADRESSE
# ============================================================================

class AdresseInfo(BaseModel):
    """Informations d'adresse"""
    ligne1: Optional[str]
    ligne2: Optional[str]
    ville: Optional[str]
    code_postal: Optional[str]
    pays: Optional[str]
    complete: Optional[str]  # Adresse formatée

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# PROFIL INVESTISSEUR
# ============================================================================

class ProfilInvestisseur(BaseModel):
    """Profil investisseur du client"""
    statut: str  # "Personne physique" ou "Personne morale"
    niveau_risque: str  # "Conservateur", "Modéré", "Agressif"
    horizon_investissement: str  # "Court terme", "Moyen terme", "Long terme"
    revenu_annuel: Optional[str]  # "50k-75k USD", etc.

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# INFORMATIONS CLIENT INDIVIDUEL
# ============================================================================

class InformationsIndividuel(BaseModel):
    """Informations spécifiques client individuel"""
    prenom: str
    nom: str
    date_naissance: date
    nationalite: Optional[str]
    type_identite: Optional[str]
    numero_identite: str
    profession: Optional[str]
    source_revenus: Optional[str]
    revenu_annuel_estime: Optional[Decimal]

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# INFORMATIONS CLIENT INSTITUTIONNEL
# ============================================================================

class InformationsInstitutionnel(BaseModel):
    """Informations spécifiques client institutionnel"""
    nom_entreprise: str
    numero_registre_commerce: str
    forme_juridique: Optional[str]
    secteur: Optional[str]
    date_creation_entreprise: Optional[date]
    chiffre_affaires_annuel: Optional[Decimal]
    nom_representant_legal: Optional[str]

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# PROFIL CLIENT COMPLET
# ============================================================================

class ProfilClientResponse(BaseModel):
    """
    Profil client complet
    Source: vw_ProfilClient

    Corresponds à l'écran "Profil KYC" avec:
    - Informations personnelles
    - Adresse
    - Contacts
    - Profil investisseur
    """
    client_id: int
    client_type: str  # "INDIVIDUEL" ou "INSTITUTIONNEL"
    nom_complet: Optional[str]  # Prenom + Nom ou NomEntreprise
    email: str
    telephone: Optional[str]

    # Adresse
    adresse: Optional[AdresseInfo]

    # Profil investisseur
    profil_investisseur: ProfilInvestisseur

    # Informations spécifiques selon le type
    informations_individuel: Optional[InformationsIndividuel]
    informations_institutionnel: Optional[InformationsInstitutionnel]

    # Statut
    statut_client: str
    date_creation: datetime
    derniere_connexion: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# MISE À JOUR PROFIL
# ============================================================================

class ProfilUpdateRequest(BaseModel):
    """Requête de mise à jour du profil"""
    telephone: Optional[str] = None
    adresse_ligne1: Optional[str] = None
    adresse_ligne2: Optional[str] = None
    ville: Optional[str] = None
    code_postal: Optional[str] = None
    pays: Optional[str] = None
    profession: Optional[str] = None
    source_revenus: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class ProfilUpdateResponse(BaseModel):
    """Réponse de mise à jour du profil"""
    success: bool
    message: str

    model_config = ConfigDict(from_attributes=True)
