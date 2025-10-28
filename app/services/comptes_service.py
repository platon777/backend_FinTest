"""
Service pour la gestion des Comptes d'investissement
"""
from sqlalchemy.orm import Session
from sqlalchemy import and_
from app.models.models import Compte, CompteRole, Client
from typing import List, Optional
from datetime import datetime
import random
import string


class ComptesService:
    """Service de gestion des comptes"""

    @staticmethod
    def generer_numero_compte() -> str:
        """Générer un numéro de compte unique"""
        # Format: INV-YYYYMMDD-XXXXX
        date_part = datetime.now().strftime("%Y%m%d")
        random_part = ''.join(random.choices(string.digits, k=5))
        return f"INV-{date_part}-{random_part}"

    @staticmethod
    def creer_compte(
        db: Session,
        client_id: int,
        numero_compte: Optional[str],
        type_compte: str,
        devise: str = "HTG",
        role: str = "TITULAIRE_PRINCIPAL"
    ) -> Compte:
        """
        Créer un nouveau compte d'investissement
        """
        # Vérifier que le client existe
        client = db.query(Client).filter(Client.ClientID == client_id).first()
        if not client:
            raise ValueError("Client introuvable")

        # Générer un numéro si non fourni
        if not numero_compte:
            numero_compte = ComptesService.generer_numero_compte()
            # Vérifier l'unicité
            while db.query(Compte).filter(Compte.NumeroCompte == numero_compte).first():
                numero_compte = ComptesService.generer_numero_compte()

        # Vérifier que le numéro n'existe pas
        existing = db.query(Compte).filter(Compte.NumeroCompte == numero_compte).first()
        if existing:
            raise ValueError(f"Le numéro de compte {numero_compte} existe déjà")

        # Créer le compte
        compte = Compte(
            NumeroCompte=numero_compte,
            TypeCompte=type_compte,
            Devise=devise,
            Solde=0,
            SoldeDisponible=0,
            StatutCompte='ACTIF'
        )
        db.add(compte)
        db.flush()

        # Créer le rôle du client sur ce compte
        compte_role = CompteRole(
            CompteID=compte.CompteID,
            ClientID=client_id,
            Role=role,
            EstActif=True
        )
        db.add(compte_role)

        db.commit()
        db.refresh(compte)

        return compte

    @staticmethod
    def get_compte_by_id(db: Session, compte_id: int) -> Optional[Compte]:
        """Récupérer un compte par son ID"""
        return db.query(Compte).filter(Compte.CompteID == compte_id).first()

    @staticmethod
    def get_compte_by_numero(db: Session, numero_compte: str) -> Optional[Compte]:
        """Récupérer un compte par son numéro"""
        return db.query(Compte).filter(Compte.NumeroCompte == numero_compte).first()

    @staticmethod
    def get_comptes_client(db: Session, client_id: int, statut: Optional[str] = None) -> List[Compte]:
        """
        Récupérer tous les comptes d'un client
        """
        query = db.query(Compte).join(CompteRole).filter(
            and_(
                CompteRole.ClientID == client_id,
                CompteRole.EstActif == True
            )
        )

        if statut:
            query = query.filter(Compte.StatutCompte == statut)

        return query.all()

    @staticmethod
    def verifier_acces_compte(db: Session, compte_id: int, client_id: int) -> bool:
        """
        Vérifier qu'un client a accès à un compte
        """
        role = db.query(CompteRole).filter(
            and_(
                CompteRole.CompteID == compte_id,
                CompteRole.ClientID == client_id,
                CompteRole.EstActif == True
            )
        ).first()

        return role is not None

    @staticmethod
    def verifier_role_compte(
        db: Session,
        compte_id: int,
        client_id: int,
        roles_autorises: List[str]
    ) -> bool:
        """
        Vérifier qu'un client a un rôle spécifique sur un compte
        """
        role = db.query(CompteRole).filter(
            and_(
                CompteRole.CompteID == compte_id,
                CompteRole.ClientID == client_id,
                CompteRole.Role.in_(roles_autorises),
                CompteRole.EstActif == True
            )
        ).first()

        return role is not None

    @staticmethod
    def mettre_a_jour_solde(
        db: Session,
        compte_id: int,
        nouveau_solde: float,
        nouveau_solde_disponible: Optional[float] = None
    ) -> Compte:
        """
        Mettre à jour le solde d'un compte
        """
        compte = db.query(Compte).filter(Compte.CompteID == compte_id).first()
        if not compte:
            raise ValueError("Compte introuvable")

        if nouveau_solde < 0:
            raise ValueError("Le solde ne peut pas être négatif")

        compte.Solde = nouveau_solde
        if nouveau_solde_disponible is not None:
            compte.SoldeDisponible = nouveau_solde_disponible
        else:
            compte.SoldeDisponible = nouveau_solde

        db.commit()
        db.refresh(compte)

        return compte

    @staticmethod
    def suspendre_compte(db: Session, compte_id: int) -> Compte:
        """Suspendre un compte"""
        compte = db.query(Compte).filter(Compte.CompteID == compte_id).first()
        if not compte:
            raise ValueError("Compte introuvable")

        compte.StatutCompte = 'SUSPENDU'
        db.commit()
        db.refresh(compte)

        return compte

    @staticmethod
    def fermer_compte(db: Session, compte_id: int) -> Compte:
        """Fermer un compte"""
        compte = db.query(Compte).filter(Compte.CompteID == compte_id).first()
        if not compte:
            raise ValueError("Compte introuvable")

        if compte.Solde > 0:
            raise ValueError("Impossible de fermer un compte avec un solde positif")

        compte.StatutCompte = 'FERME'
        compte.DateFermeture = datetime.utcnow()
        db.commit()
        db.refresh(compte)

        return compte

    @staticmethod
    def ajouter_client_compte(
        db: Session,
        compte_id: int,
        client_id: int,
        role: str
    ) -> CompteRole:
        """
        Ajouter un client à un compte avec un rôle spécifique
        """
        # Vérifier que le compte et le client existent
        compte = db.query(Compte).filter(Compte.CompteID == compte_id).first()
        if not compte:
            raise ValueError("Compte introuvable")

        client = db.query(Client).filter(Client.ClientID == client_id).first()
        if not client:
            raise ValueError("Client introuvable")

        # Vérifier que ce client n'a pas déjà ce rôle sur ce compte
        existing = db.query(CompteRole).filter(
            and_(
                CompteRole.CompteID == compte_id,
                CompteRole.ClientID == client_id,
                CompteRole.Role == role,
                CompteRole.EstActif == True
            )
        ).first()

        if existing:
            raise ValueError(f"Le client a déjà le rôle {role} sur ce compte")

        # Créer le rôle
        compte_role = CompteRole(
            CompteID=compte_id,
            ClientID=client_id,
            Role=role,
            EstActif=True
        )
        db.add(compte_role)
        db.commit()
        db.refresh(compte_role)

        return compte_role

    @staticmethod
    def retirer_client_compte(db: Session, compte_role_id: int) -> bool:
        """
        Retirer un client d'un compte (désactiver le rôle)
        """
        role = db.query(CompteRole).filter(CompteRole.CompteRoleID == compte_role_id).first()
        if not role:
            raise ValueError("Rôle introuvable")

        # Ne pas permettre de retirer le dernier titulaire principal
        if role.Role == 'TITULAIRE_PRINCIPAL':
            autres_titulaires = db.query(CompteRole).filter(
                and_(
                    CompteRole.CompteID == role.CompteID,
                    CompteRole.Role == 'TITULAIRE_PRINCIPAL',
                    CompteRole.EstActif == True,
                    CompteRole.CompteRoleID != compte_role_id
                )
            ).count()

            if autres_titulaires == 0:
                raise ValueError("Impossible de retirer le dernier titulaire principal")

        role.EstActif = False
        role.DateFin = datetime.utcnow()
        db.commit()

        return True

    @staticmethod
    def get_roles_compte(db: Session, compte_id: int) -> List[CompteRole]:
        """Récupérer tous les rôles actifs d'un compte"""
        return db.query(CompteRole).filter(
            and_(
                CompteRole.CompteID == compte_id,
                CompteRole.EstActif == True
            )
        ).all()
