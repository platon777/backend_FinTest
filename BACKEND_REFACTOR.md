# Note de refonte backend

## Périmètre retenu

Cette refonte implémente le cœur critique décrit dans `Codex_Profin/projet analyste dev.docx` et l'orientation Core Investment Platform : une source de vérité relationnelle, la cohérence financière, les comptes/positions, les validations, les écritures comptables et l'audit.

Le système est volontairement un monolithe modulaire. Le dimensionnement fourni dans le document interne ne justifie pas de découper physiquement le cœur financier en microservices : les opérations qui touchent un compte, une position, une transaction et la comptabilité doivent rester atomiques dans la même transaction PostgreSQL.

## Modèle de données

`clients` porte l'identité métier. Les profils KYC sont séparés entre `individual_profiles` et `institutional_profiles`. `accounts` et `account_roles` permettent la gestion de comptes partagés et la limitation systématique de l'accès. `instruments` et `subscriptions` représentent le référentiel et les positions.

`transactions` conserve le maker (`created_by_client_id`), le checker (`approved_by_client_id`), l'état du workflow et les dates d'exécution. `accounting_entries` conserve les deux écritures générées à l'exécution. `audit_logs` garde la preuve métier de l'action.

## Scénarios démontrés par le seed

1. Marie Jean possède un compte USD d'investissement, une épargne HTG et deux obligations (BRH 2027 et EDH 2028), avec intérêts courus réalistes.
2. Caribe Investissements S.A. possède un compte institutionnel USD et une position dans un fonds diversifié Caraïbes.
3. Paul Joseph dispose d'un rôle `OBSERVATEUR` sur un compte joint HTG : il peut consulter mais ne peut pas créer de retrait.
4. Les dépôts/retraits historiques sont exécutés et alimentent l'historique; les nouvelles opérations sont d'abord en attente de validation.

## Limites assumées du prototype

- Le bouton de souscription du prototype finalise immédiatement la position via `PROTOTYPE_AUTO_APPROVE_SUBSCRIPTIONS=true`, pour rendre le parcours investisseur testable. Les opérations cash génériques utilisent toujours maker/checker.
- Aucun back-office ou rôle employé n'est exposé. Un futur front-office pourra utiliser le même workflow avec des permissions internes dédiées.
- Pas de Redis, VPN, gateway public, IA, outbox, scheduler ou connecteurs externes pour l'instant.
- Le moteur de maturité et le calcul de valeur sont prévus dans le modèle, mais l'intégration batch sera une étape ultérieure.

## Passage vers la production

Il faudra remplacer les secrets Docker, placer PostgreSQL derrière le réseau privé prévu, ajouter un IdP ou une gestion centralisée des utilisateurs si nécessaire, compléter les migrations Alembic explicites, ajouter la réconciliation comptable, les jobs de maturité, l'outbox d'intégration et les tests PostgreSQL d'intégration.
