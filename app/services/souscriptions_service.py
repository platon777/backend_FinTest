"""
Service pour la gestion des Souscriptions (Investissements)
"""
from sqlalchemy.orm import Session
from sqlalchemy import and_
from app.models.models import Souscription, Instrument, Compte, CompteRole, PaiementInteret
from typing import List, Optional
from datetime import datetime
from decimal import Decimal


class SouscriptionsService:
    """Service de gestion des souscriptions"""

    @staticmethod
    def creer_souscription(
        db: Session,
        compte_id: int,
        instrument_id: int,
        montant_investi: Decimal,
        client_id: int
    ) -> Souscription:
        """Créer une nouvelle souscription"""
        # Vérifier que le compte existe et que le client y a accès
        role = db.query(CompteRole).filter(
            and_(
                CompteRole.CompteID == compte_id,
                CompteRole.ClientID == client_id,
                CompteRole.Role.in_(['TITULAIRE_PRINCIPAL', 'TITULAIRE_SECONDAIRE', 'MANDATAIRE']),
                CompteRole.EstActif == True
            )
        ).first()

        if not role:
            raise ValueError("Accès refusé : vous n'avez pas les droits sur ce compte")

        # Vérifier que l'instrument existe et est disponible
        instrument = db.query(Instrument).filter(Instrument.InstrumentID == instrument_id).first()
        if not instrument:
            raise ValueError("Instrument introuvable")

        if instrument.StatutInstrument != 'DISPONIBLE':
            raise ValueError(f"L'instrument {instrument.Code} n'est pas disponible")

        # Vérifier le montant minimum
        if instrument.MontantMinimum and montant_investi < instrument.MontantMinimum:
            raise ValueError(f"Montant minimum requis: {instrument.MontantMinimum}")

        # Vérifier le solde disponible
        compte = db.query(Compte).filter(Compte.CompteID == compte_id).first()
        if compte.SoldeDisponible < montant_investi:
            raise ValueError("Solde insuffisant")

        # Calculer le nombre d'unités
        nombre_unites = None
        if instrument.ValeurNominale and instrument.ValeurNominale > 0:
            nombre_unites = montant_investi / instrument.ValeurNominale

        # Créer la souscription
        souscription = Souscription(
            CompteID=compte_id,
            InstrumentID=instrument_id,
            MontantInvesti=montant_investi,
            NombreUnites=nombre_unites,
            TauxSouscription=instrument.TauxRendementAnnuel,
            DateMaturiteEffective=instrument.DateMaturite,
            ValeurActuelle=montant_investi,
            InteretsAccumules=0,
            StatutSouscription='ACTIVE'
        )
        db.add(souscription)

        # Mettre à jour le solde du compte
        compte.SoldeDisponible -= montant_investi

        db.commit()
        db.refresh(souscription)

        return souscription

    @staticmethod
    def get_souscriptions_client(db: Session, client_id: int) -> List[Souscription]:
        """Récupérer toutes les souscriptions d'un client"""
        return db.query(Souscription).join(Compte).join(CompteRole).filter(
            and_(
                CompteRole.ClientID == client_id,
                CompteRole.EstActif == True
            )
        ).all()

    @staticmethod
    def get_souscriptions_compte(db: Session, compte_id: int) -> List[Souscription]:
        """Récupérer toutes les souscriptions d'un compte"""
        return db.query(Souscription).filter(Souscription.CompteID == compte_id).all()

    @staticmethod
    def get_souscription_by_id(db: Session, souscription_id: int) -> Optional[Souscription]:
        """Récupérer une souscription par ID"""
        return db.query(Souscription).filter(Souscription.SouscriptionID == souscription_id).first()

    @staticmethod
    def racheter_souscription(db: Session, souscription_id: int, client_id: int) -> Souscription:
        """Racheter une souscription (liquidation)"""
        souscription = db.query(Souscription).filter(
            Souscription.SouscriptionID == souscription_id
        ).first()

        if not souscription:
            raise ValueError("Souscription introuvable")

        # Vérifier l'accès
        role = db.query(CompteRole).filter(
            and_(
                CompteRole.CompteID == souscription.CompteID,
                CompteRole.ClientID == client_id,
                CompteRole.Role.in_(['TITULAIRE_PRINCIPAL', 'TITULAIRE_SECONDAIRE', 'MANDATAIRE']),
                CompteRole.EstActif == True
            )
        ).first()

        if not role:
            raise ValueError("Accès refusé")

        if souscription.StatutSouscription != 'ACTIVE':
            raise ValueError("Cette souscription n'est pas active")

        # Calculer le montant à racheter
        montant_rachat = souscription.ValeurActuelle + souscription.InteretsAccumules

        # Mettre à jour la souscription
        souscription.StatutSouscription = 'RACHETEE'

        # Créditer le compte
        compte = db.query(Compte).filter(Compte.CompteID == souscription.CompteID).first()
        compte.Solde += montant_rachat
        compte.SoldeDisponible += montant_rachat

        db.commit()
        db.refresh(souscription)

        return souscription

    @staticmethod
    def get_portefeuille_client(db: Session, client_id: int) -> dict:
        """Obtenir le portefeuille complet d'un client"""
        souscriptions = SouscriptionsService.get_souscriptions_client(db, client_id)

        total_investi = sum(s.MontantInvesti for s in souscriptions)
        valeur_actuelle = sum(s.ValeurActuelle or 0 for s in souscriptions)
        interets_accumules = sum(s.InteretsAccumules for s in souscriptions)

        return {
            "total_investi": total_investi,
            "valeur_actuelle_totale": valeur_actuelle,
            "interets_accumules_total": interets_accumules,
            "nombre_souscriptions": len(souscriptions),
            "souscriptions": souscriptions
        }
