# API SPECIFICATION - PROFIN BANK
## Architecture Backend pour Application de Gestion de Portefeuille Client

---

## APERÇU GÉNÉRAL

Cette API RESTful permet à un système multi-rôles où:
- Un client peut avoir accès à **plusieurs comptes** avec **différents rôles**
- Rôles supportés: `TITULAIRE_PRINCIPAL`, `TITULAIRE_SECONDAIRE`, `MANDATAIRE`, `OBSERVATEUR`, `ADMINISTRATEUR`, `BENEFICIAIRE`
- Chaque endpoint doit filtrer les données selon le rôle du client sur le compte

### Base URL
```
http://localhost:5000/api/v1
```

### Authentification
Toutes les routes (sauf `/auth/*`) nécessitent un JWT Bearer token:
```
Authorization: Bearer {jwt_token}
```

Le JWT contient:
```json
{
  "clientId": 1,
  "email": "marceus.jethro@email.ht",
  "clientType": "INDIVIDUEL",
  "iat": 1234567890,
  "exp": 1234571490
}
```

---

## 1. AUTHENTIFICATION

### 1.1 Login
**POST** `/auth/login`

**Body:**
```json
{
  "email": "marceus.jethro@email.ht",
  "password": "password123"
}
```

**Response 200:**
```json
{
  "success": true,
  "data": {
    "accessToken": "eyJhbGciOiJIUzI1NiIs...",
    "refreshToken": "dGhpcyBpcyBhIHJlZnJl...",
    "expiresIn": 3600,
    "client": {
      "clientId": 1,
      "email": "marceus.jethro@email.ht",
      "nomComplet": "Marceus Jethro",
      "clientType": "INDIVIDUEL",
      "profilRisque": "MODERE"
    }
  }
}
```

### 1.2 Refresh Token
**POST** `/auth/refresh`

**Body:**
```json
{
  "refreshToken": "dGhpcyBpcyBhIHJlZnJl..."
}
```

**Response 200:**
```json
{
  "success": true,
  "data": {
    "accessToken": "eyJhbGciOiJIUzI1NiIs...",
    "expiresIn": 3600
  }
}
```

### 1.3 Logout
**POST** `/auth/logout`

**Headers:** `Authorization: Bearer {token}`

**Response 200:**
```json
{
  "success": true,
  "message": "Déconnexion réussie"
}
```

---

## 2. COMPTES

### 2.1 Liste des Comptes Accessibles
**GET** `/comptes`

Retourne tous les comptes auxquels le client authentifié a accès (tous rôles confondus).

**Query Parameters:**
- `actif` (optional): `true` | `false` - Filtre par statut actif

**Response 200:**
```json
{
  "success": true,
  "data": [
    {
      "compteId": 1,
      "numeroCompte": "INV-2023-230001",
      "typeCompte": "INVESTISSEMENT",
      "devise": "USD",
      "soldeTotal": 52600.00,
      "soldeDisponible": 2600.00,
      "dateOuverture": "2023-06-15T00:00:00Z",
      "statut": "ACTIF",
      "role": "TITULAIRE_PRINCIPAL",
      "typeRelation": "Personnel",
      "estComptePersonnel": true,
      "titulaire": {
        "nom": "Marceus Jethro"
      }
    },
    {
      "compteId": 5,
      "numeroCompte": "INV-2023-230005",
      "typeCompte": "INVESTISSEMENT",
      "devise": "USD",
      "soldeTotal": 455000.00,
      "soldeDisponible": 5000.00,
      "dateOuverture": "2023-06-01T00:00:00Z",
      "statut": "ACTIF",
      "role": "ADMINISTRATEUR",
      "typeRelation": "Administrateur",
      "estComptePersonnel": false,
      "titulaire": {
        "nom": "Hotel Oasis SARL"
      }
    }
  ]
}
```

### 2.2 Détails d'un Compte
**GET** `/comptes/:compteId`

**Response 200:**
```json
{
  "success": true,
  "data": {
    "compteId": 1,
    "numeroCompte": "INV-2023-230001",
    "typeCompte": "INVESTISSEMENT",
    "devise": "USD",
    "soldeTotal": 52600.00,
    "soldeDisponible": 2600.00,
    "dateOuverture": "2023-06-15T00:00:00Z",
    "dateFermeture": null,
    "statut": "ACTIF",
    "role": "TITULAIRE_PRINCIPAL",
    "permissions": {
      "peutConsulter": true,
      "peutDeposer": true,
      "peutRetirer": true,
      "peutInvestir": true,
      "peutAdministrer": true
    },
    "titulaires": [
      {
        "clientId": 1,
        "nom": "Marceus Jethro",
        "role": "TITULAIRE_PRINCIPAL"
      }
    ]
  }
}
```

---

## 3. DASHBOARD

### 3.1 Vue d'Ensemble du Portefeuille
**GET** `/dashboard/overview`

Retourne une vue agrégée de TOUS les comptes accessibles par le client.

**Query Parameters:**
- `compteId` (optional): Si fourni, filtre pour un seul compte

**Response 200:**
```json
{
  "success": true,
  "data": {
    "valeurTotale": 52600.00,
    "rendementTotal": 2000.00,
    "pourcentageRendement": 5.2,
    "nombreSouscriptionsActives": 2,
    "totalInvesti": 50000.00,
    "devise": "USD",
    "comptes": [
      {
        "compteId": 1,
        "numeroCompte": "INV-2023-230001",
        "valeurTotale": 52600.00,
        "rendementTotal": 2000.00,
        "pourcentageRendement": 5.2
      }
    ]
  }
}
```

### 3.2 Dernières Transactions
**GET** `/dashboard/transactions/recentes`

**Query Parameters:**
- `compteId` (optional): Filtre par compte
- `limit` (optional, default=3): Nombre de transactions

**Response 200:**
```json
{
  "success": true,
  "data": [
    {
      "transactionId": 1,
      "typeTransaction": "DEPOT",
      "description": "Virement entrant salaire",
      "montant": 5000.00,
      "devise": "USD",
      "dateCreation": "2024-07-20T00:00:00Z",
      "dateExecution": "2024-07-20T00:00:00Z",
      "statut": "EXECUTEE",
      "compteSource": null,
      "compteDestination": "INV-2023-230001"
    },
    {
      "transactionId": 3,
      "typeTransaction": "RETRAIT",
      "description": "Retrait en ligne",
      "montant": -1000.00,
      "devise": "USD",
      "dateCreation": "2024-07-25T00:00:00Z",
      "dateExecution": null,
      "statut": "EN_ATTENTE",
      "compteSource": "INV-2023-230001",
      "compteDestination": null
    }
  ]
}
```

### 3.3 Investissements Actifs (Aperçu)
**GET** `/dashboard/investissements`

**Query Parameters:**
- `compteId` (optional): Filtre par compte

**Response 200:**
```json
{
  "success": true,
  "data": [
    {
      "souscriptionId": 2001,
      "compteId": 1,
      "nomInstrument": "Obligation BRH 5.5% 2025",
      "codeInstrument": "OBL-BRH-2025",
      "montantInvesti": 20000.00,
      "valeurActuelle": 20900.00,
      "tauxSouscription": 5.5,
      "dateMaturite": "2025-06-14T00:00:00Z",
      "interetsAccumules": 900.00,
      "progressionMaturite": 75.5,
      "statut": "ACTIVE"
    }
  ]
}
```

### 3.4 Statistiques Mensuelles (Graphique)
**GET** `/dashboard/statistiques/mensuelles`

**Query Parameters:**
- `compteId` (optional): Filtre par compte
- `mois` (optional, default=12): Nombre de mois

**Response 200:**
```json
{
  "success": true,
  "data": {
    "periodes": [
      {
        "mois": "Janvier",
        "dateMois": "2024-01-01",
        "valeurPortefeuille": 45000.00,
        "nombreSouscriptions": 1
      },
      {
        "mois": "Février",
        "dateMois": "2024-02-01",
        "valeurPortefeuille": 45300.00,
        "nombreSouscriptions": 2
      },
      {
        "mois": "Mars",
        "dateMois": "2024-03-01",
        "valeurPortefeuille": 46200.00,
        "nombreSouscriptions": 2
      },
      {
        "mois": "Avril",
        "dateMois": "2024-04-01",
        "valeurPortefeuille": 47800.00,
        "nombreSouscriptions": 2
      },
      {
        "mois": "Mai",
        "dateMois": "2024-05-01",
        "valeurPortefeuille": 49100.00,
        "nombreSouscriptions": 2
      },
      {
        "mois": "Juin",
        "dateMois": "2024-06-01",
        "valeurPortefeuille": 50500.00,
        "nombreSouscriptions": 2
      }
    ]
  }
}
```

---

## 4. INVESTISSEMENTS (SOUSCRIPTIONS)

### 4.1 Liste des Investissements
**GET** `/investissements`

**Query Parameters:**
- `compteId` (optional): Filtre par compte
- `statut` (optional): `ACTIVE` | `MATURE` | `RACHETEE`
- `page` (optional, default=1)
- `limit` (optional, default=20)
- `sort` (optional): `dateMaturite` | `valeurActuelle` | `rendement`

**Response 200:**
```json
{
  "success": true,
  "data": {
    "investissements": [
      {
        "souscriptionId": 2001,
        "compteId": 1,
        "numeroCompte": "INV-2023-230001",
        "instrument": {
          "instrumentId": 101,
          "code": "OBL-BRH-2025",
          "nom": "Obligation BRH 5.5% 2025",
          "emetteur": "Banque de la République d'Haïti",
          "typeInstrument": "Obligation",
          "tauxRendementAnnuel": 5.5,
          "frequencePaiementInterets": "SEMESTRIEL"
        },
        "montantInvesti": 20000.00,
        "valeurActuelle": 20900.00,
        "nombreUnites": 20.0,
        "tauxSouscription": 5.5,
        "tmaReel": 5.8,
        "interetsAccumules": 900.00,
        "dateSouscription": "2023-06-15T00:00:00Z",
        "dateMaturite": "2025-06-14T00:00:00Z",
        "joursRestants": 180,
        "progressionPourcentage": 75.5,
        "gainPerte": 900.00,
        "gainPertePourcentage": 4.5,
        "statut": "ACTIVE"
      }
    ],
    "pagination": {
      "page": 1,
      "limit": 20,
      "total": 13,
      "totalPages": 1
    },
    "resume": {
      "totalInvesti": 50000.00,
      "valeurActuelleTotale": 52000.00,
      "gainPerteTotale": 2000.00,
      "rendementMoyen": 5.2
    }
  }
}
```

### 4.2 Détails d'un Investissement
**GET** `/investissements/:souscriptionId`

**Response 200:**
```json
{
  "success": true,
  "data": {
    "souscriptionId": 2001,
    "compteId": 1,
    "numeroCompte": "INV-2023-230001",
    "instrument": {
      "instrumentId": 101,
      "code": "OBL-BRH-2025",
      "nom": "Obligation BRH 5.5% 2025",
      "description": "Obligation souveraine émise par la BRH",
      "emetteur": "Banque de la République d'Haïti",
      "typeInstrument": "Obligation",
      "tauxRendementAnnuel": 5.5,
      "dateEmission": "2023-01-01T00:00:00Z",
      "dateMaturite": "2025-06-14T00:00:00Z",
      "valeurNominale": 1000.00,
      "devise": "USD",
      "frequencePaiementInterets": "SEMESTRIEL"
    },
    "montantInvesti": 20000.00,
    "valeurActuelle": 20900.00,
    "nombreUnites": 20.0,
    "tauxSouscription": 5.5,
    "tmaReel": 5.8,
    "interetsAccumules": 900.00,
    "dateSouscription": "2023-06-15T00:00:00Z",
    "dateMaturite": "2025-06-14T00:00:00Z",
    "joursRestants": 180,
    "progressionPourcentage": 75.5,
    "gainPerte": 900.00,
    "gainPertePourcentage": 4.5,
    "statut": "ACTIVE",
    "paiementsInterets": [
      {
        "paiementId": 5001,
        "datePaiement": "2024-01-01T00:00:00Z",
        "montantInteret": 250.00,
        "statut": "EXECUTE"
      },
      {
        "paiementId": 5002,
        "datePaiement": "2024-07-01T00:00:00Z",
        "montantInteret": 250.00,
        "statut": "PLANIFIE"
      }
    ]
  }
}
```

### 4.3 Instruments Disponibles
**GET** `/investissements/instruments/disponibles`

Liste tous les instruments dans lesquels le client peut investir.

**Query Parameters:**
- `typeInstrument` (optional): `OBL` | `ACTION` | `FONDS` | `DEPOT`
- `deviseCompte` (optional): Filtre les instruments compatibles avec la devise du compte

**Response 200:**
```json
{
  "success": true,
  "data": [
    {
      "instrumentId": 101,
      "code": "OBL-BRH-2025",
      "nom": "Obligation BRH 5.5% 2025",
      "description": "Obligation souveraine émise par la BRH",
      "emetteur": "Banque de la République d'Haïti",
      "typeInstrument": "Obligation",
      "tauxRendementAnnuel": 5.5,
      "dateEmission": "2023-01-01T00:00:00Z",
      "dateMaturite": "2025-06-14T00:00:00Z",
      "valeurNominale": 1000.00,
      "montantMinimum": 5000.00,
      "devise": "USD",
      "frequencePaiementInterets": "SEMESTRIEL",
      "statut": "DISPONIBLE"
    }
  ]
}
```

### 4.4 Créer une Souscription
**POST** `/investissements/souscrire`

**Body:**
```json
{
  "compteId": 1,
  "instrumentId": 101,
  "montantInvesti": 10000.00
}
```

**Response 201:**
```json
{
  "success": true,
  "message": "Souscription créée avec succès",
  "data": {
    "souscriptionId": 2010,
    "transactionId": 5050,
    "statut": "EN_ATTENTE"
  }
}
```

---

## 5. TRANSACTIONS

### 5.1 Historique des Transactions
**GET** `/transactions`

**Query Parameters:**
- `compteId` (optional): Filtre par compte
- `typeTransaction` (optional): `DEPOT` | `RETRAIT` | `SOUSCRIPTION` | `RACHAT` | `PAIEMENT_INTERET` | `REMBOURSEMENT_MATURITE` | `TRANSFERT`
- `statut` (optional): `EN_ATTENTE` | `EXECUTEE` | `ECHOUEE` | `ANNULEE`
- `dateDebut` (optional): Format ISO 8601
- `dateFin` (optional): Format ISO 8601
- `page` (optional, default=1)
- `limit` (optional, default=50)
- `search` (optional): Recherche dans la description

**Response 200:**
```json
{
  "success": true,
  "data": {
    "transactions": [
      {
        "transactionId": 3001,
        "typeTransaction": "DEPOT",
        "description": "Virement entrant salaire",
        "montant": 5000.00,
        "devise": "USD",
        "statut": "EXECUTEE",
        "dateCreation": "2024-07-20T10:30:00Z",
        "dateExecution": "2024-07-20T10:30:00Z",
        "estAutomatique": false,
        "compteSource": null,
        "numeroCompteSource": null,
        "compteDestination": 1,
        "numeroCompteDestination": "INV-2023-230001",
        "souscription": null
      },
      {
        "transactionId": 3002,
        "typeTransaction": "SOUSCRIPTION",
        "description": "Souscription OBL-BRH-2025",
        "montant": -20000.00,
        "devise": "USD",
        "statut": "EXECUTEE",
        "dateCreation": "2023-06-15T14:00:00Z",
        "dateExecution": "2023-06-15T14:00:00Z",
        "estAutomatique": false,
        "compteSource": 1,
        "numeroCompteSource": "INV-2023-230001",
        "compteDestination": null,
        "numeroCompteDestination": null,
        "souscription": {
          "souscriptionId": 2001,
          "codeInstrument": "OBL-BRH-2025",
          "nomInstrument": "Obligation BRH 5.5% 2025"
        }
      },
      {
        "transactionId": 3003,
        "typeTransaction": "RETRAIT",
        "description": "Retrait en ligne",
        "montant": -1000.00,
        "devise": "USD",
        "statut": "EN_ATTENTE",
        "dateCreation": "2024-07-25T09:15:00Z",
        "dateExecution": null,
        "estAutomatique": false,
        "compteSource": 1,
        "numeroCompteSource": "INV-2023-230001",
        "compteDestination": null,
        "numeroCompteDestination": null,
        "souscription": null
      }
    ],
    "pagination": {
      "page": 1,
      "limit": 50,
      "total": 15,
      "totalPages": 1
    }
  }
}
```

### 5.2 Détails d'une Transaction
**GET** `/transactions/:transactionId`

**Response 200:**
```json
{
  "success": true,
  "data": {
    "transactionId": 3001,
    "typeTransaction": "DEPOT",
    "description": "Virement entrant salaire",
    "montant": 5000.00,
    "devise": "USD",
    "statut": "EXECUTEE",
    "dateCreation": "2024-07-20T10:30:00Z",
    "dateExecution": "2024-07-20T10:30:00Z",
    "estAutomatique": false,
    "commentaires": null,
    "compteSource": null,
    "compteDestination": {
      "compteId": 1,
      "numeroCompte": "INV-2023-230001",
      "typeCompte": "INVESTISSEMENT"
    },
    "creePar": {
      "clientId": 1,
      "nom": "Marceus Jethro"
    }
  }
}
```

### 5.3 Créer un Dépôt
**POST** `/transactions/depot`

**Body:**
```json
{
  "compteId": 1,
  "montant": 5000.00,
  "description": "Dépôt mensuel"
}
```

**Response 201:**
```json
{
  "success": true,
  "message": "Dépôt créé avec succès",
  "data": {
    "transactionId": 3010,
    "statut": "EN_ATTENTE"
  }
}
```

### 5.4 Créer un Retrait
**POST** `/transactions/retrait`

**Body:**
```json
{
  "compteId": 1,
  "montant": 1000.00,
  "description": "Retrait en ligne"
}
```

**Response 201:**
```json
{
  "success": true,
  "message": "Retrait créé avec succès",
  "data": {
    "transactionId": 3011,
    "statut": "EN_ATTENTE"
  }
}
```

### 5.5 Exporter Transactions en CSV
**GET** `/transactions/export/csv`

**Query Parameters:** (mêmes que `/transactions`)

**Response 200:**
Content-Type: text/csv
```csv
Date,Description,Compte Source,Compte Destination,Montant,Statut
2024-07-20,Virement entrant salaire,N/A,INV-2023-230001,5000.00 $US,Executée
2024-07-25,Retrait en ligne,INV-2023-230001,N/A,-1000.00 $US,En Attente Validation
```

---

## 6. PROFIL CLIENT (KYC)

### 6.1 Informations Personnelles
**GET** `/profil`

**Response 200:**
```json
{
  "success": true,
  "data": {
    "clientId": 1,
    "clientType": "INDIVIDUEL",
    "nomComplet": "Marceus Jethro",
    "email": "marceus.jethro@email.ht",
    "telephone": "+509 3812 5678",
    "adresse": {
      "ligne1": "45 Rue Grégoire, Pétion-Ville",
      "ligne2": null,
      "ville": "Port-au-Prince",
      "codePostal": "HT6140",
      "pays": "Haïti",
      "complete": "45 Rue Grégoire, Pétion-Ville, HT6140 Port-au-Prince, Haïti"
    },
    "profilInvestisseur": {
      "statut": "Personne physique",
      "niveauRisque": "Modéré",
      "horizonInvestissement": "Moyen terme",
      "revenuAnnuel": "50k-75k USD"
    },
    "informationsIndividuel": {
      "prenom": "Marceus",
      "nom": "Jethro",
      "dateNaissance": "1985-03-15",
      "nationalite": "Haïtienne",
      "typeIdentite": "CIN",
      "numeroIdentite": "CIN-001-2020-12345",
      "profession": "Entrepreneur",
      "sourceRevenus": "Commerce et Investissements",
      "revenuAnnuelEstime": 85000.00
    },
    "statutClient": "ACTIF",
    "dateCreation": "2023-06-01T00:00:00Z",
    "dernierConnexion": "2024-07-25T08:30:00Z"
  }
}
```

### 6.2 Mise à Jour du Profil
**PATCH** `/profil`

**Body:**
```json
{
  "telephone": "+509 3812 9999",
  "adresse": {
    "ligne1": "Nouvelle adresse",
    "ville": "Port-au-Prince",
    "codePostal": "HT6140",
    "pays": "Haïti"
  }
}
```

**Response 200:**
```json
{
  "success": true,
  "message": "Profil mis à jour avec succès"
}
```

---

## 7. GESTION DES ERREURS

Toutes les erreurs suivent le format:

```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "Message d'erreur lisible",
    "details": {}
  }
}
```

### Codes d'Erreur Communs

| Code HTTP | Error Code | Description |
|-----------|------------|-------------|
| 400 | `INVALID_REQUEST` | Requête invalide |
| 401 | `UNAUTHORIZED` | Non authentifié |
| 403 | `FORBIDDEN` | Accès refusé (rôle insuffisant) |
| 404 | `NOT_FOUND` | Ressource introuvable |
| 409 | `CONFLICT` | Conflit (ex: solde insuffisant) |
| 422 | `VALIDATION_ERROR` | Erreur de validation |
| 500 | `INTERNAL_ERROR` | Erreur serveur |

### Exemples d'Erreurs

**401 - Non authentifié:**
```json
{
  "success": false,
  "error": {
    "code": "UNAUTHORIZED",
    "message": "Token invalide ou expiré"
  }
}
```

**403 - Accès refusé:**
```json
{
  "success": false,
  "error": {
    "code": "FORBIDDEN",
    "message": "Vous n'avez pas les permissions nécessaires pour accéder à ce compte",
    "details": {
      "compteId": 5,
      "roleRequis": "TITULAIRE_PRINCIPAL",
      "roleActuel": "OBSERVATEUR"
    }
  }
}
```

**409 - Solde insuffisant:**
```json
{
  "success": false,
  "error": {
    "code": "INSUFFICIENT_BALANCE",
    "message": "Solde disponible insuffisant",
    "details": {
      "soldeDisponible": 2600.00,
      "montantDemande": 5000.00,
      "devise": "USD"
    }
  }
}
```

---

## 8. SYSTÈME DE PERMISSIONS PAR RÔLE

### Matrice de Permissions

| Action | TITULAIRE_PRINCIPAL | TITULAIRE_SECONDAIRE | MANDATAIRE | OBSERVATEUR | ADMINISTRATEUR | BENEFICIAIRE |
|--------|---------------------|----------------------|------------|-------------|----------------|--------------|
| Consulter solde | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ |
| Consulter transactions | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ |
| Consulter investissements | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ |
| Effectuer dépôt | ✅ | ✅ | ✅ | ❌ | ✅ | ❌ |
| Effectuer retrait | ✅ | ✅ | ✅ | ❌ | ✅ | ❌ |
| Souscrire investissement | ✅ | ✅ | ✅ | ❌ | ✅ | ❌ |
| Racheter investissement | ✅ | ✅ | ❌ | ❌ | ✅ | ❌ |
| Gérer rôles | ✅ | ❌ | ❌ | ❌ | ✅ | ❌ |
| Fermer compte | ✅ | ❌ | ❌ | ❌ | ✅ | ❌ |

### Vérification des Permissions dans l'API

Chaque endpoint doit vérifier:
1. Le client est-il authentifié? (JWT valide)
2. Le client a-t-il accès au compte demandé? (existe-t-il dans `ComptesRoles`?)
3. Le rôle du client permet-il l'action demandée?

**Exemple de middleware:**
```javascript
async function checkAccountAccess(req, res, next) {
  const { clientId } = req.user; // Du JWT
  const { compteId } = req.params;
  const requiredPermission = req.route.permission; // Ex: 'canDeposit'

  // Vérifier l'accès au compte
  const role = await ComptesRoles.findOne({
    where: { clientId, compteId, estActif: true }
  });

  if (!role) {
    return res.status(403).json({
      success: false,
      error: {
        code: 'FORBIDDEN',
        message: 'Accès au compte refusé'
      }
    });
  }

  // Vérifier la permission selon le rôle
  const hasPermission = checkPermission(role.Role, requiredPermission);

  if (!hasPermission) {
    return res.status(403).json({
      success: false,
      error: {
        code: 'INSUFFICIENT_PERMISSIONS',
        message: `Le rôle ${role.Role} ne permet pas cette action`
      }
    });
  }

  req.accountRole = role.Role;
  next();
}
```

---

## 9. FILTRAGE DES DONNÉES PAR CONTEXTE CLIENT

### Principe Important

**TOUTES les requêtes SQL doivent filtrer via la table `ComptesRoles`** pour s'assurer que le client ne voit que les données auxquelles il a accès.

**Exemple - Dashboard Overview:**
```sql
SELECT
    cr.ClientID,
    cr.CompteID,
    SUM(s.ValeurActuelle) AS ValeurTotale
FROM ComptesRoles cr
INNER JOIN Comptes cpt ON cr.CompteID = cpt.CompteID
LEFT JOIN Souscriptions s ON cpt.CompteID = s.CompteID
WHERE cr.ClientID = @ClientID  -- ← FILTRAGE CRITIQUE
  AND cr.EstActif = 1
  AND cr.Role IN ('TITULAIRE_PRINCIPAL', 'MANDATAIRE', 'OBSERVATEUR')
GROUP BY cr.ClientID, cr.CompteID
```

**Exemple - Transactions:**
```sql
SELECT *
FROM Transactions t
WHERE (
    t.CompteSource IN (
        SELECT CompteID FROM ComptesRoles
        WHERE ClientID = @ClientID AND EstActif = 1
    )
    OR t.CompteDestination IN (
        SELECT CompteID FROM ComptesRoles
        WHERE ClientID = @ClientID AND EstActif = 1
    )
)
```

---

## 10. CONSIDÉRATIONS TECHNIQUES

### 10.1 Pagination
Utiliser la pagination pour toutes les listes:
```
?page=1&limit=20
```

### 10.2 Tri
```
?sort=dateMaturite&order=asc
```

### 10.3 Recherche
```
?search=salaire
```

### 10.4 Filtres Multiples
```
?compteId=1&statut=EXECUTEE&dateDebut=2024-01-01&dateFin=2024-12-31
```

### 10.5 Validation des Données
- Valider tous les montants > 0
- Valider les devises (USD, HTG uniquement)
- Valider les dates (format ISO 8601)
- Valider les IDs (nombres positifs)

### 10.6 Rate Limiting
Implémenter un rate limiting pour éviter les abus:
- 100 requêtes/minute par IP
- 1000 requêtes/heure par utilisateur authentifié

### 10.7 Logging et Audit
Toutes les actions importantes doivent être auditées dans `JournalAudit`:
- Connexions/déconnexions
- Transactions créées
- Modifications de profil
- Accès aux comptes

---

## 11. ENDPOINTS ADDITIONNELS (Optionnels mais Recommandés)

### 11.1 Notifications
**GET** `/notifications`

Liste des notifications pour le client (paiements d'intérêts à venir, etc.)

### 11.2 Documents
**GET** `/documents`

Liste des documents KYC, relevés, attestations

### 11.3 Support
**POST** `/support/ticket`

Créer un ticket de support

### 11.4 Nouveau Compte
**POST** `/comptes/nouveau`

Ouvrir un nouveau compte

### 11.5 Rapports
**GET** `/rapports/performance`

Rapport de performance du portefeuille

---

## RÉSUMÉ DES ENDPOINTS

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| **AUTH** |
| POST | `/auth/login` | Connexion |
| POST | `/auth/refresh` | Rafraîchir le token |
| POST | `/auth/logout` | Déconnexion |
| **COMPTES** |
| GET | `/comptes` | Liste des comptes accessibles |
| GET | `/comptes/:id` | Détails d'un compte |
| **DASHBOARD** |
| GET | `/dashboard/overview` | Vue d'ensemble |
| GET | `/dashboard/transactions/recentes` | Dernières transactions |
| GET | `/dashboard/investissements` | Investissements actifs |
| GET | `/dashboard/statistiques/mensuelles` | Stats mensuelles |
| **INVESTISSEMENTS** |
| GET | `/investissements` | Liste des investissements |
| GET | `/investissements/:id` | Détails investissement |
| GET | `/investissements/instruments/disponibles` | Instruments disponibles |
| POST | `/investissements/souscrire` | Nouvelle souscription |
| **TRANSACTIONS** |
| GET | `/transactions` | Historique |
| GET | `/transactions/:id` | Détails transaction |
| POST | `/transactions/depot` | Créer dépôt |
| POST | `/transactions/retrait` | Créer retrait |
| GET | `/transactions/export/csv` | Export CSV |
| **PROFIL** |
| GET | `/profil` | Informations personnelles |
| PATCH | `/profil` | Mise à jour profil |

---

**Total: 22 endpoints principaux**
