"""
Service Dashboard - Utilise les vues SQL pour alimenter le portail client
"""
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List, Optional, Dict, Any
from datetime import datetime, date
from decimal import Decimal


class DashboardService:
    """Service de gestion du dashboard client"""

    @staticmethod
    def get_overview(db: Session, client_id: int, compte_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Vue d'ensemble du portefeuille
        Source: vw_Dashboard_Overview

        Args:
            db: Session SQLAlchemy
            client_id: ID du client connecté
            compte_id: ID du compte spécifique (optionnel)

        Returns:
            Dict avec valeur_totale, rendement_total, etc.
        """
        # Construction de la requête SQL
        params = {"client_id": client_id}
        where_clause = "cr.ClientID = :client_id AND cr.EstActif = 1"

        if compte_id:
            where_clause += " AND cr.CompteID = :compte_id"
            params["compte_id"] = compte_id

        query = text(f"""
            SELECT
                cr.ClientID,
                cr.CompteID,
                cpt.NumeroCompte,
                cpt.Devise AS DeviseCompte,
                ISNULL(SUM(s.ValeurActuelle), 0) AS ValeurTotale,
                ISNULL(SUM(s.InteretsAccumules), 0) AS RendementTotal,
                CASE
                    WHEN SUM(s.MontantInvesti) > 0
                    THEN (SUM(s.InteretsAccumules) / SUM(s.MontantInvesti)) * 100
                    ELSE 0
                END AS PourcentageRendement,
                COUNT(s.SouscriptionID) AS NombreSouscriptionsActives,
                ISNULL(SUM(s.MontantInvesti), 0) AS TotalInvesti
            FROM ComptesRoles cr
            INNER JOIN Comptes cpt ON cr.CompteID = cpt.CompteID
            LEFT JOIN Souscriptions s ON cpt.CompteID = s.CompteID AND s.StatutSouscription = 'ACTIVE'
            WHERE {where_clause}
                AND cpt.StatutCompte = 'ACTIF'
                AND cr.Role IN ('TITULAIRE_PRINCIPAL', 'MANDATAIRE', 'OBSERVATEUR', 'ADMINISTRATEUR')
            GROUP BY cr.ClientID, cr.CompteID, cpt.NumeroCompte, cpt.Devise
        """)

        result = db.execute(query, params).fetchall()

        if not result:
            return {
                "valeur_totale": Decimal("0"),
                "rendement_total": Decimal("0"),
                "pourcentage_rendement": 0.0,
                "nombre_souscriptions_actives": 0,
                "total_investi": Decimal("0"),
                "devise": "USD",
                "comptes": []
            }

        # Calculer les totaux globaux
        totals = {
            "valeur_totale": Decimal("0"),
            "rendement_total": Decimal("0"),
            "total_investi": Decimal("0"),
            "nombre_souscriptions": 0
        }

        comptes = []

        for row in result:
            valeur_totale = Decimal(str(row.ValeurTotale))
            rendement_total = Decimal(str(row.RendementTotal))
            pourcentage = float(row.PourcentageRendement)

            totals["valeur_totale"] += valeur_totale
            totals["rendement_total"] += rendement_total
            totals["total_investi"] += Decimal(str(row.TotalInvesti))
            totals["nombre_souscriptions"] += int(row.NombreSouscriptionsActives)

            comptes.append({
                "compte_id": row.CompteID,
                "numero_compte": row.NumeroCompte,
                "valeur_totale": valeur_totale,
                "rendement_total": rendement_total,
                "pourcentage_rendement": round(pourcentage, 2)
            })

        pourcentage_global = (
            (totals["rendement_total"] / totals["total_investi"]) * 100
            if totals["total_investi"] > 0 else 0
        )

        return {
            "valeur_totale": totals["valeur_totale"],
            "rendement_total": totals["rendement_total"],
            "pourcentage_rendement": round(float(pourcentage_global), 2),
            "nombre_souscriptions_actives": totals["nombre_souscriptions"],
            "total_investi": totals["total_investi"],
            "devise": result[0].DeviseCompte if result else "USD",
            "comptes": comptes
        }

    @staticmethod
    def get_transactions_recentes(
        db: Session,
        client_id: int,
        compte_id: Optional[int] = None,
        limit: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Dernières transactions
        Source: vw_Dashboard_DernieresTransactions

        Args:
            db: Session SQLAlchemy
            client_id: ID du client connecté
            compte_id: ID du compte spécifique (optionnel)
            limit: Nombre de transactions à retourner (défaut: 3)

        Returns:
            Liste des transactions récentes
        """
        params = {"client_id": client_id, "limit": limit}
        where_clause = "cr.ClientID = :client_id AND cr.EstActif = 1"

        if compte_id:
            where_clause += " AND cr.CompteID = :compte_id"
            params["compte_id"] = compte_id

        query = text(f"""
            SELECT TOP (:limit)
                t.TransactionID,
                t.TypeTransaction,
                t.Description,
                t.Montant,
                t.Devise,
                t.DateCreation,
                t.DateExecution,
                t.StatutTransaction,
                cptSrc.NumeroCompte AS CompteSource,
                cptDest.NumeroCompte AS CompteDestination
            FROM ComptesRoles cr
            INNER JOIN Comptes cpt ON cr.CompteID = cpt.CompteID
            LEFT JOIN Transactions t ON (t.CompteSource = cpt.CompteID OR t.CompteDestination = cpt.CompteID)
            LEFT JOIN Comptes cptSrc ON t.CompteSource = cptSrc.CompteID
            LEFT JOIN Comptes cptDest ON t.CompteDestination = cptDest.CompteID
            WHERE {where_clause}
                AND cr.Role IN ('TITULAIRE_PRINCIPAL', 'MANDATAIRE', 'OBSERVATEUR', 'ADMINISTRATEUR')
                AND t.TransactionID IS NOT NULL
            ORDER BY ISNULL(t.DateExecution, t.DateCreation) DESC
        """)

        result = db.execute(query, params).fetchall()

        transactions = []
        for row in result:
            transactions.append({
                "transaction_id": row.TransactionID,
                "type_transaction": row.TypeTransaction,
                "description": row.Description,
                "montant": Decimal(str(row.Montant)),
                "devise": row.Devise,
                "date_creation": row.DateCreation,
                "date_execution": row.DateExecution,
                "statut": row.StatutTransaction,
                "compte_source": row.CompteSource,
                "compte_destination": row.CompteDestination
            })

        return transactions

    @staticmethod
    def get_investissements_actifs(
        db: Session,
        client_id: int,
        compte_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Investissements actifs (aperçu)
        Source: vw_Dashboard_InvestissementsActifs

        Args:
            db: Session SQLAlchemy
            client_id: ID du client connecté
            compte_id: ID du compte spécifique (optionnel)

        Returns:
            Liste des investissements actifs
        """
        params = {"client_id": client_id}
        where_clause = "cr.ClientID = :client_id AND cr.EstActif = 1"

        if compte_id:
            where_clause += " AND cr.CompteID = :compte_id"
            params["compte_id"] = compte_id

        query = text(f"""
            SELECT
                s.SouscriptionID,
                cr.CompteID,
                i.Nom AS NomInstrument,
                i.Code AS CodeInstrument,
                s.MontantInvesti,
                s.ValeurActuelle,
                s.TauxSouscription,
                s.DateMaturiteEffective,
                s.InteretsAccumules,
                s.StatutSouscription,
                CASE
                    WHEN DATEDIFF(DAY, s.DateSouscription, s.DateMaturiteEffective) > 0
                    THEN CAST(DATEDIFF(DAY, s.DateSouscription, GETDATE()) AS FLOAT) /
                         DATEDIFF(DAY, s.DateSouscription, s.DateMaturiteEffective) * 100
                    ELSE 0
                END AS ProgressionMaturite
            FROM ComptesRoles cr
            INNER JOIN Comptes cpt ON cr.CompteID = cpt.CompteID
            INNER JOIN Souscriptions s ON cpt.CompteID = s.CompteID
            INNER JOIN Instruments i ON s.InstrumentID = i.InstrumentID
            WHERE {where_clause}
                AND s.StatutSouscription = 'ACTIVE'
                AND cr.Role IN ('TITULAIRE_PRINCIPAL', 'MANDATAIRE', 'OBSERVATEUR', 'ADMINISTRATEUR')
            ORDER BY s.DateMaturiteEffective
        """)

        result = db.execute(query, params).fetchall()

        investissements = []
        for row in result:
            investissements.append({
                "souscription_id": row.SouscriptionID,
                "compte_id": row.CompteID,
                "nom_instrument": row.NomInstrument,
                "code_instrument": row.CodeInstrument,
                "montant_investi": Decimal(str(row.MontantInvesti)),
                "valeur_actuelle": Decimal(str(row.ValeurActuelle)),
                "taux_souscription": Decimal(str(row.TauxSouscription)),
                "date_maturite": row.DateMaturiteEffective,
                "interets_accumules": Decimal(str(row.InteretsAccumules)),
                "progression_maturite": round(float(row.ProgressionMaturite), 2),
                "statut": row.StatutSouscription
            })

        return investissements

    @staticmethod
    def get_statistiques_mensuelles(
        db: Session,
        client_id: int,
        compte_id: Optional[int] = None,
        mois: int = 12
    ) -> List[Dict[str, Any]]:
        """
        Statistiques mensuelles pour le graphique
        Source: vw_StatistiquesMensuelles

        Args:
            db: Session SQLAlchemy
            client_id: ID du client connecté
            compte_id: ID du compte spécifique (optionnel)
            mois: Nombre de mois à retourner (défaut: 12)

        Returns:
            Liste des statistiques mensuelles
        """
        params = {"client_id": client_id}
        where_clause = "cr.ClientID = :client_id AND cr.EstActif = 1"

        if compte_id:
            where_clause += " AND cr.CompteID = :compte_id"
            params["compte_id"] = compte_id

        # Générer les N derniers mois
        query = text(f"""
            WITH MoisRecents AS (
                SELECT DATEADD(MONTH, -n, DATEFROMPARTS(YEAR(GETDATE()), MONTH(GETDATE()), 1)) AS DateMois
                FROM (
                    SELECT 0 AS n UNION ALL SELECT 1 UNION ALL SELECT 2 UNION ALL
                    SELECT 3 UNION ALL SELECT 4 UNION ALL SELECT 5 UNION ALL
                    SELECT 6 UNION ALL SELECT 7 UNION ALL SELECT 8 UNION ALL
                    SELECT 9 UNION ALL SELECT 10 UNION ALL SELECT 11
                ) AS Nombres
            )
            SELECT
                m.DateMois,
                DATENAME(MONTH, m.DateMois) AS NomMois,
                ISNULL(SUM(s.ValeurActuelle), 0) AS ValeurPortefeuille,
                COUNT(s.SouscriptionID) AS NombreSouscriptions
            FROM MoisRecents m
            CROSS JOIN ComptesRoles cr
            INNER JOIN Comptes cpt ON cr.CompteID = cpt.CompteID
            LEFT JOIN Souscriptions s ON cpt.CompteID = s.CompteID
                AND s.DateSouscription <= EOMONTH(m.DateMois)
                AND (s.DateMaturiteEffective >= m.DateMois OR s.DateMaturiteEffective IS NULL)
                AND s.StatutSouscription = 'ACTIVE'
            WHERE {where_clause}
                AND cr.Role IN ('TITULAIRE_PRINCIPAL', 'MANDATAIRE', 'ADMINISTRATEUR')
            GROUP BY cr.ClientID, cr.CompteID, m.DateMois
            ORDER BY m.DateMois
        """)

        result = db.execute(query, params).fetchall()

        # Agréger par mois (si plusieurs comptes)
        mois_dict = {}
        for row in result:
            date_mois = row.DateMois
            if date_mois not in mois_dict:
                mois_dict[date_mois] = {
                    "mois": row.NomMois,
                    "date_mois": date_mois,
                    "valeur_portefeuille": Decimal("0"),
                    "nombre_souscriptions": 0
                }

            mois_dict[date_mois]["valeur_portefeuille"] += Decimal(str(row.ValeurPortefeuille))
            mois_dict[date_mois]["nombre_souscriptions"] += int(row.NombreSouscriptions)

        # Convertir en liste triée
        statistiques = sorted(mois_dict.values(), key=lambda x: x["date_mois"])

        return statistiques

    @staticmethod
    def get_dashboard_complet(
        db: Session,
        client_id: int,
        compte_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Récupère toutes les données du dashboard en un seul appel

        Args:
            db: Session SQLAlchemy
            client_id: ID du client connecté
            compte_id: ID du compte spécifique (optionnel)

        Returns:
            Dict avec overview, transactions_recentes, investissements_actifs, statistiques_mensuelles
        """
        return {
            "overview": DashboardService.get_overview(db, client_id, compte_id),
            "transactions_recentes": {
                "total": len(DashboardService.get_transactions_recentes(db, client_id, compte_id, limit=3)),
                "transactions": DashboardService.get_transactions_recentes(db, client_id, compte_id, limit=3)
            },
            "investissements_actifs": {
                "total": len(DashboardService.get_investissements_actifs(db, client_id, compte_id)),
                "investissements": DashboardService.get_investissements_actifs(db, client_id, compte_id)
            },
            "statistiques_mensuelles": {
                "periodes": DashboardService.get_statistiques_mensuelles(db, client_id, compte_id, mois=12)
            }
        }
