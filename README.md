# ProFin Core Investment Platform — backend prototype

Backend FastAPI du prototype demandé pour le système d'information miniature d'une banque d'investissement.

## Choix d'architecture

Le backend est un monolithe modulaire : une seule API et une seule base relationnelle PostgreSQL portent la vérité financière. Les domaines sont séparés dans le code : authentification/KYC, comptes et rôles, instruments, souscriptions, transactions, écritures comptables, audit et dashboard.

Redis, VPN, point d'entrée public, IA, connecteurs CRM/comptabilité et workers asynchrones sont volontairement hors du prototype exécutable. Les contrats et le modèle de données gardent toutefois les points d'extension nécessaires.

## Démarrage Docker

```bash
docker compose up --build
```

La base de développement est exposée sur `localhost:55431` (le port interne reste `5432`). Le port `55432` est réservé à la base PostgreSQL de tests.

La commande lance PostgreSQL, applique la migration Alembic, charge le seed idempotent, démarre l'API et construit le frontend ProFin Core Console sur `http://localhost:3000`.

- API : http://localhost:8000
- Swagger : http://localhost:8000/api/v1/docs
- Health : http://localhost:8000/health
- Adminer : http://localhost:5050

Dans Adminer, sélectionnez PostgreSQL, utilisez `db` comme serveur interne Docker, le port `5432`, la base `profin_core`, l'utilisateur `profin` et le mot de passe `profin_dev`.

Le volume `profin_pgdata` conserve les données. Pour repartir de zéro en environnement de démonstration :

```bash
docker compose down -v
docker compose up --build
```

## Fonctionnalités métier

- clients individuels et institutionnels avec KYC;
- comptes multi-devises et rôles `TITULAIRE_PRINCIPAL`, `TITULAIRE_SECONDAIRE`, `MANDATAIRE`, `OBSERVATEUR`;
- catalogue d'instruments, obligations et fonds;
- souscriptions avec contrôle de devise, minimum, solde, position et rendement;
- dépôts, retraits et transferts en workflow `PENDING_APPROVAL -> APPROVED -> EXECUTED`;
- maker/checker : le créateur d'une transaction ne peut pas la valider lui-même;
- écritures comptables équilibrées générées à l'exécution;
- audit métier pour les créations, validations et exécutions;
- dashboard portefeuille et historique filtrés par les comptes autorisés.

## Authentification

`POST /api/v1/auth/login` émet un JWT d'accès valable 30 minutes et un refresh token opaque valable 7 jours. Seul le hash SHA-256 du refresh token est conservé en base; chaque rafraîchissement révoque l'ancien token et en émet un nouveau. Le JWT ne contient que `client_id`, le type et l'expiration. Les permissions sont relues en base à chaque accès métier.

## Endpoints principaux

| Domaine | Routes |
|---|---|
| Auth | `/auth/register`, `/auth/login`, `/auth/refresh`, `/auth/logout` |
| KYC | `/users/me`, `/profil` |
| Comptes | `/comptes/mes-comptes`, `/comptes/{id}` |
| Instruments | `/instruments`, `/instruments/{id}` |
| Investissements | `/souscriptions/mes-souscriptions`, `POST /souscriptions/`, `/souscriptions/{id}/racheter` |
| Transactions | `POST /transactions/`, `/transactions/{id}/approve`, `/transactions/mes-transactions` |
| Dashboard | `/dashboard/overview`, `/dashboard/complet`, `/dashboard/investissements` |

## Tests PostgreSQL

Les tests n'utilisent pas SQLite. Ils se connectent à PostgreSQL sur le service Docker `db-test` et créent un schéma isolé temporaire par test :

```bash
docker compose --profile test up -d db-test
set TEST_DATABASE_URL=postgresql+psycopg2://profin:profin_dev@127.0.0.1:55432/profin_test
python -m pytest -q tests
```

La fixture réinitialise la base de test PostgreSQL dédiée entre les scénarios; aucune donnée de démonstration ou de production n'est utilisée par les tests.

La base de production/démonstration reste PostgreSQL et est créée par `alembic upgrade head`.

## Documents utiles

- [Comptes de démonstration](DEMO_CREDENTIALS.md)
- [Note de refonte backend](BACKEND_REFACTOR.md)
- [Guide de lancement complet](../Codex_Profin/GUIDE_LANCEMENT_PROFIN.md)
