# PROCHAINES ÉTAPES - IMPLÉMENTATION BACKEND API
## Guide d'implémentation étape par étape

---

## PHASE 1: CONFIGURATION INITIALE (1-2 jours)

### Étape 1.1: Initialiser le projet Node.js

```bash
# Créer package.json
npm init -y

# Installer les dépendances principales
npm install express sequelize tedious dotenv cors helmet express-rate-limit winston morgan jsonwebtoken bcryptjs joi

# Installer les dépendances de développement
npm install -D nodemon jest supertest
```

### Étape 1.2: Créer la structure des dossiers

```bash
mkdir -p src/{config,models,controllers,services,middlewares,routes,utils,database/views}
mkdir -p tests/{unit,integration,e2e}
```

### Étape 1.3: Configurer les fichiers de base

**Créer `.env`:**
```env
NODE_ENV=development
PORT=5000
DB_HOST=your-server.database.windows.net
DB_PORT=1433
DB_NAME=Db_test
DB_USER=your-username
DB_PASSWORD=your-password
DB_ENCRYPT=true
JWT_SECRET=generate-a-random-secret-key-here
JWT_EXPIRES_IN=1h
REFRESH_TOKEN_EXPIRES_IN=7d
CORS_ORIGIN=http://localhost:3000
```

**Créer `server.js`:**
```javascript
require('dotenv').config();
const app = require('./src/app');
const sequelize = require('./src/config/database');
const logger = require('./src/utils/logger');

const PORT = process.env.PORT || 5000;

sequelize.authenticate()
  .then(() => {
    logger.info('✓ Connexion DB réussie');
    app.listen(PORT, () => {
      logger.info(`✓ Serveur démarré sur port ${PORT}`);
    });
  })
  .catch(err => {
    logger.error('✗ Erreur connexion DB:', err);
    process.exit(1);
  });
```

**Créer `src/app.js`:**
```javascript
const express = require('express');
const cors = require('cors');
const helmet = require('helmet');
const morgan = require('morgan');
const routes = require('./routes');
const errorHandler = require('./middlewares/errorHandler');

const app = express();

// Middlewares
app.use(helmet());
app.use(cors({ origin: process.env.CORS_ORIGIN }));
app.use(express.json());
app.use(express.urlencoded({ extended: true }));
app.use(morgan('combined'));

// Health check
app.get('/health', (req, res) => {
  res.json({ status: 'OK', timestamp: new Date().toISOString() });
});

// Routes API
app.use('/api/v1', routes);

// Error handler
app.use(errorHandler);

module.exports = app;
```

**Créer `package.json` scripts:**
```json
{
  "scripts": {
    "start": "node server.js",
    "dev": "nodemon server.js",
    "test": "jest",
    "test:watch": "jest --watch"
  }
}
```

---

## PHASE 2: CONFIGURATION & UTILS (1 jour)

### Étape 2.1: Configuration Database

**Créer `src/config/database.js`:**
```javascript
const { Sequelize } = require('sequelize');
require('dotenv').config();

const sequelize = new Sequelize(
  process.env.DB_NAME,
  process.env.DB_USER,
  process.env.DB_PASSWORD,
  {
    host: process.env.DB_HOST,
    port: process.env.DB_PORT || 1433,
    dialect: 'mssql',
    dialectOptions: {
      options: {
        encrypt: process.env.DB_ENCRYPT === 'true',
        trustServerCertificate: process.env.NODE_ENV === 'development'
      }
    },
    logging: process.env.NODE_ENV === 'development' ? console.log : false,
    pool: { max: 10, min: 0, acquire: 30000, idle: 10000 }
  }
);

module.exports = sequelize;
```

### Étape 2.2: Configuration JWT

**Créer `src/config/jwt.js`:**
```javascript
module.exports = {
  JWT_SECRET: process.env.JWT_SECRET,
  JWT_EXPIRES_IN: process.env.JWT_EXPIRES_IN || '1h',
  REFRESH_TOKEN_EXPIRES_IN: process.env.REFRESH_TOKEN_EXPIRES_IN || '7d'
};
```

### Étape 2.3: Logger Winston

**Créer `src/utils/logger.js`:**
```javascript
const winston = require('winston');

const logger = winston.createLogger({
  level: process.env.LOG_LEVEL || 'info',
  format: winston.format.combine(
    winston.format.timestamp(),
    winston.format.json()
  ),
  transports: [
    new winston.transports.File({ filename: 'logs/error.log', level: 'error' }),
    new winston.transports.File({ filename: 'logs/combined.log' })
  ]
});

if (process.env.NODE_ENV !== 'production') {
  logger.add(new winston.transports.Console({
    format: winston.format.simple()
  }));
}

module.exports = logger;
```

### Étape 2.4: Codes d'Erreur

**Créer `src/utils/errorCodes.js`:**
```javascript
module.exports = {
  UNAUTHORIZED: 'UNAUTHORIZED',
  FORBIDDEN: 'FORBIDDEN',
  NOT_FOUND: 'NOT_FOUND',
  VALIDATION_ERROR: 'VALIDATION_ERROR',
  INSUFFICIENT_BALANCE: 'INSUFFICIENT_BALANCE',
  INTERNAL_ERROR: 'INTERNAL_ERROR'
};
```

---

## PHASE 3: MODÈLES SEQUELIZE (2-3 jours)

### Priorité Haute (à faire en premier)

#### Étape 3.1: Créer les modèles essentiels

1. **`src/models/Client.js`** - Modèle de base client
2. **`src/models/ClientIndividuel.js`** - Extension client individuel
3. **`src/models/ClientAuthentification.js`** - Authentification
4. **`src/models/Compte.js`** - Comptes
5. **`src/models/CompteRole.js`** - Rôles multi-utilisateurs (CRITIQUE!)
6. **`src/models/RefreshToken.js`** - Tokens de refresh

#### Étape 3.2: Créer `src/models/index.js`

```javascript
const sequelize = require('../config/database');
const Client = require('./Client')(sequelize);
const ClientIndividuel = require('./ClientIndividuel')(sequelize);
const ClientAuthentification = require('./ClientAuthentification')(sequelize);
const Compte = require('./Compte')(sequelize);
const CompteRole = require('./CompteRole')(sequelize);
const RefreshToken = require('./RefreshToken')(sequelize);

// Définir les associations
Client.associate({ ClientIndividuel, ClientAuthentification, CompteRole });
ClientIndividuel.associate({ Client });
ClientAuthentification.associate({ Client });
Compte.associate({ CompteRole });
CompteRole.associate({ Client, Compte });
RefreshToken.associate({ Client });

module.exports = {
  sequelize,
  Client,
  ClientIndividuel,
  ClientAuthentification,
  Compte,
  CompteRole,
  RefreshToken
};
```

---

## PHASE 4: SERVICES DE BASE (2 jours)

### Étape 4.1: Permission Service (CRITIQUE!)

**Créer `src/services/permissionService.js`**

Ce service doit:
- Définir toutes les permissions par rôle
- Exposer `hasPermission(role, permission)`
- Exposer `getPermissions(role)`

### Étape 4.2: Account Access Service (CRITIQUE!)

**Créer `src/services/accountAccessService.js`**

Ce service doit:
- `checkAccess(clientId, compteId)` → retourne `{hasAccess, role}`
- `hasPermission(clientId, compteId, permission)` → boolean
- `getAccessibleAccounts(clientId)` → liste des comptes

### Étape 4.3: Auth Service

**Créer `src/services/authService.js`**

Ce service doit:
- `login(email, password)` → génère JWT + refresh token
- `verifyToken(token)` → vérifie et decode JWT
- `refreshAccessToken(refreshToken)` → nouveau access token
- `logout(refreshToken)` → révoque le refresh token

### Étape 4.4: Audit Service

**Créer `src/services/auditService.js`**

Ce service doit:
- `log(auditData)` → enregistre dans JournalAudit
- `logLogin(clientId, ip, userAgent)`
- `logLogout(clientId, ip)`
- `logTransaction(clientId, transactionId, data, ip)`

---

## PHASE 5: MIDDLEWARES (1 jour)

### Étape 5.1: Auth Middleware

**Créer `src/middlewares/auth.js`**
- Vérifie le JWT Bearer token
- Ajoute `req.user = { clientId, email, clientType }`

### Étape 5.2: Account Access Middleware

**Créer `src/middlewares/accountAccess.js`**
- `checkAccountAccess(permission)` → middleware factory
- Vérifie l'accès au compte et la permission
- Ajoute `req.accountRole` et `req.compteId`

### Étape 5.3: Error Handler Middleware

**Créer `src/middlewares/errorHandler.js`**
- Gère toutes les erreurs (Sequelize, custom, etc.)
- Retourne JSON standardisé

### Étape 5.4: Rate Limiter

**Créer `src/middlewares/rateLimiter.js`**
- 100 requêtes/minute par IP

---

## PHASE 6: ROUTES & CONTROLLERS (3-4 jours)

### Ordre d'Implémentation Recommandé

#### Jour 1: Authentification
1. **Routes:** `src/routes/auth.routes.js`
2. **Controller:** `src/controllers/authController.js`
   - `POST /auth/login`
   - `POST /auth/refresh`
   - `POST /auth/logout`
3. **Test:** Tester la connexion avec Marceus Jethro

#### Jour 2: Comptes & Profil
1. **Routes:** `src/routes/compte.routes.js`
2. **Controller:** `src/controllers/compteController.js`
   - `GET /comptes`
   - `GET /comptes/:id`
3. **Routes:** `src/routes/profil.routes.js`
4. **Controller:** `src/controllers/profilController.js`
   - `GET /profil`
5. **Test:** Vérifier qu'un client voit TOUS ses comptes (avec rôles)

#### Jour 3: Dashboard
1. **Routes:** `src/routes/dashboard.routes.js`
2. **Controller:** `src/controllers/dashboardController.js`
   - `GET /dashboard/overview`
   - `GET /dashboard/transactions/recentes`
   - `GET /dashboard/investissements`
   - `GET /dashboard/statistiques/mensuelles`
3. **Test:** Dashboard complet de Marceus (3 comptes)

#### Jour 4: Investissements
1. **Routes:** `src/routes/investissement.routes.js`
2. **Controller:** `src/controllers/investissementController.js`
   - `GET /investissements`
   - `GET /investissements/:id`
   - `GET /investissements/instruments/disponibles`
3. **Test:** Liste des investissements multi-comptes

#### Jour 5: Transactions
1. **Routes:** `src/routes/transaction.routes.js`
2. **Controller:** `src/controllers/transactionController.js`
   - `GET /transactions`
   - `GET /transactions/:id`
   - `GET /transactions/export/csv`
3. **Test:** Historique complet de toutes les transactions

---

## PHASE 7: FONCTIONNALITÉS AVANCÉES (2 jours)

### Étape 7.1: Créer Transactions

**Controller:** `src/controllers/transactionController.js`
- `POST /transactions/depot`
- `POST /transactions/retrait`

**Validations:**
- Vérifier solde disponible
- Vérifier permissions (role)
- Créer transaction + audit

### Étape 7.2: Créer Souscriptions

**Controller:** `src/controllers/investissementController.js`
- `POST /investissements/souscrire`

**Logique:**
- Vérifier montant minimum
- Vérifier solde disponible
- Créer souscription + transaction
- Mettre à jour soldes

---

## PHASE 8: TESTS (2-3 jours)

### Étape 8.1: Tests Unitaires

**Tester les services:**
```bash
tests/unit/services/permissionService.test.js
tests/unit/services/accountAccessService.test.js
tests/unit/services/authService.test.js
```

### Étape 8.2: Tests d'Intégration

**Tester les endpoints:**
```bash
tests/integration/auth.test.js
tests/integration/dashboard.test.js
tests/integration/comptes.test.js
tests/integration/investissements.test.js
```

### Étape 8.3: Tests E2E

**Scénarios complets:**
- Connexion → Dashboard → Nouvelle souscription → Déconnexion
- Connexion → Changement de compte → Dashboard actualisé
- Connexion en tant que mandataire → Accès limité

---

## PHASE 9: DOCUMENTATION & DÉPLOIEMENT (1-2 jours)

### Étape 9.1: Documentation Swagger

**Installer Swagger:**
```bash
npm install swagger-ui-express swagger-jsdoc
```

**Créer `src/config/swagger.js`**

### Étape 9.2: Déploiement Azure

**Créer Azure App Service:**
```bash
az group create --name profin-rg --location eastus
az appservice plan create --name profin-plan --resource-group profin-rg --sku B1
az webapp create --name profin-bank-api --resource-group profin-rg --plan profin-plan
```

**Configurer variables d'environnement Azure:**
```bash
az webapp config appsettings set --name profin-bank-api \
  --resource-group profin-rg \
  --settings NODE_ENV=production DB_HOST=xxx ...
```

---

## CHECKLIST FINALE AVANT DÉPLOIEMENT

### Sécurité ✅
- [ ] JWT_SECRET est une clé aléatoire forte (32+ caractères)
- [ ] Passwords hashés avec bcryptjs (10+ rounds)
- [ ] Rate limiting activé
- [ ] CORS configuré avec origin spécifique
- [ ] Helmet activé
- [ ] Validation Joi sur tous les inputs
- [ ] Requêtes SQL paramétrées (jamais de concaténation!)
- [ ] Pas de données sensibles dans les logs

### Performance ✅
- [ ] Index SQL vérifiés
- [ ] Pagination sur toutes les listes
- [ ] Connection pool configuré (max 10)
- [ ] Logs en mode production (pas de console.log)

### Fonctionnel ✅
- [ ] Tous les endpoints testés
- [ ] Tests unitaires passent (>80% coverage)
- [ ] Tests d'intégration passent
- [ ] Scénarios multi-rôles testés
- [ ] Filtrage par clientId vérifié sur TOUTES les requêtes
- [ ] Permissions par rôle vérifiées

### Monitoring ✅
- [ ] Winston configuré
- [ ] Logs fichiers rotatifs
- [ ] Audit activé (JournalAudit)
- [ ] Health check endpoint `/health`

---

## TEMPS ESTIMÉ TOTAL

| Phase | Durée | Effort |
|-------|-------|--------|
| Phase 1: Configuration | 1-2 jours | Junior OK |
| Phase 2: Config & Utils | 1 jour | Junior OK |
| Phase 3: Modèles | 2-3 jours | Intermédiaire |
| Phase 4: Services | 2 jours | Intermédiaire |
| Phase 5: Middlewares | 1 jour | Intermédiaire |
| Phase 6: Routes & Controllers | 3-4 jours | Senior |
| Phase 7: Fonctionnalités avancées | 2 jours | Senior |
| Phase 8: Tests | 2-3 jours | Intermédiaire |
| Phase 9: Doc & Déploiement | 1-2 jours | Intermédiaire |
| **TOTAL** | **15-20 jours** | **1-2 développeurs** |

---

## CONSEILS IMPORTANTS

### ⚠️ Pièges à Éviter

1. **Oublier le filtrage par ClientID** → TOUJOURS filtrer via ComptesRoles
2. **Ignorer les rôles** → TOUJOURS vérifier les permissions
3. **Requêtes SQL non sécurisées** → TOUJOURS utiliser des paramètres
4. **Pas de pagination** → Performance catastrophique sur grandes listes
5. **Logs sensibles** → JAMAIS logger les passwords ou tokens

### ✅ Bonnes Pratiques

1. **Commencer par les tests de données** → Vérifier que les vues SQL fonctionnent
2. **Tester avec plusieurs clients** → Notamment les cas multi-rôles
3. **Commiter souvent** → Git commit après chaque phase
4. **Documenter au fur et à mesure** → Commenter le code complexe
5. **Tester les cas limites** → Solde insuffisant, permissions refusées, etc.

---

## PROCHAINE ACTION IMMÉDIATE

**COMMENCER PAR:**

1. ✅ Créer le fichier `package.json` et installer les dépendances
2. ✅ Créer le fichier `.env` avec vos credentials SQL Server
3. ✅ Créer `server.js` et `src/app.js`
4. ✅ Créer `src/config/database.js`
5. ✅ Tester la connexion: `npm run dev` → vérifier "Connexion DB réussie"

**COMMANDE:**
```bash
node -e "const seq = require('./src/config/database'); seq.authenticate().then(() => console.log('OK')).catch(e => console.error(e))"
```

Si ça affiche "OK", vous êtes prêt pour la Phase 3 (Modèles) !

---

**Bonne chance! 🚀**
