# Refonte backend ProFin — périmètre prototype

Le backend est un monolithe modulaire FastAPI/PostgreSQL. Le cœur financier reste transactionnel afin que compte, position, transaction, écritures comptables et audit soient cohérents dans la même opération PostgreSQL.

## Couverture métier

- KYC individuel et institutionnel, profil de risque et informations de contact;
- comptes multi-devises et rôles `TITULAIRE_PRINCIPAL`, `MANDATAIRE`, `ADMINISTRATEUR`, `OBSERVATEUR`;
- référentiel d'instruments, souscriptions, positions, rachats et maturités;
- dépôt, retrait et transfert avec maker/checker;
- ordre d'investissement client soumis avant exécution, montant réservé, étapes conformité → back-office → checker, rejet/annulation et libération de la réservation;
- création atomique de la position, de la transaction `SOUSCRIPTION`, des écritures équilibrées et de l'audit à la dernière validation;
- audit des créations, validations, rejets, exécutions et maturités;
- PostgreSQL dockerisé, migrations Alembic additives, seed idempotent et tests d'intégration PostgreSQL.

## Règle d'exécution des ordres

Une soumission client ne crée pas immédiatement une position. Le montant diminue seulement de `available_balance` pour matérialiser une réservation. Après les trois contrôles, le solde comptable est débité, la position est créée et la transaction ainsi que les écritures sont enregistrées. Un rejet ou une annulation restitue le disponible.

## Limites assumées du prototype

- les profils internes sont simulés par des clients habilités sur un compte partagé afin de montrer le maker/checker sans ajouter un IdP interne;
- les étapes conformité, back-office et reporting sont des étapes persistées, sans CRM, connecteur, outbox ou retry réseau;
- Redis, VPN, gateway public, IA conversationnelle, scheduler de production, revalorisation de marché, réconciliation avancée et reporting AUM/fees/TCA restent hors périmètre de la démonstration;
- la maturité est générée par une action de maintenance puis soumise au même contrôle, en attendant un job planifié.

## Passage vers la production

Ajouter une identité interne séparée (conseiller, conformité, back-office, superviseur), un contrôle d'habilitation centralisé, une outbox transactionnelle avec retry, les connecteurs CRM/comptabilité, les jobs de maturité/revalorisation, la réconciliation, les rapports AUM/performance/frais, l'observabilité SIEM et le réseau privé prévu par l'architecture.
