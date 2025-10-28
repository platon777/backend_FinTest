"""
Service d'authentification - VERSION SIMPLE
"""
from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.models.models import Client, ClientIndividuel, ClientInstitutionnel, ClientAuthentification, RefreshToken, ContactClient
from app.core.security import verify_password, get_password_hash, create_access_token, create_refresh_token, decode_token
from app.core.config import settings


class AuthService:
    """Service gérant l'authentification"""

    @staticmethod
    def register_client(
        db: Session,
        client_type: str,
        email: str,
        password: str,
        # Individuel
        prenom: Optional[str] = None,
        nom: Optional[str] = None,
        date_naissance: Optional[str] = None,
        numero_piece_identite: Optional[str] = None,
        # Institutionnel
        nom_entreprise: Optional[str] = None,
        numero_registre_commerce: Optional[str] = None,
        nom_representant_legal: Optional[str] = None
    ):
        """Inscrire un nouveau client"""

        # Vérifier si l'email existe déjà
        existing_auth = db.query(ClientAuthentification).filter(
            ClientAuthentification.Email == email
        ).first()

        if existing_auth:
            raise ValueError("Cet email est déjà utilisé")

        # Créer le client
        client = Client(
            ClientType=client_type,
            StatutClient='ACTIF'
        )
        db.add(client)
        db.flush()  # Pour obtenir le ClientID

        # Créer le profil selon le type
        if client_type == 'INDIVIDUEL':
            if not all([prenom, nom, date_naissance, numero_piece_identite]):
                raise ValueError("Informations manquantes pour un client individuel")

            # Vérifier numéro pièce unique
            existing_piece = db.query(ClientIndividuel).filter(
                ClientIndividuel.NumeroPieceIdentite == numero_piece_identite
            ).first()
            if existing_piece:
                raise ValueError("Ce numéro de pièce d'identité existe déjà")

            client_individuel = ClientIndividuel(
                ClientID=client.ClientID,
                Prenom=prenom,
                Nom=nom,
                DateNaissance=date_naissance,
                NumeroPieceIdentite=numero_piece_identite
            )
            db.add(client_individuel)

        elif client_type == 'INSTITUTIONNEL':
            if not all([nom_entreprise, numero_registre_commerce, nom_representant_legal]):
                raise ValueError("Informations manquantes pour un client institutionnel")

            # Vérifier registre commerce unique
            existing_registre = db.query(ClientInstitutionnel).filter(
                ClientInstitutionnel.NumeroRegistreCommerce == numero_registre_commerce
            ).first()
            if existing_registre:
                raise ValueError("Ce numéro de registre de commerce existe déjà")

            client_inst = ClientInstitutionnel(
                ClientID=client.ClientID,
                NomEntreprise=nom_entreprise,
                NumeroRegistreCommerce=numero_registre_commerce,
                NomRepresentantLegal=nom_representant_legal
            )
            db.add(client_inst)

        # Créer l'authentification
        password_hash = get_password_hash(password)
        auth = ClientAuthentification(
            ClientID=client.ClientID,
            Email=email,
            PasswordHash=password_hash,
            EstActif=True
        )
        db.add(auth)

        # Ajouter l'email comme contact
        contact = ContactClient(
            ClientID=client.ClientID,
            TypeContact='EMAIL',
            Valeur=email,
            EstPrincipal=True,
            EstVerifie=False
        )
        db.add(contact)

        db.commit()
        db.refresh(client)

        return client

    @staticmethod
    def login(db: Session, email: str, password: str, ip_address: Optional[str] = None):
        """Connexion d'un client"""

        # Récupérer l'authentification
        auth = db.query(ClientAuthentification).filter(
            ClientAuthentification.Email == email
        ).first()

        if not auth:
            raise ValueError("Email ou mot de passe incorrect")

        if not auth.EstActif:
            raise ValueError("Compte désactivé")

        # Vérifier le mot de passe
        if not verify_password(password, auth.PasswordHash):
            raise ValueError("Email ou mot de passe incorrect")

        # Récupérer le client complet
        client = db.query(Client).filter(Client.ClientID == auth.ClientID).first()

        if client.StatutClient != 'ACTIF':
            raise ValueError("Compte client suspendu ou fermé")

        # Générer les tokens JWT
        token_data = {
            "sub": str(auth.ClientID),
            "email": email,
            "client_type": client.ClientType
        }

        access_token = create_access_token(token_data)
        refresh_token_str = create_refresh_token(token_data)

        # Stocker le refresh token
        refresh_token = RefreshToken(
            ClientID=auth.ClientID,
            Token=refresh_token_str,
            DateExpiration=datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
            AdresseIP=ip_address
        )
        db.add(refresh_token)

        # Mettre à jour la dernière connexion
        auth.DateDerniereConnexion = datetime.utcnow()

        db.commit()

        return {
            "access_token": access_token,
            "refresh_token": refresh_token_str,
            "client": client,
            "auth": auth
        }

    @staticmethod
    def refresh_access_token(db: Session, refresh_token_str: str):
        """Rafraîchir l'access token"""

        # Vérifier que le refresh token existe
        refresh_token = db.query(RefreshToken).filter(
            RefreshToken.Token == refresh_token_str
        ).first()

        if not refresh_token:
            raise ValueError("Refresh token invalide")

        if refresh_token.EstRevoque:
            raise ValueError("Refresh token révoqué")

        if refresh_token.DateExpiration < datetime.utcnow():
            raise ValueError("Refresh token expiré")

        # Décoder le token
        payload = decode_token(refresh_token_str)
        if not payload:
            raise ValueError("Refresh token invalide")

        # Récupérer le client
        client = db.query(Client).filter(
            Client.ClientID == refresh_token.ClientID
        ).first()

        auth = db.query(ClientAuthentification).filter(
            ClientAuthentification.ClientID == client.ClientID
        ).first()

        # Générer un nouveau access token
        token_data = {
            "sub": str(client.ClientID),
            "email": auth.Email,
            "client_type": client.ClientType
        }

        access_token = create_access_token(token_data)

        return {
            "access_token": access_token,
            "refresh_token": refresh_token_str
        }

    @staticmethod
    def get_current_client(db: Session, token: str):
        """Récupérer le client à partir du token"""

        payload = decode_token(token)
        if not payload:
            raise ValueError("Token invalide")

        client_id = payload.get("sub")
        if not client_id:
            raise ValueError("Token invalide")

        # Récupérer le client
        client = db.query(Client).filter(Client.ClientID == int(client_id)).first()

        if not client:
            raise ValueError("Client non trouvé")

        if client.StatutClient != 'ACTIF':
            raise ValueError("Compte désactivé")

        return client

    @staticmethod
    def logout(db: Session, refresh_token_str: str):
        """Déconnexion - révoquer le refresh token"""

        refresh_token = db.query(RefreshToken).filter(
            RefreshToken.Token == refresh_token_str
        ).first()

        if refresh_token:
            refresh_token.EstRevoque = True
            db.commit()

        return True
