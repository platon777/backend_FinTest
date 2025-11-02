# ARCHITECTURE TECHNIQUE - BACKEND API
## Profin Bank - Système de Gestion de Portefeuille Client

---

## STACK TECHNIQUE RECOMMANDÉE

### Backend
- **Runtime:** Node.js (v18+)
- **Framework:** Express.js
- **ORM:** Sequelize (pour SQL Server)
- **Authentification:** JWT (jsonwebtoken + bcryptjs)
- **Validation:** Joi ou express-validator
- **Documentation:** Swagger/OpenAPI

### Base de Données
- **SGBD:** Microsoft SQL Server (Azure SQL)
- **Driver:** tedious + sequelize

### Outils
- **Logging:** Winston
- **Monitoring:** Morgan (HTTP logs)
- **Environment:** dotenv
- **CORS:** cors middleware
- **Security:** helmet, express-rate-limit

---

## STRUCTURE DU PROJET

```
backend_FinTest/
├── src/
│   ├── config/
│   │   ├── database.js          # Configuration Sequelize
│   │   ├── jwt.js               # Configuration JWT
│   │   └── constants.js         # Constantes globales
│   │
│   ├── models/                  # Modèles Sequelize
│   │   ├── index.js             # Export tous les modèles
│   │   ├── Client.js
│   │   ├── ClientIndividuel.js
│   │   ├── ClientInstitutionnel.js
│   │   ├── Compte.js
│   │   ├── CompteRole.js
│   │   ├── Instrument.js
│   │   ├── Souscription.js
│   │   ├── Transaction.js
│   │   ├── ClientAuthentification.js
│   │   └── ...
│   │
│   ├── controllers/             # Logique métier
│   │   ├── authController.js
│   │   ├── compteController.js
│   │   ├── dashboardController.js
│   │   ├── investissementController.js
│   │   ├── transactionController.js
│   │   └── profilController.js
│   │
│   ├── services/                # Services réutilisables
│   │   ├── authService.js
│   │   ├── permissionService.js # Gestion permissions par rôle
│   │   ├── accountAccessService.js
│   │   ├── transactionService.js
│   │   ├── auditService.js
│   │   └── notificationService.js
│   │
│   ├── middlewares/
│   │   ├── auth.js              # Vérification JWT
│   │   ├── accountAccess.js     # Vérification accès compte
│   │   ├── permissions.js       # Vérification permissions
│   │   ├── validation.js        # Validation des données
│   │   ├── errorHandler.js      # Gestion globale erreurs
│   │   └── rateLimiter.js       # Rate limiting
│   │
│   ├── routes/
│   │   ├── index.js             # Routes principales
│   │   ├── auth.routes.js
│   │   ├── compte.routes.js
│   │   ├── dashboard.routes.js
│   │   ├── investissement.routes.js
│   │   ├── transaction.routes.js
│   │   └── profil.routes.js
│   │
│   ├── utils/
│   │   ├── logger.js            # Configuration Winston
│   │   ├── responseFormatter.js # Formatage réponses
│   │   ├── errorCodes.js        # Codes d'erreur
│   │   └── validators.js        # Fonctions validation
│   │
│   ├── database/
│   │   ├── views/               # Définitions vues SQL (DDL)
│   │   │   ├── vw_Dashboard_Overview.sql
│   │   │   ├── vw_MesComptes.sql
│   │   │   └── ...
│   │   └── migrations/          # Migrations (optionnel)
│   │
│   └── app.js                   # Application Express principale
│
├── sql_scripts/                 # Scripts SQL existants
│   ├── database_structure.sql
│   ├── test_simulation_base.sql
│   └── vue_sql.sql
│
├── tests/                       # Tests unitaires et intégration
│   ├── unit/
│   ├── integration/
│   └── e2e/
│
├── .env.example                 # Variables d'environnement exemple
├── .env                         # Variables d'environnement (git-ignored)
├── .gitignore
├── package.json
├── server.js                    # Point d'entrée
└── README.md
```

---

## MODÈLES SEQUELIZE

### Exemple: Client.js

```javascript
const { DataTypes } = require('sequelize');

module.exports = (sequelize) => {
  const Client = sequelize.define('Client', {
    ClientID: {
      type: DataTypes.INTEGER,
      primaryKey: true,
      autoIncrement: true,
      field: 'ClientID'
    },
    ClientType: {
      type: DataTypes.STRING(20),
      allowNull: false,
      validate: {
        isIn: [['INDIVIDUEL', 'INSTITUTIONNEL']]
      },
      field: 'ClientType'
    },
    ProfilRisque: {
      type: DataTypes.STRING(20),
      allowNull: true,
      validate: {
        isIn: [['CONSERVATEUR', 'MODERE', 'AGRESSIF']]
      },
      field: 'ProfilRisque'
    },
    StatutClient: {
      type: DataTypes.STRING(20),
      allowNull: false,
      defaultValue: 'ACTIF',
      validate: {
        isIn: [['ACTIF', 'SUSPENDU', 'FERME']]
      },
      field: 'StatutClient'
    },
    DateCreation: {
      type: DataTypes.DATE,
      allowNull: false,
      defaultValue: DataTypes.NOW,
      field: 'DateCreation'
    },
    DerniereMiseAJour: {
      type: DataTypes.DATE,
      allowNull: false,
      defaultValue: DataTypes.NOW,
      field: 'DerniereMiseAJour'
    }
  }, {
    tableName: 'Clients',
    timestamps: false, // Utiliser les champs DateCreation/DerniereMiseAJour
    schema: 'dbo'
  });

  // Associations
  Client.associate = (models) => {
    Client.hasOne(models.ClientIndividuel, {
      foreignKey: 'ClientID',
      as: 'individuel'
    });

    Client.hasOne(models.ClientInstitutionnel, {
      foreignKey: 'ClientID',
      as: 'institutionnel'
    });

    Client.hasMany(models.CompteRole, {
      foreignKey: 'ClientID',
      as: 'comptesRoles'
    });

    Client.hasOne(models.ClientAuthentification, {
      foreignKey: 'ClientID',
      as: 'authentification'
    });
  };

  return Client;
};
```

### Exemple: CompteRole.js

```javascript
const { DataTypes } = require('sequelize');

module.exports = (sequelize) => {
  const CompteRole = sequelize.define('CompteRole', {
    CompteRoleID: {
      type: DataTypes.INTEGER,
      primaryKey: true,
      autoIncrement: true,
      field: 'CompteRoleID'
    },
    CompteID: {
      type: DataTypes.INTEGER,
      allowNull: false,
      field: 'CompteID'
    },
    ClientID: {
      type: DataTypes.INTEGER,
      allowNull: false,
      field: 'ClientID'
    },
    Role: {
      type: DataTypes.STRING(30),
      allowNull: false,
      validate: {
        isIn: [[
          'TITULAIRE_PRINCIPAL',
          'TITULAIRE_SECONDAIRE',
          'MANDATAIRE',
          'OBSERVATEUR',
          'ADMINISTRATEUR',
          'BENEFICIAIRE'
        ]]
      },
      field: 'Role'
    },
    DateDebut: {
      type: DataTypes.DATE,
      allowNull: false,
      defaultValue: DataTypes.NOW,
      field: 'DateDebut'
    },
    DateFin: {
      type: DataTypes.DATE,
      allowNull: true,
      field: 'DateFin'
    },
    EstActif: {
      type: DataTypes.BOOLEAN,
      allowNull: false,
      defaultValue: true,
      field: 'EstActif'
    }
  }, {
    tableName: 'ComptesRoles',
    timestamps: false,
    schema: 'dbo',
    indexes: [
      {
        fields: ['ClientID', 'EstActif']
      },
      {
        unique: true,
        fields: ['CompteID', 'ClientID', 'Role']
      }
    ]
  });

  // Associations
  CompteRole.associate = (models) => {
    CompteRole.belongsTo(models.Client, {
      foreignKey: 'ClientID',
      as: 'client'
    });

    CompteRole.belongsTo(models.Compte, {
      foreignKey: 'CompteID',
      as: 'compte'
    });
  };

  return CompteRole;
};
```

---

## SERVICES CRITIQUES

### 1. Permission Service

```javascript
// src/services/permissionService.js

const PERMISSIONS = {
  TITULAIRE_PRINCIPAL: {
    canView: true,
    canDeposit: true,
    canWithdraw: true,
    canInvest: true,
    canDivest: true,
    canManageRoles: true,
    canCloseAccount: true
  },
  TITULAIRE_SECONDAIRE: {
    canView: true,
    canDeposit: true,
    canWithdraw: true,
    canInvest: true,
    canDivest: true,
    canManageRoles: false,
    canCloseAccount: false
  },
  MANDATAIRE: {
    canView: true,
    canDeposit: true,
    canWithdraw: true,
    canInvest: true,
    canDivest: false,
    canManageRoles: false,
    canCloseAccount: false
  },
  OBSERVATEUR: {
    canView: true,
    canDeposit: false,
    canWithdraw: false,
    canInvest: false,
    canDivest: false,
    canManageRoles: false,
    canCloseAccount: false
  },
  ADMINISTRATEUR: {
    canView: true,
    canDeposit: true,
    canWithdraw: true,
    canInvest: true,
    canDivest: true,
    canManageRoles: true,
    canCloseAccount: true
  },
  BENEFICIAIRE: {
    canView: false,
    canDeposit: false,
    canWithdraw: false,
    canInvest: false,
    canDivest: false,
    canManageRoles: false,
    canCloseAccount: false
  }
};

class PermissionService {
  /**
   * Vérifie si un rôle a une permission spécifique
   * @param {string} role - Le rôle du client sur le compte
   * @param {string} permission - La permission à vérifier (ex: 'canDeposit')
   * @returns {boolean}
   */
  static hasPermission(role, permission) {
    const rolePermissions = PERMISSIONS[role];
    if (!rolePermissions) {
      return false;
    }
    return rolePermissions[permission] === true;
  }

  /**
   * Obtient toutes les permissions pour un rôle
   * @param {string} role
   * @returns {object}
   */
  static getPermissions(role) {
    return PERMISSIONS[role] || {};
  }

  /**
   * Vérifie si le rôle permet de consulter (minimum requis)
   * @param {string} role
   * @returns {boolean}
   */
  static canAccessAccount(role) {
    return this.hasPermission(role, 'canView');
  }
}

module.exports = PermissionService;
```

### 2. Account Access Service

```javascript
// src/services/accountAccessService.js

const { CompteRole, Compte } = require('../models');
const PermissionService = require('./permissionService');

class AccountAccessService {
  /**
   * Vérifie si un client a accès à un compte
   * @param {number} clientId
   * @param {number} compteId
   * @returns {Promise<{hasAccess: boolean, role: string|null}>}
   */
  static async checkAccess(clientId, compteId) {
    const compteRole = await CompteRole.findOne({
      where: {
        ClientID: clientId,
        CompteID: compteId,
        EstActif: true
      }
    });

    if (!compteRole) {
      return { hasAccess: false, role: null };
    }

    return {
      hasAccess: true,
      role: compteRole.Role
    };
  }

  /**
   * Vérifie si un client a une permission spécifique sur un compte
   * @param {number} clientId
   * @param {number} compteId
   * @param {string} permission - Ex: 'canDeposit', 'canWithdraw'
   * @returns {Promise<boolean>}
   */
  static async hasPermission(clientId, compteId, permission) {
    const { hasAccess, role } = await this.checkAccess(clientId, compteId);

    if (!hasAccess) {
      return false;
    }

    return PermissionService.hasPermission(role, permission);
  }

  /**
   * Récupère tous les comptes accessibles par un client
   * @param {number} clientId
   * @returns {Promise<Array>}
   */
  static async getAccessibleAccounts(clientId) {
    const comptesRoles = await CompteRole.findAll({
      where: {
        ClientID: clientId,
        EstActif: true
      },
      include: [{
        model: Compte,
        as: 'compte',
        where: {
          StatutCompte: 'ACTIF'
        }
      }]
    });

    return comptesRoles.map(cr => ({
      compteId: cr.CompteID,
      role: cr.Role,
      compte: cr.compte
    }));
  }
}

module.exports = AccountAccessService;
```

### 3. Audit Service

```javascript
// src/services/auditService.js

const { JournalAudit } = require('../models');

class AuditService {
  /**
   * Enregistre une action dans le journal d'audit
   * @param {object} auditData
   */
  static async log(auditData) {
    const {
      clientId = null,
      typeAction,
      tableCiblee,
      enregistrementId = null,
      ancienneValeur = null,
      nouvelleValeur = null,
      adresseIP = null,
      userAgent = null
    } = auditData;

    try {
      await JournalAudit.create({
        ClientID: clientId,
        TypeAction: typeAction,
        TableCiblee: tableCiblee,
        EnregistrementID: enregistrementId,
        AncienneValeur: ancienneValeur ? JSON.stringify(ancienneValeur) : null,
        NouvelleValeur: nouvelleValeur ? JSON.stringify(nouvelleValeur) : null,
        AdresseIP: adresseIP,
        UserAgent: userAgent,
        DateAction: new Date()
      });
    } catch (error) {
      console.error('Erreur lors de l\'audit:', error);
      // Ne pas bloquer l'opération si l'audit échoue
    }
  }

  /**
   * Enregistre une connexion
   */
  static async logLogin(clientId, adresseIP, userAgent) {
    return this.log({
      clientId,
      typeAction: 'LOGIN',
      tableCiblee: 'ClientsAuthentification',
      enregistrementId: clientId,
      nouvelleValeur: { action: 'Connexion réussie' },
      adresseIP,
      userAgent
    });
  }

  /**
   * Enregistre une déconnexion
   */
  static async logLogout(clientId, adresseIP) {
    return this.log({
      clientId,
      typeAction: 'LOGOUT',
      tableCiblee: 'ClientsAuthentification',
      enregistrementId: clientId,
      nouvelleValeur: { action: 'Déconnexion' },
      adresseIP
    });
  }

  /**
   * Enregistre une transaction
   */
  static async logTransaction(clientId, transactionId, transactionData, adresseIP) {
    return this.log({
      clientId,
      typeAction: 'CREATE',
      tableCiblee: 'Transactions',
      enregistrementId: transactionId,
      nouvelleValeur: transactionData,
      adresseIP
    });
  }
}

module.exports = AuditService;
```

---

## MIDDLEWARES

### 1. Authentication Middleware

```javascript
// src/middlewares/auth.js

const jwt = require('jsonwebtoken');
const { JWT_SECRET } = require('../config/jwt');

const authMiddleware = async (req, res, next) => {
  try {
    // Récupérer le token du header
    const authHeader = req.headers.authorization;

    if (!authHeader || !authHeader.startsWith('Bearer ')) {
      return res.status(401).json({
        success: false,
        error: {
          code: 'UNAUTHORIZED',
          message: 'Token manquant ou invalide'
        }
      });
    }

    const token = authHeader.substring(7); // Enlever "Bearer "

    // Vérifier le token
    const decoded = jwt.verify(token, JWT_SECRET);

    // Ajouter les infos du client à la requête
    req.user = {
      clientId: decoded.clientId,
      email: decoded.email,
      clientType: decoded.clientType
    };

    next();
  } catch (error) {
    if (error.name === 'TokenExpiredError') {
      return res.status(401).json({
        success: false,
        error: {
          code: 'TOKEN_EXPIRED',
          message: 'Token expiré'
        }
      });
    }

    return res.status(401).json({
      success: false,
      error: {
        code: 'UNAUTHORIZED',
        message: 'Token invalide'
      }
    });
  }
};

module.exports = authMiddleware;
```

### 2. Account Access Middleware

```javascript
// src/middlewares/accountAccess.js

const AccountAccessService = require('../services/accountAccessService');
const PermissionService = require('../services/permissionService');

/**
 * Middleware pour vérifier l'accès à un compte
 * @param {string} permission - Permission requise (ex: 'canDeposit')
 */
const checkAccountAccess = (permission = 'canView') => {
  return async (req, res, next) => {
    try {
      const { clientId } = req.user;
      const compteId = parseInt(req.params.compteId) || parseInt(req.body.compteId);

      if (!compteId) {
        return res.status(400).json({
          success: false,
          error: {
            code: 'INVALID_REQUEST',
            message: 'ID du compte manquant'
          }
        });
      }

      // Vérifier l'accès au compte
      const { hasAccess, role } = await AccountAccessService.checkAccess(clientId, compteId);

      if (!hasAccess) {
        return res.status(403).json({
          success: false,
          error: {
            code: 'FORBIDDEN',
            message: 'Vous n\'avez pas accès à ce compte'
          }
        });
      }

      // Vérifier la permission
      const hasPermission = PermissionService.hasPermission(role, permission);

      if (!hasPermission) {
        return res.status(403).json({
          success: false,
          error: {
            code: 'INSUFFICIENT_PERMISSIONS',
            message: `Votre rôle (${role}) ne permet pas cette action`,
            details: {
              roleActuel: role,
              permissionRequise: permission
            }
          }
        });
      }

      // Ajouter le rôle à la requête pour utilisation ultérieure
      req.accountRole = role;
      req.compteId = compteId;

      next();
    } catch (error) {
      console.error('Erreur vérification accès compte:', error);
      return res.status(500).json({
        success: false,
        error: {
          code: 'INTERNAL_ERROR',
          message: 'Erreur lors de la vérification des accès'
        }
      });
    }
  };
};

module.exports = checkAccountAccess;
```

### 3. Error Handler Middleware

```javascript
// src/middlewares/errorHandler.js

const logger = require('../utils/logger');

const errorHandler = (err, req, res, next) => {
  // Logger l'erreur
  logger.error('Erreur:', {
    message: err.message,
    stack: err.stack,
    url: req.url,
    method: req.method,
    ip: req.ip
  });

  // Erreur de validation Sequelize
  if (err.name === 'SequelizeValidationError') {
    return res.status(422).json({
      success: false,
      error: {
        code: 'VALIDATION_ERROR',
        message: 'Erreur de validation des données',
        details: err.errors.map(e => ({
          field: e.path,
          message: e.message
        }))
      }
    });
  }

  // Erreur de contrainte unique
  if (err.name === 'SequelizeUniqueConstraintError') {
    return res.status(409).json({
      success: false,
      error: {
        code: 'CONFLICT',
        message: 'Cette ressource existe déjà',
        details: err.errors.map(e => ({
          field: e.path,
          message: e.message
        }))
      }
    });
  }

  // Erreur par défaut
  return res.status(500).json({
    success: false,
    error: {
      code: 'INTERNAL_ERROR',
      message: process.env.NODE_ENV === 'production'
        ? 'Une erreur est survenue'
        : err.message
    }
  });
};

module.exports = errorHandler;
```

---

## EXEMPLE DE CONTROLLER

### Dashboard Controller

```javascript
// src/controllers/dashboardController.js

const { sequelize } = require('../models');
const AccountAccessService = require('../services/accountAccessService');

class DashboardController {
  /**
   * GET /dashboard/overview
   */
  static async getOverview(req, res, next) {
    try {
      const { clientId } = req.user;
      const { compteId } = req.query;

      // Construire la clause WHERE
      let whereClause = `cr.ClientID = @clientId AND cr.EstActif = 1`;
      const replacements = { clientId };

      if (compteId) {
        whereClause += ` AND cr.CompteID = @compteId`;
        replacements.compteId = compteId;
      }

      // Requête SQL utilisant la vue
      const query = `
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
        WHERE ${whereClause}
          AND cpt.StatutCompte = 'ACTIF'
          AND cr.Role IN ('TITULAIRE_PRINCIPAL', 'MANDATAIRE', 'OBSERVATEUR')
        GROUP BY cr.ClientID, cr.CompteID, cpt.NumeroCompte, cpt.Devise
      `;

      const results = await sequelize.query(query, {
        replacements,
        type: sequelize.QueryTypes.SELECT
      });

      // Calculer les totaux globaux
      const totals = results.reduce((acc, row) => {
        acc.valeurTotale += parseFloat(row.ValeurTotale || 0);
        acc.rendementTotal += parseFloat(row.RendementTotal || 0);
        acc.totalInvesti += parseFloat(row.TotalInvesti || 0);
        acc.nombreSouscriptions += parseInt(row.NombreSouscriptionsActives || 0);
        return acc;
      }, {
        valeurTotale: 0,
        rendementTotal: 0,
        totalInvesti: 0,
        nombreSouscriptions: 0
      });

      const pourcentageRendement = totals.totalInvesti > 0
        ? (totals.rendementTotal / totals.totalInvesti) * 100
        : 0;

      return res.json({
        success: true,
        data: {
          valeurTotale: totals.valeurTotale,
          rendementTotal: totals.rendementTotal,
          pourcentageRendement: parseFloat(pourcentageRendement.toFixed(2)),
          nombreSouscriptionsActives: totals.nombreSouscriptions,
          totalInvesti: totals.totalInvesti,
          devise: results.length > 0 ? results[0].DeviseCompte : 'USD',
          comptes: results.map(row => ({
            compteId: row.CompteID,
            numeroCompte: row.NumeroCompte,
            valeurTotale: parseFloat(row.ValeurTotale),
            rendementTotal: parseFloat(row.RendementTotal),
            pourcentageRendement: parseFloat(row.PourcentageRendement).toFixed(2)
          }))
        }
      });
    } catch (error) {
      next(error);
    }
  }

  /**
   * GET /dashboard/transactions/recentes
   */
  static async getRecentTransactions(req, res, next) {
    try {
      const { clientId } = req.user;
      const { compteId, limit = 3 } = req.query;

      let whereClause = `cr.ClientID = @clientId AND cr.EstActif = 1`;
      const replacements = { clientId, limit: parseInt(limit) };

      if (compteId) {
        whereClause += ` AND cr.CompteID = @compteId`;
        replacements.compteId = compteId;
      }

      const query = `
        SELECT TOP (@limit)
          t.TransactionID,
          t.TypeTransaction,
          t.Description,
          t.Montant,
          t.Devise,
          t.DateCreation,
          t.DateExecution,
          t.StatutTransaction,
          cptSrc.NumeroCompte AS NumeroCompteSource,
          cptDest.NumeroCompte AS NumeroCompteDestination
        FROM ComptesRoles cr
        INNER JOIN Comptes cpt ON cr.CompteID = cpt.CompteID
        LEFT JOIN Transactions t ON (t.CompteSource = cpt.CompteID OR t.CompteDestination = cpt.CompteID)
        LEFT JOIN Comptes cptSrc ON t.CompteSource = cptSrc.CompteID
        LEFT JOIN Comptes cptDest ON t.CompteDestination = cptDest.CompteID
        WHERE ${whereClause}
          AND cr.Role IN ('TITULAIRE_PRINCIPAL', 'MANDATAIRE', 'OBSERVATEUR')
        ORDER BY ISNULL(t.DateExecution, t.DateCreation) DESC
      `;

      const results = await sequelize.query(query, {
        replacements,
        type: sequelize.QueryTypes.SELECT
      });

      return res.json({
        success: true,
        data: results.map(row => ({
          transactionId: row.TransactionID,
          typeTransaction: row.TypeTransaction,
          description: row.Description,
          montant: parseFloat(row.Montant),
          devise: row.Devise,
          dateCreation: row.DateCreation,
          dateExecution: row.DateExecution,
          statut: row.StatutTransaction,
          compteSource: row.NumeroCompteSource,
          compteDestination: row.NumeroCompteDestination
        }))
      });
    } catch (error) {
      next(error);
    }
  }
}

module.exports = DashboardController;
```

---

## CONFIGURATION

### .env.example

```env
# Serveur
NODE_ENV=development
PORT=5000

# Base de données SQL Server
DB_HOST=your-server.database.windows.net
DB_PORT=1433
DB_NAME=Db_test
DB_USER=your-username
DB_PASSWORD=your-password
DB_ENCRYPT=true

# JWT
JWT_SECRET=your-super-secret-jwt-key-change-this-in-production
JWT_EXPIRES_IN=1h
REFRESH_TOKEN_EXPIRES_IN=7d

# CORS
CORS_ORIGIN=http://localhost:3000

# Rate Limiting
RATE_LIMIT_WINDOW_MS=60000
RATE_LIMIT_MAX_REQUESTS=100

# Logging
LOG_LEVEL=info
```

### config/database.js

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
    pool: {
      max: 10,
      min: 0,
      acquire: 30000,
      idle: 10000
    }
  }
);

module.exports = sequelize;
```

---

## DÉMARRAGE DU PROJET

### package.json

```json
{
  "name": "profin-bank-api",
  "version": "1.0.0",
  "description": "API Backend pour Profin Bank",
  "main": "server.js",
  "scripts": {
    "start": "node server.js",
    "dev": "nodemon server.js",
    "test": "jest",
    "test:watch": "jest --watch"
  },
  "dependencies": {
    "express": "^4.18.2",
    "sequelize": "^6.35.0",
    "tedious": "^16.6.1",
    "jsonwebtoken": "^9.0.2",
    "bcryptjs": "^2.4.3",
    "dotenv": "^16.3.1",
    "cors": "^2.8.5",
    "helmet": "^7.1.0",
    "express-rate-limit": "^7.1.5",
    "winston": "^3.11.0",
    "morgan": "^1.10.0",
    "joi": "^17.11.0"
  },
  "devDependencies": {
    "nodemon": "^3.0.2",
    "jest": "^29.7.0",
    "supertest": "^6.3.3"
  }
}
```

### server.js

```javascript
require('dotenv').config();
const app = require('./src/app');
const sequelize = require('./src/config/database');
const logger = require('./src/utils/logger');

const PORT = process.env.PORT || 5000;

// Test connexion DB
sequelize.authenticate()
  .then(() => {
    logger.info('✓ Connexion à la base de données réussie');

    // Démarrer le serveur
    app.listen(PORT, () => {
      logger.info(`✓ Serveur démarré sur le port ${PORT}`);
      logger.info(`✓ Environnement: ${process.env.NODE_ENV}`);
    });
  })
  .catch(err => {
    logger.error('✗ Erreur de connexion à la base de données:', err);
    process.exit(1);
  });

// Gestion arrêt gracieux
process.on('SIGTERM', () => {
  logger.info('SIGTERM reçu, arrêt gracieux...');
  sequelize.close().then(() => {
    logger.info('✓ Connexion DB fermée');
    process.exit(0);
  });
});
```

---

## SÉCURITÉ

### Recommandations

1. **Toujours valider les entrées** avec Joi ou express-validator
2. **Utiliser des requêtes paramétrées** (protection contre SQL Injection)
3. **Hasher les mots de passe** avec bcryptjs (10 rounds minimum)
4. **Implémenter le rate limiting** pour éviter les attaques brute-force
5. **Utiliser HTTPS** en production
6. **Activer CORS** seulement pour les domaines autorisés
7. **Logs sensibles** : ne jamais logger les mots de passe ou tokens
8. **Variables d'environnement** : ne jamais commit .env
9. **Helmet** : ajouter des headers de sécurité HTTP
10. **Audit logging** : tracer toutes les actions sensibles

---

## TESTS

### Exemple de test unitaire

```javascript
// tests/unit/services/permissionService.test.js

const PermissionService = require('../../../src/services/permissionService');

describe('PermissionService', () => {
  test('TITULAIRE_PRINCIPAL peut tout faire', () => {
    expect(PermissionService.hasPermission('TITULAIRE_PRINCIPAL', 'canView')).toBe(true);
    expect(PermissionService.hasPermission('TITULAIRE_PRINCIPAL', 'canDeposit')).toBe(true);
    expect(PermissionService.hasPermission('TITULAIRE_PRINCIPAL', 'canWithdraw')).toBe(true);
  });

  test('OBSERVATEUR peut seulement voir', () => {
    expect(PermissionService.hasPermission('OBSERVATEUR', 'canView')).toBe(true);
    expect(PermissionService.hasPermission('OBSERVATEUR', 'canDeposit')).toBe(false);
    expect(PermissionService.hasPermission('OBSERVATEUR', 'canWithdraw')).toBe(false);
  });
});
```

---

## CONCLUSION

Cette architecture vous permet de:

✅ **Gérer les rôles multi-utilisateurs** de manière sécurisée
✅ **Filtrer les données** selon les accès du client
✅ **Auditer toutes les actions** critiques
✅ **Scalabilité** avec une architecture modulaire
✅ **Maintenabilité** avec séparation des responsabilités
✅ **Sécurité** avec validation, authentification, et rate limiting

Prochaines étapes recommandées:
1. Implémenter les modèles Sequelize
2. Créer les services de base
3. Implémenter les middlewares
4. Développer les controllers et routes
5. Écrire les tests
6. Documenter avec Swagger
