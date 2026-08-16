# Audit de cohérence du portail ProFin

## Verdict de présentation

Oui, le prototype est présentable pour un entretien d'analyste programmeur si le périmètre est expliqué clairement. Il montre maintenant un portail client qui ne déclenche pas silencieusement une transaction : le client soumet un ordre, le montant est réservé, les contrôles sont visibles et la position n'existe qu'après validation complète.

## Parcours à montrer

1. **Marie — lecture client** : connexion, KYC, comptes USD/HTG, positions BRH/EDH, activité et liquidités par devise.
2. **Marie — soumission** : sélection d'un instrument, contrôle du minimum et de la devise, soumission de l'ordre, réservation du disponible et statut `SUBMITTED`.
3. **Sophie — maker/checker** : ouverture du même compte avec un autre profil habilité, approbation conformité, back-office puis checker. Le maker ne peut pas valider son propre ordre.
4. **Cohérence financière** : après la dernière étape, vérifier la position, la transaction `SOUSCRIPTION`, le débit du solde et les deux écritures comptables équilibrées.
5. **Cas négatifs** : rejeter un ordre et constater la libération du disponible; connecter Paul et montrer que son rôle observateur ne peut pas opérer; créer un retrait et le faire valider/rejeter.
6. **Maturité** : lancer la maintenance, générer le remboursement automatique en attente, puis le soumettre au checker.

## Correspondance avec le document du projet

Les rapports presentent maintenant le TMA annualise calcule sur les flux dates,
les frais d'entree, les coupons payes ou planifies et l'AUM par devise. Une
contrepassation est testable comme une nouvelle operation de correction soumise
a validation ; elle conserve l'operation d'origine et ses ecritures inversees.

| Exigence | Prototype |
|---|---|
| KYC individuel/institutionnel | Marie, Paul et Caribe |
| Comptes et rôles | Comptes individuels, institutionnels, joints, mandataire et observateur |
| Instruments et obligations | BRH 2027, EDH 2028, fonds Caraïbes |
| Ordre client | `POST /api/v1/ordres/`, liste portail et annulation |
| Maker/checker | Étapes persistées et contrôle d'identité distincte |
| Maturités automatiques | Génération de transaction `REMBOURSEMENT_MATURITE` prête à valider |
| Comptabilité/audit | Écritures débit/crédit et `audit_logs` dans le même commit |
| PostgreSQL/Docker | Compose avec API, frontend, PostgreSQL de production et PostgreSQL de test |
| IA, VPN, Redis, connecteurs | Délibérément différés et documentés comme limites du prototype |

## Réserve à dire pendant la présentation

Le workflow interne est représenté fonctionnellement, mais les rôles sont encore portés par des clients habilités sur un compte partagé. En production, ils doivent être remplacés par une identité interne séparée et des profils conseiller, conformité, back-office et superviseur. Cette limite est assumée pour garder le prototype focalisé sur la vérité financière et les parcours métier.
