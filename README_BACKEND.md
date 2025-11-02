# PROFIN BANK - BACKEND API
## Système de Gestion de Portefeuille Client avec Multi-Rôles

---

## APERÇU DU PROJET

Profin Bank est une application de gestion de portefeuille client qui permet à des utilisateurs d'accéder à plusieurs comptes avec différents rôles (Titulaire, Mandataire, Observateur, Administrateur).

### Fonctionnalités Principales

- **Multi-comptes avec rôles**: Un client peut avoir accès à plusieurs comptes avec différents niveaux de permissions
- **Gestion d'investissements**: Souscription à des obligations, actions, fonds communs
- **Transactions**: Dépôts, retraits, souscriptions, rachats
- **Dashboard interactif**: Vue d'ensemble du portefeuille, statistiques mensuelles
- **Profil KYC**: Informations personnelles et conformité
- **Audit complet**: Traçabilité de toutes les actions

### Technologies

- **Backend**: Node.js + Express.js
- **ORM**: Sequelize
- **Base de données**: Microsoft SQL Server (Azure SQL)
- **Authentification**: JWT
- **Frontend**: React (séparé)

---

## DOCUMENTS DISPONIBLES

Ce projet contient 3 documents de spécification complets:

### 1. [API_SPECIFICATION.md](./API_SPECIFICATION.md)
**Spécification complète des endpoints API**
- 22 endpoints RESTful détaillés
- Paramètres de requête, body, et réponses
- Gestion des erreurs et codes d'erreur
- Système de permissions par rôle
- Exemples de requêtes/réponses

### 2. [ARCHITECTURE_TECHNIQUE.md](./ARCHITECTURE_TECHNIQUE.md)
**Architecture backend détaillée**
- Structure du projet recommandée
- Modèles Sequelize
- Services (Permission, AccountAccess, Audit)
- Middlewares (Auth, AccountAccess, ErrorHandler)
- Exemples de code complets
- Configuration et déploiement

### 3. [MAPPING_VUES_SQL.md](./MAPPING_VUES_SQL.md)
**Mapping Vues SQL → Endpoints API**
- Comment utiliser les 10 vues SQL existantes
- Requêtes SQL pour chaque endpoint
- Correspondance avec les vues frontend

---

## STRUCTURE DE LA BASE DE DONNÉES

### Tables Principales

```
Clients
├── ClientsIndividuels (1:1)
├── ClientsInstitutionnels (1:1)
├── ClientsAuthentification (1:1)
├── AdressesClients (1:N)
├── ContactsClients (1:N)
└── ComptesRoles (N:M avec Comptes)

Comptes
├── ComptesRoles (N:M avec Clients)
├── Souscriptions (1:N)
└── Transactions (1:N)

Instruments
├── TypesInstruments (N:1)
└── Souscriptions (1:N)

Souscriptions
├── Comptes (N:1)
├── Instruments (N:1)
├── PaiementsInterets (1:N)
└── Transactions (1:N)

Transactions
├── Comptes (N:1 pour source et destination)
└── Souscriptions (N:1 optionnel)
```

### Système de Rôles (ComptesRoles)

Un client peut avoir **plusieurs rôles sur différents comptes**:

| Rôle | Description | Permissions |
|------|-------------|-------------|
| `TITULAIRE_PRINCIPAL` | Propriétaire principal | Toutes |
| `TITULAIRE_SECONDAIRE` | Copropriétaire | Toutes sauf gestion rôles et fermeture |
| `MANDATAIRE` | Procuration | Consultation, dépôt, retrait, investissement |
| `OBSERVATEUR` | Lecture seule | Consultation uniquement |
| `ADMINISTRATEUR` | Gestionnaire | Toutes (entreprises) |
| `BENEFICIAIRE` | Bénéficiaire futur | Aucune (visible seulement) |

### Vues SQL Créées

10 vues optimisées pour l'API:
1. `vw_Dashboard_Overview` - Vue d'ensemble portefeuille
2. `vw_Dashboard_DernieresTransactions` - Dernières transactions
3. `vw_Dashboard_InvestissementsActifs` - Investissements actifs
4. `vw_MesComptes` - Liste des comptes
5. `vw_MesInvestissements` - Liste des investissements
6. `vw_HistoriqueTransactions` - Historique complet
7. `vw_ProfilClient` - Profil KYC
8. `vw_ComptesAccessibles` - Sélecteur de comptes
9. `vw_StatistiquesMensuelles` - Graphique mensuel
10. `vw_ProchainsInterets` - Paiements à venir

---

## ENDPOINTS API

### Authentification
- `POST /api/v1/auth/login` - Connexion
- `POST /api/v1/auth/refresh` - Rafraîchir token
- `POST /api/v1/auth/logout` - Déconnexion

### Comptes
- `GET /api/v1/comptes` - Liste des comptes accessibles
- `GET /api/v1/comptes/:id` - Détails d'un compte

### Dashboard
- `GET /api/v1/dashboard/overview` - Vue d'ensemble
- `GET /api/v1/dashboard/transactions/recentes` - Dernières transactions
- `GET /api/v1/dashboard/investissements` - Investissements actifs
- `GET /api/v1/dashboard/statistiques/mensuelles` - Stats mensuelles

### Investissements
- `GET /api/v1/investissements` - Liste des investissements
- `GET /api/v1/investissements/:id` - Détails investissement
- `GET /api/v1/investissements/instruments/disponibles` - Instruments disponibles
- `POST /api/v1/investissements/souscrire` - Nouvelle souscription

### Transactions
- `GET /api/v1/transactions` - Historique
- `GET /api/v1/transactions/:id` - Détails transaction
- `POST /api/v1/transactions/depot` - Créer dépôt
- `POST /api/v1/transactions/retrait` - Créer retrait
- `GET /api/v1/transactions/export/csv` - Export CSV

### Profil
- `GET /api/v1/profil` - Informations personnelles
- `PATCH /api/v1/profil` - Mise à jour profil

---

## EXEMPLE DE FLUX UTILISATEUR

### 1. Connexion
```
Client → POST /auth/login
       ← JWT token + refresh token
```

### 2. Dashboard
```
Client → GET /dashboard/overview (avec JWT)
       ← Valeur totale, rendement, souscriptions actives

Client → GET /dashboard/statistiques/mensuelles
       ← Données pour graphique (12 mois)

Client → GET /dashboard/transactions/recentes?limit=3
       ← 3 dernières transactions
```

### 3. Consulter Investissements
```
Client → GET /investissements?compteId=1&statut=ACTIVE
       ← Liste paginée des souscriptions actives
```

### 4. Nouvelle Souscription
```
Client → POST /investissements/souscrire
         Body: { compteId: 1, instrumentId: 101, montantInvesti: 10000 }
       ← { success: true, souscriptionId: 2010 }
```

---

## SÉCURITÉ MULTI-RÔLES

### Principe Fondamental

**Chaque requête doit:**
1. Vérifier le JWT (middleware auth)
2. Vérifier l'accès au compte (via ComptesRoles)
3. Vérifier la permission pour l'action (selon le rôle)

### Exemple Concret

**Utilisateur:** Marceus (ClientID = 1)

**Ses accès:**
- Compte INV-2023-230001 → `TITULAIRE_PRINCIPAL` (peut tout faire)
- Compte INV-2023-230005 (Hotel Oasis) → `ADMINISTRATEUR` (peut tout faire)
- Compte INV-2024-240001 (Joint avec Marie) → `TITULAIRE_PRINCIPAL` (peut tout faire)

**Requête:** `POST /transactions/retrait` sur compte INV-2023-230005

**Vérifications:**
1. ✅ JWT valide → ClientID = 1
2. ✅ Existe dans ComptesRoles → Rôle = ADMINISTRATEUR
3. ✅ Rôle ADMINISTRATEUR a permission `canWithdraw`
4. ✅ Transaction créée

**Si Marceus était OBSERVATEUR:**
3. ❌ Rôle OBSERVATEUR n'a PAS permission `canWithdraw`
4. ❌ Retour 403 Forbidden

---

## DONNÉES DE TEST

### Clients de Test (dans test_simulation_base.sql)

| Client | Type | Profil Risque | Comptes |
|--------|------|---------------|---------|
| Marceus Jethro | Individuel | Modéré | 3 comptes (titulaire sur 2, admin sur 1) |
| Patrick Marcellus | Individuel | Agressif | 2 comptes (titulaire + mandataire) |
| Joseph Woldy | Individuel | Conservateur | 1 compte |
| Alexandra Dorcean | Individuel | Modéré | 2 comptes (titulaire + observateur) |
| Hotel Oasis SARL | Institutionnel | Modéré | 1 compte |
| Marie Jethro | Individuel | Conservateur | 2 comptes |
| Sophia Marcellus | Individuel | Conservateur | 1 compte |

### Relations Multi-Rôles de Test

- **Marceus & Marie**: Compte joint (TITULAIRE_PRINCIPAL + TITULAIRE_SECONDAIRE)
- **Patrick → Sophia**: Mandataire sur compte épargne de sa fille
- **Marceus → Hotel Oasis**: Administrateur de l'entreprise
- **Alexandra → Hotel Oasis**: Observateur (architecte du projet)

### Instruments de Test

- **OBL-BRH-2025**: Obligation BRH 5% 2025-2030
- **OBL-BRH-2024-002**: Obligation BRH 5.5% 2024-2034
- **OBL-SOUV-2023**: Obligation Souveraine 4.2% 2023-2028
- **OBL-VERT-2024**: Obligation Verte Énergie 4% 2024-2027

---

## INSTALLATION ET DÉMARRAGE

### Prérequis
- Node.js v18+
- SQL Server ou Azure SQL Database
- npm ou yarn

### Installation

```bash
# 1. Installer les dépendances
npm install

# 2. Copier et configurer .env
cp .env.example .env
# Éditer .env avec vos credentials

# 3. Créer la base de données
# Exécuter les scripts SQL dans l'ordre:
#   1. sql_scripts/database_structure.sql
#   2. sql_scripts/vue_sql.sql
#   3. sql_scripts/test_simulation_base.sql

# 4. Tester la connexion
npm run test-db

# 5. Démarrer en développement
npm run dev

# 6. Démarrer en production
npm start
```

### Variables d'Environnement (.env)

```env
NODE_ENV=development
PORT=5000

DB_HOST=your-server.database.windows.net
DB_PORT=1433
DB_NAME=Db_test
DB_USER=your-username
DB_PASSWORD=your-password
DB_ENCRYPT=true

JWT_SECRET=change-this-to-a-random-secret
JWT_EXPIRES_IN=1h
REFRESH_TOKEN_EXPIRES_IN=7d

CORS_ORIGIN=http://localhost:3000
```

---

## TESTS

### Tests Unitaires
```bash
npm test
```

### Tests d'Intégration
```bash
npm run test:integration
```

### Tests E2E
```bash
npm run test:e2e
```

### Coverage
```bash
npm run test:coverage
```

---

## LOGGING ET MONITORING

### Logs
Les logs sont gérés par Winston:
- **info**: Événements importants (connexion DB, démarrage serveur)
- **error**: Erreurs (échecs DB, erreurs API)
- **debug**: Détails de développement

### Audit
Toutes les actions sensibles sont enregistrées dans `JournalAudit`:
- Connexions/déconnexions
- Créations de transactions
- Modifications de profil
- Accès aux comptes

---

## DÉPLOIEMENT

### Azure App Service (Recommandé)

```bash
# 1. Build
npm run build

# 2. Déployer sur Azure
az webapp up --name profin-bank-api --resource-group profin-rg

# 3. Configurer les variables d'environnement
az webapp config appsettings set --name profin-bank-api \
  --resource-group profin-rg \
  --settings NODE_ENV=production DB_HOST=xxx DB_NAME=xxx ...
```

### Docker (Alternative)

```dockerfile
FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production
COPY . .
EXPOSE 5000
CMD ["node", "server.js"]
```

```bash
docker build -t profin-bank-api .
docker run -p 5000:5000 --env-file .env profin-bank-api
```

---

## CONTRIBUER

### Conventions de Code
- **ESLint**: Standard JavaScript
- **Prettier**: Formatage automatique
- **Commits**: Convention Conventional Commits

### Workflow Git
```bash
# 1. Créer une branche
git checkout -b feature/nouvelle-fonctionnalite

# 2. Développer et tester
npm run dev
npm test

# 3. Commit
git add .
git commit -m "feat: ajout endpoint pour racheter souscription"

# 4. Push et PR
git push origin feature/nouvelle-fonctionnalite
```

---

## SUPPORT ET CONTACT

### Documentation
- [API Specification](./API_SPECIFICATION.md)
- [Architecture Technique](./ARCHITECTURE_TECHNIQUE.md)
- [Mapping Vues SQL](./MAPPING_VUES_SQL.md)

### Issues
Créer une issue sur le repository Git

---

## ROADMAP

### Version 1.0 (MVP) ✅
- [x] Authentification JWT
- [x] Dashboard multi-comptes
- [x] Gestion investissements
- [x] Historique transactions
- [x] Profil KYC
- [x] Système de rôles

### Version 1.1 (À venir)
- [ ] Notifications push (paiements d'intérêts)
- [ ] Documents PDF (relevés, attestations)
- [ ] Graphiques avancés (répartition par instrument)
- [ ] Export Excel
- [ ] API webhooks pour synchronisation

### Version 2.0 (Future)
- [ ] Application mobile (React Native)
- [ ] Authentification biométrique
- [ ] Chat support intégré
- [ ] Recommandations d'investissement IA
- [ ] Marketplace d'instruments

---

## LICENCE

Propriétaire - Profin Bank © 2024

---

## NOTES IMPORTANTES

### ⚠️ Sécurité
- **Ne jamais** commit le fichier `.env`
- **Toujours** valider les entrées utilisateur
- **Toujours** utiliser des requêtes paramétrées
- **Toujours** vérifier les permissions par rôle

### ⚠️ Performance
- Utiliser les index SQL existants
- Implémenter le caching (Redis) pour données fréquentes
- Pagination obligatoire pour listes longues
- Rate limiting activé

### ⚠️ Maintenance
- Backups quotidiens de la base de données
- Logs rotatifs (conserver 30 jours)
- Monitoring des erreurs (Sentry recommandé)
- Tests automatisés avant déploiement

---

**Dernière mise à jour**: 2024-11-01
**Version**: 1.0.0
**Auteur**: Équipe Profin Bank
