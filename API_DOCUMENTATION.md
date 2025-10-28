# 📘 Documentation API - Banque d'Investissement

## 🚀 Vue d'ensemble

Cette API RESTful permet la gestion complète d'une banque d'investissement avec :
- Gestion des clients (individuels et institutionnels)
- Comptes d'investissement
- Instruments financiers (obligations, actions, dépôts)
- Souscriptions (investissements)
- Transactions financières
- Authentification JWT

**Base URL:** `http://localhost:8000/api/v1`

**Documentation interactive:** `http://localhost:8000/api/v1/docs`

---

## 🔐 Authentification

Toutes les routes (sauf `/auth/*`) nécessitent un token JWT dans le header :
```
Authorization: Bearer <access_token>
```

### Endpoints d'authentification

#### 1. Inscription
```http
POST /api/v1/auth/register
```

**Body:**
```json
{
  "client_type": "INDIVIDUEL",  // ou "INSTITUTIONNEL"
  "email": "jean@email.ht",
  "password": "motdepasse123",

  // Pour INDIVIDUEL:
  "prenom": "Jean",
  "nom": "Dupont",
  "date_naissance": "1985-03-15",
  "numero_piece_identite": "CIN-001-2024",

  // Pour INSTITUTIONNEL:
  "nom_entreprise": "TechHaiti S.A.",
  "numero_registre_commerce": "RC-2020-001234",
  "nom_representant_legal": "Jacques Bernard"
}
```

**Réponse:**
```json
{
  "success": true,
  "message": "Inscription réussie",
  "client_id": 1,
  "email": "jean@email.ht"
}
```

#### 2. Connexion
```http
POST /api/v1/auth/login
```

**Body:**
```json
{
  "email": "jean@email.ht",
  "password": "motdepasse123"
}
```

**Réponse:**
```json
{
  "success": true,
  "message": "Connexion réussie",
  "tokens": {
    "access_token": "eyJhbGc...",
    "refresh_token": "eyJhbGc...",
    "token_type": "bearer",
    "expires_in": 1800
  },
  "client": {
    "client_id": 1,
    "email": "jean@email.ht",
    "client_type": "INDIVIDUEL",
    "prenom": "Jean",
    "nom": "Dupont"
  }
}
```

#### 3. Rafraîchir le token
```http
POST /api/v1/auth/refresh
```

**Body:**
```json
{
  "refresh_token": "eyJhbGc..."
}
```

#### 4. Déconnexion
```http
POST /api/v1/auth/logout
```

**Body:**
```json
{
  "refresh_token": "eyJhbGc..."
}
```

---

## 👤 Utilisateurs

### Profil du client connecté

```http
GET /api/v1/users/me
Authorization: Bearer <token>
```

**Réponse:**
```json
{
  "client_id": 1,
  "client_type": "INDIVIDUEL",
  "email": "jean@email.ht",
  "statut_client": "ACTIF",
  "profil_risque": "CONSERVATEUR",
  "date_creation": "2025-01-15T10:30:00",
  "prenom": "Jean",
  "nom": "Dupont",
  "date_naissance": "1985-03-15",
  "profession": "Ingénieur"
}
```

---

## 💰 Comptes

### 1. Créer un compte
```http
POST /api/v1/comptes/
Authorization: Bearer <token>
```

**Body:**
```json
{
  "ClientID": 1,
  "NumeroCompte": "INV-20250115-12345",
  "TypeCompte": "INVESTISSEMENT",  // "INVESTISSEMENT", "CASH", "EPARGNE"
  "Devise": "HTG",
  "Role": "TITULAIRE_PRINCIPAL"
}
```

**Réponse:**
```json
{
  "success": true,
  "message": "Compte créé avec succès",
  "compte": {
    "CompteID": 1,
    "NumeroCompte": "INV-20250115-12345",
    "TypeCompte": "INVESTISSEMENT",
    "Devise": "HTG",
    "Solde": 0,
    "SoldeDisponible": 0,
    "StatutCompte": "ACTIF",
    "DateOuverture": "2025-01-15T10:30:00"
  }
}
```

### 2. Liste de mes comptes
```http
GET /api/v1/comptes/mes-comptes?statut=ACTIF
Authorization: Bearer <token>
```

**Réponse:**
```json
{
  "total": 2,
  "comptes": [
    {
      "CompteID": 1,
      "NumeroCompte": "INV-20250115-12345",
      "TypeCompte": "INVESTISSEMENT",
      "Solde": 500000.00,
      "SoldeDisponible": 450000.00,
      "StatutCompte": "ACTIF"
    }
  ]
}
```

### 3. Détails d'un compte
```http
GET /api/v1/comptes/{compte_id}
Authorization: Bearer <token>
```

### 4. Suspendre un compte
```http
PUT /api/v1/comptes/{compte_id}/suspendre
Authorization: Bearer <token>
```

### 5. Fermer un compte
```http
DELETE /api/v1/comptes/{compte_id}
Authorization: Bearer <token>
```

---

## 📊 Instruments Financiers

### 1. Instruments disponibles
```http
GET /api/v1/instruments/disponibles
Authorization: Bearer <token>
```

**Réponse:**
```json
{
  "total": 5,
  "instruments": [
    {
      "InstrumentID": 1,
      "TypeInstrumentID": 1,
      "Code": "OBL-BRH-2025",
      "Nom": "Obligation BRH 5% 2025-2030",
      "Emetteur": "Banque de la République d'Haïti",
      "TauxRendementAnnuel": 5.00,
      "DateEmission": "2025-01-01",
      "DateMaturite": "2030-01-01",
      "ValeurNominale": 1000.00,
      "MontantMinimum": 5000.00,
      "Devise": "HTG",
      "FrequencePaiementInterets": "TRIMESTRIEL",
      "StatutInstrument": "DISPONIBLE",
      "type_instrument": {
        "TypeInstrumentID": 1,
        "Code": "OBL",
        "Nom": "Obligation"
      }
    }
  ]
}
```

### 2. Tous les instruments
```http
GET /api/v1/instruments/?statut=DISPONIBLE
Authorization: Bearer <token>
```

### 3. Détails d'un instrument
```http
GET /api/v1/instruments/{instrument_id}
Authorization: Bearer <token>
```

### 4. Types d'instruments
```http
GET /api/v1/instruments/types/
Authorization: Bearer <token>
```

**Réponse:**
```json
[
  {
    "TypeInstrumentID": 1,
    "Code": "OBL",
    "Nom": "Obligation",
    "Description": "Titre de créance à taux fixe"
  },
  {
    "TypeInstrumentID": 2,
    "Code": "ACTION",
    "Nom": "Action",
    "Description": "Part de propriété dans une entreprise"
  }
]
```

---

## 💼 Souscriptions (Investissements)

### 1. Créer une souscription
```http
POST /api/v1/souscriptions/
Authorization: Bearer <token>
```

**Body:**
```json
{
  "CompteID": 1,
  "InstrumentID": 1,
  "MontantInvesti": 100000.00,
  "NombreUnites": 100,
  "TauxSouscription": 5.00
}
```

**Réponse:**
```json
{
  "success": true,
  "message": "Souscription créée avec succès",
  "souscription": {
    "SouscriptionID": 1,
    "CompteID": 1,
    "InstrumentID": 1,
    "MontantInvesti": 100000.00,
    "NombreUnites": 100,
    "DateSouscription": "2025-01-15T10:30:00",
    "DateMaturiteEffective": "2030-01-01",
    "TauxSouscription": 5.00,
    "ValeurActuelle": 100000.00,
    "InteretsAccumules": 0,
    "StatutSouscription": "ACTIVE"
  },
  "transaction_id": 5
}
```

### 2. Mes souscriptions
```http
GET /api/v1/souscriptions/mes-souscriptions
Authorization: Bearer <token>
```

**Réponse:**
```json
{
  "total": 3,
  "souscriptions": [
    {
      "SouscriptionID": 1,
      "CompteID": 1,
      "InstrumentID": 1,
      "MontantInvesti": 100000.00,
      "ValeurActuelle": 105000.00,
      "InteretsAccumules": 5000.00,
      "StatutSouscription": "ACTIVE",
      "instrument_nom": "Obligation BRH 5%",
      "instrument_code": "OBL-BRH-2025",
      "emetteur": "Banque de la République d'Haïti",
      "taux_rendement": 5.00
    }
  ]
}
```

### 3. Mon portefeuille
```http
GET /api/v1/souscriptions/portefeuille
Authorization: Bearer <token>
```

**Réponse:**
```json
{
  "total_investi": 500000.00,
  "valeur_actuelle_totale": 525000.00,
  "interets_accumules_total": 25000.00,
  "nombre_souscriptions": 3,
  "souscriptions": [...]
}
```

### 4. Détails d'une souscription
```http
GET /api/v1/souscriptions/{souscription_id}
Authorization: Bearer <token>
```

### 5. Racheter une souscription
```http
POST /api/v1/souscriptions/{souscription_id}/racheter
Authorization: Bearer <token>
```

---

## 💸 Transactions

### 1. Créer un dépôt
```http
POST /api/v1/transactions/depot
Authorization: Bearer <token>
```

**Body:**
```json
{
  "CompteDestination": 1,
  "Montant": 100000.00,
  "Devise": "HTG",
  "Description": "Dépôt mensuel"
}
```

**Réponse:**
```json
{
  "success": true,
  "message": "Dépôt créé avec succès",
  "transaction": {
    "TransactionID": 1,
    "TypeTransaction": "DEPOT",
    "CompteDestination": 1,
    "Montant": 100000.00,
    "Devise": "HTG",
    "Description": "Dépôt mensuel",
    "StatutTransaction": "EXECUTEE",
    "DateCreation": "2025-01-15T10:30:00",
    "DateExecution": "2025-01-15T10:30:00"
  }
}
```

### 2. Créer un retrait
```http
POST /api/v1/transactions/retrait
Authorization: Bearer <token>
```

**Body:**
```json
{
  "CompteSource": 1,
  "Montant": 50000.00,
  "Devise": "HTG",
  "Description": "Retrait ATM"
}
```

### 3. Créer un transfert
```http
POST /api/v1/transactions/transfert
Authorization: Bearer <token>
```

**Body:**
```json
{
  "CompteSource": 1,
  "CompteDestination": 2,
  "Montant": 75000.00,
  "Devise": "HTG",
  "Description": "Transfert entre comptes"
}
```

### 4. Mes transactions
```http
GET /api/v1/transactions/mes-transactions?limit=100
Authorization: Bearer <token>
```

**Réponse:**
```json
{
  "total": 15,
  "transactions": [
    {
      "TransactionID": 1,
      "TypeTransaction": "DEPOT",
      "CompteDestination": 1,
      "Montant": 100000.00,
      "Devise": "HTG",
      "StatutTransaction": "EXECUTEE",
      "DateCreation": "2025-01-15T10:30:00",
      "compte_destination_numero": "INV-20250115-12345"
    }
  ]
}
```

### 5. Historique d'un compte
```http
GET /api/v1/transactions/compte/{compte_id}?limit=50
Authorization: Bearer <token>
```

**Réponse:**
```json
{
  "compte_id": 1,
  "compte_numero": "INV-20250115-12345",
  "total": 10,
  "transactions": [...]
}
```

### 6. Détails d'une transaction
```http
GET /api/v1/transactions/{transaction_id}
Authorization: Bearer <token>
```

---

## 📋 Codes de statut HTTP

| Code | Signification |
|------|---------------|
| 200  | Succès |
| 201  | Créé avec succès |
| 400  | Requête invalide |
| 401  | Non authentifié |
| 403  | Accès refusé |
| 404  | Ressource introuvable |
| 500  | Erreur serveur |

---

## 🧪 Données de test

Utilisez le script SQL `sql_scripts/test_data.sql` pour insérer des données de test.

**Comptes de test :**
- **jean.dupont@email.ht** - Client individuel (Profil Conservateur)
- **marie.pierre@email.ht** - Client individuel (Profil Modéré)
- **pierre.lafontaine@email.ht** - Client individuel (Profil Agressif)
- **finance@techhaiti.ht** - Client institutionnel (Tech)
- **contact@agriprogres.ht** - Client institutionnel (Agriculture)

Tous les mots de passe doivent être créés avec le hash bcrypt approprié.

---

## 🔧 Exemples d'utilisation avec cURL

### 1. Inscription
```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "client_type": "INDIVIDUEL",
    "email": "test@email.ht",
    "password": "password123",
    "prenom": "Test",
    "nom": "User",
    "date_naissance": "1990-01-01",
    "numero_piece_identite": "TEST-001"
  }'
```

### 2. Connexion
```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@email.ht",
    "password": "password123"
  }'
```

### 3. Créer un compte (avec token)
```bash
curl -X POST http://localhost:8000/api/v1/comptes/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "ClientID": 1,
    "NumeroCompte": "INV-20250115-99999",
    "TypeCompte": "INVESTISSEMENT",
    "Devise": "HTG",
    "Role": "TITULAIRE_PRINCIPAL"
  }'
```

### 4. Investir dans un instrument
```bash
curl -X POST http://localhost:8000/api/v1/souscriptions/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "CompteID": 1,
    "InstrumentID": 1,
    "MontantInvesti": 50000.00
  }'
```

---

## 📚 Structure des données

### Types de comptes
- `INVESTISSEMENT` - Compte pour investissements
- `CASH` - Compte de liquidités
- `EPARGNE` - Compte d'épargne

### Types de transactions
- `DEPOT` - Dépôt d'argent
- `RETRAIT` - Retrait d'argent
- `SOUSCRIPTION` - Investissement dans un instrument
- `RACHAT` - Rachat d'une souscription
- `PAIEMENT_INTERET` - Paiement d'intérêt
- `REMBOURSEMENT_MATURITE` - Remboursement à maturité
- `TRANSFERT` - Transfert entre comptes

### Statuts
- **Comptes:** `ACTIF`, `SUSPENDU`, `FERME`
- **Instruments:** `DISPONIBLE`, `EPUISE`, `EXPIRE`
- **Souscriptions:** `ACTIVE`, `MATURE`, `RACHETEE`
- **Transactions:** `EN_ATTENTE`, `EXECUTEE`, `ECHOUEE`, `ANNULEE`

---

## 🎯 Scénarios d'utilisation

### Scénario 1: Nouveau client investit
1. S'inscrire (`POST /auth/register`)
2. Se connecter (`POST /auth/login`)
3. Créer un compte (`POST /comptes/`)
4. Faire un dépôt (`POST /transactions/depot`)
5. Voir les instruments disponibles (`GET /instruments/disponibles`)
6. Investir dans un instrument (`POST /souscriptions/`)
7. Consulter son portefeuille (`GET /souscriptions/portefeuille`)

### Scénario 2: Client gère ses investissements
1. Se connecter
2. Voir ses comptes (`GET /comptes/mes-comptes`)
3. Voir ses souscriptions (`GET /souscriptions/mes-souscriptions`)
4. Voir l'historique des transactions (`GET /transactions/mes-transactions`)
5. Racheter une souscription (`POST /souscriptions/{id}/racheter`)

---

## 💡 Notes importantes

- Tous les montants sont en **HTG** (Gourde Haïtienne)
- Les tokens JWT expirent après **30 minutes**
- Les refresh tokens sont valides **7 jours**
- Les mots de passe doivent faire minimum **6 caractères**
- Le solde d'un compte ne peut jamais être négatif
- Un compte ne peut être fermé que si son solde est à 0

---

## 📞 Support

Pour toute question ou problème, consultez la documentation Swagger interactive à `/api/v1/docs` ou contactez l'équipe de développement.
