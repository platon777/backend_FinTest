"""
Service Profil - Gestion du profil client (KYC)
"""
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Dict, Any, Optional
from app.models.models import Client, ClientIndividuel, ClientInstitutionnel, AdresseClient, ContactClient
from datetime import datetime
from decimal import Decimal


class ProfilService:
    """Service de gestion du profil client"""

    @staticmethod
    def get_profil_client(db: Session, client_id: int) -> Dict[str, Any]:
        """
        Récupérer le profil complet d'un client
        Source: vw_ProfilClient

        Args:
            db: Session SQLAlchemy
            client_id: ID du client

        Returns:
            Dict avec toutes les informations du profil
        """
        query = text("""
            SELECT
                c.ClientID,
                c.ClientType,
                c.ProfilRisque,
                c.StatutClient,
                c.DateCreation,
                -- CLIENT INDIVIDUEL
                ci.Prenom,
                ci.Nom,
                CONCAT(ci.Prenom, ' ', ci.Nom) AS NomComplet,
                ci.DateNaissance,
                ci.Nationalite,
                ci.TypePieceIdentite,
                ci.NumeroPieceIdentite,
                ci.Profession,
                ci.SourceRevenus,
                ci.RevenuAnnuelEstime,
                -- CLIENT INSTITUTIONNEL
                cin.NomEntreprise,
                cin.NumeroRegistreCommerce,
                cin.FormeJuridique,
                cin.Secteur,
                cin.DateCreationEntreprise,
                cin.ChiffreAffairesAnnuel,
                cin.NomRepresentantLegal,
                -- ADRESSE PRINCIPALE
                adr.AdresseLigne1,
                adr.AdresseLigne2,
                adr.Ville,
                adr.CodePostal,
                adr.Pays,
                -- CONTACT PRINCIPAL EMAIL
                ctEmail.Valeur AS Email,
                -- CONTACT PRINCIPAL TÉLÉPHONE
                ctTel.Valeur AS Telephone,
                -- AUTHENTIFICATION
                auth.Email AS EmailConnexion,
                auth.DateDerniereConnexion
            FROM Clients c
            LEFT JOIN ClientsIndividuels ci ON c.ClientID = ci.ClientID
            LEFT JOIN ClientsInstitutionnels cin ON c.ClientID = cin.ClientID
            LEFT JOIN AdressesClients adr ON c.ClientID = adr.ClientID AND adr.EstPrincipale = 1
            LEFT JOIN ContactsClients ctEmail ON c.ClientID = ctEmail.ClientID
                AND ctEmail.TypeContact = 'EMAIL' AND ctEmail.EstPrincipal = 1
            LEFT JOIN ContactsClients ctTel ON c.ClientID = ctTel.ClientID
                AND ctTel.TypeContact IN ('TELEPHONE', 'MOBILE') AND ctTel.EstPrincipal = 1
            LEFT JOIN ClientsAuthentification auth ON c.ClientID = auth.ClientID
            WHERE c.ClientID = :client_id
        """)

        result = db.execute(query, {"client_id": client_id}).fetchone()

        if not result:
            raise ValueError("Client introuvable")

        # Construire la réponse
        profil = {
            "client_id": result.ClientID,
            "client_type": result.ClientType,
            "nom_complet": result.NomComplet if result.NomComplet else result.NomEntreprise,
            "email": result.EmailConnexion,
            "telephone": result.Telephone,
            "statut_client": result.StatutClient,
            "date_creation": result.DateCreation,
            "derniere_connexion": result.DateDerniereConnexion
        }

        # Adresse
        if result.AdresseLigne1:
            adresse_complete = result.AdresseLigne1
            if result.AdresseLigne2:
                adresse_complete += ", " + result.AdresseLigne2
            adresse_complete += f", {result.CodePostal} {result.Ville}, {result.Pays}"

            profil["adresse"] = {
                "ligne1": result.AdresseLigne1,
                "ligne2": result.AdresseLigne2,
                "ville": result.Ville,
                "code_postal": result.CodePostal,
                "pays": result.Pays,
                "complete": adresse_complete
            }
        else:
            profil["adresse"] = None

        # Profil investisseur
        statut_map = {
            "INDIVIDUEL": "Personne physique",
            "INSTITUTIONNEL": "Personne morale"
        }

        risque_map = {
            "CONSERVATEUR": "Conservateur",
            "MODERE": "Modéré",
            "AGRESSIF": "Agressif"
        }

        # Déterminer horizon d'investissement (simplifié)
        horizon = "Moyen terme"  # Valeur par défaut

        # Déterminer tranche de revenu
        revenu_annuel = None
        if result.ClientType == "INDIVIDUEL" and result.RevenuAnnuelEstime:
            revenu = float(result.RevenuAnnuelEstime)
            if revenu < 25000:
                revenu_annuel = "0-25k USD"
            elif revenu < 50000:
                revenu_annuel = "25k-50k USD"
            elif revenu < 75000:
                revenu_annuel = "50k-75k USD"
            elif revenu < 100000:
                revenu_annuel = "75k-100k USD"
            else:
                revenu_annuel = "100k+ USD"

        profil["profil_investisseur"] = {
            "statut": statut_map.get(result.ClientType, result.ClientType),
            "niveau_risque": risque_map.get(result.ProfilRisque, result.ProfilRisque),
            "horizon_investissement": horizon,
            "revenu_annuel": revenu_annuel
        }

        # Informations spécifiques selon le type
        if result.ClientType == "INDIVIDUEL":
            profil["informations_individuel"] = {
                "prenom": result.Prenom,
                "nom": result.Nom,
                "date_naissance": result.DateNaissance,
                "nationalite": result.Nationalite,
                "type_identite": result.TypePieceIdentite,
                "numero_identite": result.NumeroPieceIdentite,
                "profession": result.Profession,
                "source_revenus": result.SourceRevenus,
                "revenu_annuel_estime": Decimal(str(result.RevenuAnnuelEstime)) if result.RevenuAnnuelEstime else None
            }
            profil["informations_institutionnel"] = None
        else:
            profil["informations_individuel"] = None
            profil["informations_institutionnel"] = {
                "nom_entreprise": result.NomEntreprise,
                "numero_registre_commerce": result.NumeroRegistreCommerce,
                "forme_juridique": result.FormeJuridique,
                "secteur": result.Secteur,
                "date_creation_entreprise": result.DateCreationEntreprise,
                "chiffre_affaires_annuel": Decimal(str(result.ChiffreAffairesAnnuel)) if result.ChiffreAffairesAnnuel else None,
                "nom_representant_legal": result.NomRepresentantLegal
            }

        return profil

    @staticmethod
    def update_profil(
        db: Session,
        client_id: int,
        telephone: Optional[str] = None,
        adresse_ligne1: Optional[str] = None,
        adresse_ligne2: Optional[str] = None,
        ville: Optional[str] = None,
        code_postal: Optional[str] = None,
        pays: Optional[str] = None,
        profession: Optional[str] = None,
        source_revenus: Optional[str] = None
    ) -> bool:
        """
        Mettre à jour le profil client

        Args:
            db: Session SQLAlchemy
            client_id: ID du client
            **kwargs: Champs à mettre à jour

        Returns:
            True si la mise à jour a réussi
        """
        # Récupérer le client
        client = db.query(Client).filter(Client.ClientID == client_id).first()
        if not client:
            raise ValueError("Client introuvable")

        # Mettre à jour le téléphone
        if telephone:
            # Trouver le contact principal
            contact = db.query(ContactClient).filter(
                ContactClient.ClientID == client_id,
                ContactClient.TypeContact.in_(['TELEPHONE', 'MOBILE']),
                ContactClient.EstPrincipal == True
            ).first()

            if contact:
                contact.Valeur = telephone
            else:
                # Créer un nouveau contact
                new_contact = ContactClient(
                    ClientID=client_id,
                    TypeContact='MOBILE',
                    Valeur=telephone,
                    EstPrincipal=True,
                    EstVerifie=False
                )
                db.add(new_contact)

        # Mettre à jour l'adresse
        if any([adresse_ligne1, adresse_ligne2, ville, code_postal, pays]):
            # Trouver l'adresse principale
            adresse = db.query(AdresseClient).filter(
                AdresseClient.ClientID == client_id,
                AdresseClient.EstPrincipale == True
            ).first()

            if adresse:
                if adresse_ligne1:
                    adresse.AdresseLigne1 = adresse_ligne1
                if adresse_ligne2:
                    adresse.AdresseLigne2 = adresse_ligne2
                if ville:
                    adresse.Ville = ville
                if code_postal:
                    adresse.CodePostal = code_postal
                if pays:
                    adresse.Pays = pays
            else:
                # Créer une nouvelle adresse
                new_adresse = AdresseClient(
                    ClientID=client_id,
                    TypeAdresse='DOMICILE',
                    AdresseLigne1=adresse_ligne1,
                    AdresseLigne2=adresse_ligne2,
                    Ville=ville,
                    CodePostal=code_postal,
                    Pays=pays,
                    EstPrincipale=True
                )
                db.add(new_adresse)

        # Mettre à jour les infos client individuel
        if client.ClientType == "INDIVIDUEL" and (profession or source_revenus):
            individuel = db.query(ClientIndividuel).filter(
                ClientIndividuel.ClientID == client_id
            ).first()

            if individuel:
                if profession:
                    individuel.Profession = profession
                if source_revenus:
                    individuel.SourceRevenus = source_revenus

        # Mettre à jour la date de dernière mise à jour
        client.DerniereMiseAJour = datetime.utcnow()

        db.commit()
        return True
