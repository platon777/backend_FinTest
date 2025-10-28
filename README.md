# Système de Gestion de Portefeuille - Version Finale

## 🎯 Vue d'ensemble

Un système où les **CLIENTS** peuvent:
- S'inscrire et créer leur compte
- Se connecter au portail web
- Voir leurs comptes d'investissement
- Consulter leurs obligations/actions achetées
- Suivre leurs transactions

**Il n'y a QUE des clients. Pas d'employés/back-office.**

## 🏗️ Architecture Simple

```
┌──────────────────────────────────┐
│     PORTAIL WEB (React)          │
│     Interface Client             │
│                                  │
│  - Inscription                   │
│  - Connexion                     │
│  - Mes comptes                   │
│  - Mes investissements           │
│  - Mes transactions              │
└─────────────┬────────────────────┘
              │
              │ REST API
              ↓
┌─────────────┴────────────────────┐
│     BACKEND (FastAPI)            │
│                                  │
│  Endpoints:                      │
│  /auth/register                  │
│  /auth/login                     │
│  /users/me                       │
│  /comptes                        │
│  /souscriptions                  │
└─────────────┬────────────────────┘
              │
              │ SQL
              ↓
┌─────────────┴────────────────────┐
│  SQL Server Azure (Db_test)      │
│                                  │
│  Tables:                         │
│  - Clients                       │
│  - ClientsAuthentification       │
│  - Comptes                       │
│  - Instruments                   │
│  - Souscriptions                 │
│  - Transactions                  │
└──────────────────────────────────┘
```

## 📊 Structure de la base de données

### Les clients sont les utilisateurs du système

```
Client (Utilisateur)
    ↓
ClientsAuthentification (Login)
    ↓
Comptes (Comptes d'investissement)
    ↓
Souscriptions (Achats d'obligations/actions)
    ↓
Transactions (Historique)
```

### Tables principales

**1. Clients**
- Un client peut être INDIVIDUEL ou INSTITUTIONNEL
- Chaque client a un profil de risque
- Statut: ACTIF, SUSPENDU, FERME

**2. ClientsAuthentification**
- Email + Password pour login
- Un client = un compte de connexion
- Sessions gérées avec JWT tokens

**3. Comptes**
- Chaque client peut avoir plusieurs comptes
- Types: INVESTISSEMENT, CASH, EPARGNE
- Devise: HTG, USD, EUR

**4. Instruments**
- Obligations (OBL)
- Actions (ACTION)
- Fonds communs (FONDS)
- Dépôts à terme (DEPOT)

**5. Souscriptions**
- Quand un client achète un instrument
- Suivi du montant investi, intérêts accumulés
- Valeur actuelle

**6. Transactions**
- DEPOT, RETRAIT, SOUSCRIPTION, RACHAT
- Historique de toutes les opérations

## 🚀 Installation

### 1. Créer la base de données

Exécutez le script SQL:
```sql
-- Fichier: sql_scripts/DATABASE_CLIENTS_ONLY.sql
```

Ce script crée:
- ✅ Toutes les tables nécessaires
- ✅ Quelques instruments de test (obligations BRH, EDH)
- ✅ Indexes pour la performance

### 2. Lancer l'API

```bash
# Activer l'environnement virtuel
venv\Scripts\activate

# Lancer FastAPI
python main.py
```

API: http://localhost:8000
Docs: http://localhost:8000/api/v1/docs

## 📝 Exemples d'utilisation

### 1. Inscription d'un client individuel

```http
POST /api/v1/auth/register
Content-Type: application/json

{
  "client_type": "INDIVIDUEL",
  "email": "marie.jean@example.com",
  "password": "MotDePasse123",
  "prenom": "Marie",
  "nom": "Jean",
  "date_naissance": "1990-03-20",
  "numero_piece_identite": "CIN12345"
}
```

**Réponse:**
```json
{
  "success": true,
  "message": "Inscription réussie",
  "client_id": 1,
  "email": "marie.jean@example.com"
}
```

### 2. Connexion

```http
POST /api/v1/auth/login
Content-Type: application/json

{
  "email": "marie.jean@example.com",
  "password": "MotDePasse123"
}
```

**Réponse:**
```json
{
  "success": true,
  "tokens": {
    "access_token": "eyJhbGci...",
    "refresh_token": "eyJhbGci...",
    "expires_in": 1800
  },
  "client": {
    "client_id": 1,
    "email": "marie.jean@example.com",
    "client_type": "INDIVIDUEL",
    "prenom": "Marie",
    "nom": "Jean"
  }
}
```

### 3. Voir mon profil (route protégée)

```http
GET /api/v1/users/me
Authorization: Bearer eyJhbGci...
```

**Réponse:**
```json
{
  "client_id": 1,
  "email": "marie.jean@example.com",
  "client_type": "INDIVIDUEL",
  "prenom": "Marie",
  "nom": "Jean",
  "statut_client": "ACTIF",
  "date_naissance": "1990-03-20"
}
```

## 🔐 Sécurité

- **Passwords**: Hashés avec bcrypt
- **JWT Tokens**:
  - Access token: 30 minutes
  - Refresh token: 7 jours
- **Sessions**: Stockées dans RefreshTokens (révocables)
- **HTTPS**: Obligatoire en production

## 📱 Intégration React

### Service d'authentification

```javascript
// src/services/authService.js
import axios from 'axios';

const API_URL = 'http://localhost:8000/api/v1';

export const authService = {
  async register(data) {
    const response = await axios.post(`${API_URL}/auth/register`, data);
    return response.data;
  },

  async login(email, password) {
    const response = await axios.post(`${API_URL}/auth/login`, {
      email,
      password
    });

    if (response.data.success) {
      localStorage.setItem('access_token', response.data.tokens.access_token);
      localStorage.setItem('refresh_token', response.data.tokens.refresh_token);
      localStorage.setItem('user', JSON.stringify(response.data.client));
    }

    return response.data;
  },

  async getProfile() {
    const token = localStorage.getItem('access_token');
    const response = await axios.get(`${API_URL}/users/me`, {
      headers: { Authorization: `Bearer ${token}` }
    });
    return response.data;
  },

  logout() {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('user');
  },

  isLoggedIn() {
    return !!localStorage.getItem('access_token');
  }
};
```

### Composant Login

```javascript
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { authService } from '../services/authService';

function Login() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const navigate = useNavigate();

  const handleLogin = async (e) => {
    e.preventDefault();
    try {
      await authService.login(email, password);
      navigate('/dashboard');
    } catch (error) {
      alert('Erreur de connexion');
    }
  };

  return (
    <form onSubmit={handleLogin}>
      <input
        type="email"
        value={email}
        onChange={(e) => setEmail(e.target.value)}
        placeholder="Email"
      />
      <input
        type="password"
        value={password}
        onChange={(e) => setPassword(e.target.value)}
        placeholder="Mot de passe"
      />
      <button type="submit">Se connecter</button>
    </form>
  );
}
```

## 🗂️ Structure des fichiers

```
backend_FinTest/
├── app/
│   ├── api/v1/endpoints/
│   │   ├── auth.py          # Inscription, login
│   │   ├── users.py         # Profil client
│   │   └── health.py        # Health check
│   ├── core/
│   │   ├── config.py        # Configuration
│   │   ├── security.py      # JWT, bcrypt
│   │   └── dependencies.py  # get_current_client
│   ├── db/
│   │   └── database.py      # Connexion SQL Server
│   ├── models/
│   │   └── all_models.py    # Modèles SQLAlchemy
│   ├── schemas/
│   │   └── auth_schemas.py  # Schémas Pydantic
│   └── services/
│       └── auth_service.py  # Logique métier
├── sql_scripts/
│   └── DATABASE_CLIENTS_ONLY.sql  # Script SQL
├── main.py                  # Point d'entrée
├── requirements.txt
└── README_FINAL.md         # Ce fichier
```

## ✅ Ce qui fonctionne

- [x] Inscription clients (INDIVIDUEL et INSTITUTIONNEL)
- [x] Connexion avec JWT
- [x] Profil client
- [x] Sessions avec refresh tokens
- [x] Routes protégées
- [x] Connexion SQL Server Azure

## 🔜 À implémenter ensuite

- [ ] Endpoint pour lister les comptes d'un client
- [ ] Endpoint pour lister les souscriptions
- [ ] Endpoint pour lister les instruments disponibles
- [ ] Endpoint pour souscrire à un instrument
- [ ] Endpoint pour l'historique des transactions
- [ ] Dashboard avec statistiques

## 💡 Notes importantes

**Les clients sont les utilisateurs:**
- Il n'y a pas de table "Utilisateurs" séparée
- Les clients se connectent directement
- Chaque client a ses propres comptes et investissements

**La table Clients remplace Utilisateurs:**
- `Clients` = Les personnes qui utilisent le système
- `ClientsAuthentification` = Comment ils se connectent
- `Comptes` = Leurs comptes d'investissement

C'est simple et direct! 🚀
