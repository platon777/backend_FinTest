"""
Service pour la gestion des Transactions
"""
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from app.models.models import Transaction, Compte, CompteRole
from typing import List, Optional
from datetime import datetime
from decimal import Decimal


class TransactionsService:
    """Service de gestion des transactions"""

    @staticmethod
    def creer_transaction(
        db: Session,
        type_transaction: str,
        montant: Decimal,
        devise: str,
        compte_source: Optional[int] = None,
        compte_destination: Optional[int] = None,
        description: Optional[str] = None,
        souscription_id: Optional[int] = None,
        est_automatique: bool = False
    ) -> Transaction:
        """Créer une nouvelle transaction"""

        # Validation selon le type de transaction
        if type_transaction == 'DEPOT' and not compte_destination:
            raise ValueError("Un compte destination est requis pour un dépôt")

        if type_transaction == 'RETRAIT' and not compte_source:
            raise ValueError("Un compte source est requis pour un retrait")

        if type_transaction == 'TRANSFERT' and (not compte_source or not compte_destination):
            raise ValueError("Un compte source et destination sont requis pour un transfert")

        # Créer la transaction
        transaction = Transaction(
            TypeTransaction=type_transaction,
            CompteSource=compte_source,
            CompteDestination=compte_destination,
            Montant=montant,
            Devise=devise,
            Description=description,
            StatutTransaction='EN_ATTENTE',
            SouscriptionID=souscription_id,
            EstAutomatique=est_automatique
        )

        db.add(transaction)
        db.commit()
        db.refresh(transaction)

        return transaction

    @staticmethod
    def executer_transaction(db: Session, transaction_id: int) -> Transaction:
        """Exécuter une transaction en attente"""
        transaction = db.query(Transaction).filter(
            Transaction.TransactionID == transaction_id
        ).first()

        if not transaction:
            raise ValueError("Transaction introuvable")

        if transaction.StatutTransaction != 'EN_ATTENTE':
            raise ValueError(f"Cette transaction est déjà {transaction.StatutTransaction}")

        try:
            # Traiter selon le type
            if transaction.TypeTransaction == 'DEPOT':
                TransactionsService._executer_depot(db, transaction)

            elif transaction.TypeTransaction == 'RETRAIT':
                TransactionsService._executer_retrait(db, transaction)

            elif transaction.TypeTransaction == 'TRANSFERT':
                TransactionsService._executer_transfert(db, transaction)

            elif transaction.TypeTransaction in ['PAIEMENT_INTERET', 'REMBOURSEMENT_MATURITE']:
                TransactionsService._executer_credit(db, transaction)

            # Marquer comme exécutée
            transaction.StatutTransaction = 'EXECUTEE'
            transaction.DateExecution = datetime.utcnow()

            db.commit()
            db.refresh(transaction)

            return transaction

        except Exception as e:
            transaction.StatutTransaction = 'ECHOUEE'
            transaction.Description = f"{transaction.Description or ''} - Erreur: {str(e)}"
            db.commit()
            raise

    @staticmethod
    def _executer_depot(db: Session, transaction: Transaction):
        """Exécuter un dépôt"""
        compte = db.query(Compte).filter(
            Compte.CompteID == transaction.CompteDestination
        ).first()

        if not compte:
            raise ValueError("Compte destination introuvable")

        if compte.StatutCompte != 'ACTIF':
            raise ValueError("Le compte n'est pas actif")

        # Créditer le compte
        compte.Solde += transaction.Montant
        compte.SoldeDisponible += transaction.Montant

    @staticmethod
    def _executer_retrait(db: Session, transaction: Transaction):
        """Exécuter un retrait"""
        compte = db.query(Compte).filter(
            Compte.CompteID == transaction.CompteSource
        ).first()

        if not compte:
            raise ValueError("Compte source introuvable")

        if compte.StatutCompte != 'ACTIF':
            raise ValueError("Le compte n'est pas actif")

        if compte.SoldeDisponible < transaction.Montant:
            raise ValueError("Solde insuffisant")

        # Débiter le compte
        compte.Solde -= transaction.Montant
        compte.SoldeDisponible -= transaction.Montant

    @staticmethod
    def _executer_transfert(db: Session, transaction: Transaction):
        """Exécuter un transfert"""
        # Débiter le compte source
        TransactionsService._executer_retrait(db, transaction)

        # Créditer le compte destination
        compte_dest = db.query(Compte).filter(
            Compte.CompteID == transaction.CompteDestination
        ).first()

        if not compte_dest:
            raise ValueError("Compte destination introuvable")

        compte_dest.Solde += transaction.Montant
        compte_dest.SoldeDisponible += transaction.Montant

    @staticmethod
    def _executer_credit(db: Session, transaction: Transaction):
        """Exécuter un crédit (paiement intérêt, remboursement)"""
        if not transaction.CompteDestination:
            raise ValueError("Compte destination requis")

        compte = db.query(Compte).filter(
            Compte.CompteID == transaction.CompteDestination
        ).first()

        if not compte:
            raise ValueError("Compte introuvable")

        compte.Solde += transaction.Montant
        compte.SoldeDisponible += transaction.Montant

    @staticmethod
    def get_transactions_compte(db: Session, compte_id: int, limit: int = 100) -> List[Transaction]:
        """Récupérer les transactions d'un compte"""
        return db.query(Transaction).filter(
            or_(
                Transaction.CompteSource == compte_id,
                Transaction.CompteDestination == compte_id
            )
        ).order_by(Transaction.DateCreation.desc()).limit(limit).all()

    @staticmethod
    def get_transactions_client(db: Session, client_id: int, limit: int = 100) -> List[Transaction]:
        """Récupérer les transactions d'un client"""
        # Récupérer les comptes du client
        comptes_ids = db.query(CompteRole.CompteID).filter(
            and_(
                CompteRole.ClientID == client_id,
                CompteRole.EstActif == True
            )
        ).all()

        comptes_ids = [c[0] for c in comptes_ids]

        return db.query(Transaction).filter(
            or_(
                Transaction.CompteSource.in_(comptes_ids),
                Transaction.CompteDestination.in_(comptes_ids)
            )
        ).order_by(Transaction.DateCreation.desc()).limit(limit).all()

    @staticmethod
    def get_transaction_by_id(db: Session, transaction_id: int) -> Optional[Transaction]:
        """Récupérer une transaction par ID"""
        return db.query(Transaction).filter(
            Transaction.TransactionID == transaction_id
        ).first()

    @staticmethod
    def annuler_transaction(db: Session, transaction_id: int) -> Transaction:
        """Annuler une transaction en attente"""
        transaction = db.query(Transaction).filter(
            Transaction.TransactionID == transaction_id
        ).first()

        if not transaction:
            raise ValueError("Transaction introuvable")

        if transaction.StatutTransaction != 'EN_ATTENTE':
            raise ValueError("Seules les transactions en attente peuvent être annulées")

        transaction.StatutTransaction = 'ANNULEE'
        db.commit()
        db.refresh(transaction)

        return transaction
