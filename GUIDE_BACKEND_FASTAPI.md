# GUIDE BACKEND FASTAPI - PROFIN BANK
## API Conforme à la Base de Données et aux Vues SQL

---

## ✅ RÉSUMÉ DES MODIFICATIONS

J'ai analysé votre backend FastAPI existant et ajouté les endpoints manquants pour alimenter votre portail client React avec les visuels que vous m'avez montrés.

### Nouveaux Fichiers Créés

1. **`app/schemas/dashboard.py`** - Schemas Pydantic pour le Dashboard
2. **`app/services/dashboard_service.py`** - Service Dashboard utilisant les vues SQL
3. **`app/api/v1/endpoints/dashboard.py`** - Endpoints Dashboard
4. **`app/schemas/profil.py`** - Schemas Pydantic pour le Profil
5. **`app/services/profil_service.py`** - Service Profil (KYC)
6. **`app/api/v1/endpoints/profil.py`** - Endpoints Profil

### Fichiers Modifiés

1. **`app/api/v1/api.py`** - Ajout des routes dashboard et profil

---

## 📊 ENDPOINTS DISPONIBLES

### 1. AUTHENTIFICATION (Existant ✅)
```
POST   /api/v1/auth/register      - Inscription client
POST   /api/v1/auth/login         - Connexion
POST   /api/v1/auth/refresh       - Rafraîchir token
POST   /api/v1/auth/logout        - Déconnexion
```

### 2. DASHBOARD (Nouveau 🆕)
```
GET    /api/v1/dashboard/overview                    - Vue d'ensemble portefeuille
GET    /api/v1/dashboard/transactions/recentes       - 3 dernières transactions
GET    /api/v1/dashboard/investissements             - Investissements actifs
GET    /api/v1/dashboard/statistiques/mensuelles     - Stats mensuelles (graphique)
GET    /api/v1/dashboard/complet                     - Tout le dashboard en 1 appel
```

### 3. PROFIL (Nouveau 🆕)
```
GET    /api/v1/profil             - Profil complet client (KYC)
PATCH  /api/v1/profil             - Mise à jour profil
```

### 4. COMPTES (Existant ✅)
```
POST   /api/v1/comptes/           - Créer compte
GET    /api/v1/comptes/mes-comptes - Liste des comptes du client
GET    /api/v1/comptes/{id}       - Détails d'un compte
PUT    /api/v1/comptes/{id}/suspendre - Suspendre compte
DELETE /api/v1/comptes/{id}       - Fermer compte
```

### 5. INSTRUMENTS (Existant ✅)
```
GET    /api/v1/instruments/       - Liste instruments disponibles
GET    /api/v1/instruments/{id}   - Détails instrument
```

### 6. SOUSCRIPTIONS (Existant ✅)
```
POST   /api/v1/souscriptions/     - Créer souscription
GET    /api/v1/souscriptions/mes-souscriptions - Souscriptions du client
GET    /api/v1/souscriptions/{id} - Détails souscription
```

### 7. TRANSACTIONS (Existant ✅)
```
POST   /api/v1/transactions/      - Créer transaction
GET    /api/v1/transactions/mes-transactions - Transactions du client
GET    /api/v1/transactions/{id}  - Détails transaction
```

---

## 🎯 MAPPING AVEC VOS VISUELS

### Visual 1: Dashboard Principal
**Endpoint:** `GET /api/v1/dashboard/overview`

**Retourne:**
```json
{
  "valeur_totale": 50000.00,
  "rendement_total": 2600.00,
  "pourcentage_rendement": 5.2,
  "nombre_souscriptions_actives": 2,
  "total_investi": 50000.00,
  "devise": "USD",
  "comptes": [...]
}
```

**Alimente:**
- Section "Valeur totale: 50 000,00 $US"
- Section "Rendement total: +2 600,00 $US (5.2%)"
- Section "Souscriptions actives: 2"

---

### Visual 1: Graphique Mensuel
**Endpoint:** `GET /api/v1/dashboard/statistiques/mensuelles?mois=6`

**Retourne:**
```json
{
  "periodes": [
    {"mois": "Janvier", "date_mois": "2024-01-01", "valeur_portefeuille": 45000.00, "nombre_souscriptions": 1},
    {"mois": "Février", "date_mois": "2024-02-01", "valeur_portefeuille": 45300.00, "nombre_souscriptions": 2},
    ...
  ]
}
```

**Alimente:**
- Graphique à barres avec valeur du portefeuille par mois

---

### Visual 1: Dernières Transactions
**Endpoint:** `GET /api/v1/dashboard/transactions/recentes?limit=3`

**Retourne:**
```json
{
  "total": 3,
  "transactions": [
    {
      "transaction_id": 1,
      "type_transaction": "DEPOT",
      "description": "Virement entrant salaire",
      "montant": 5000.00,
      "devise": "USD",
      "date_creation": "2024-07-20T00:00:00",
      "statut": "EXECUTEE",
      ...
    }
  ]
}
```

**Alimente:**
- Section "Dernières transactions" avec liste des 3 dernières

---

### Visual 1: Investissements Actifs
**Endpoint:** `GET /api/v1/dashboard/investissements`

**Retourne:**
```json
{
  "total": 1,
  "investissements": [
    {
      "souscription_id": 2001,
      "nom_instrument": "Obligation BRH 5.5% 2025",
      "code_instrument": "OBL-BRH-2025",
      "montant_investi": 20000.00,
      "valeur_actuelle": 20900.00,
      "date_maturite": "2025-06-14",
      "progression_maturite": 75.5,
      "statut": "ACTIVE"
    }
  ]
}
```

**Alimente:**
- Section "Investissements Actifs" avec barre de progression

---

### Visual 2: Mes Comptes
**Endpoint:** `GET /api/v1/comptes/mes-comptes`

**Retourne:**
```json
{
  "total": 2,
  "comptes": [
    {
      "CompteID": 1,
      "NumeroCompte": "INV-2023-00001",
      "TypeCompte": "INVESTISSEMENT",
      "Devise": "USD",
      "Solde": 52600.00,
      "SoldeDisponible": 2600.00,
      "StatutCompte": "ACTIF"
    },
    {
      "CompteID": 2,
      "NumeroCompte": "SVG-2023-00002",
      "TypeCompte": "EPARGNE",
      "Devise": "HTG",
      "Solde": 250000.00,
      "SoldeDisponible": 250000.00,
      "StatutCompte": "ACTIF"
    }
  ]
}
```

**Alimente:**
- Carte "Investissement INV-2023-00001"
  - Solde Total: 52 600,00 $US
  - Solde Disponible: 2 600,00 $US
- Carte "Epargne SVG-2023-00002"
  - Solde Total: 250 000,00 HTG
  - Solde Disponible: 250 000,00 HTG

---

### Visual 3: Mes Investissements
**Endpoint:** `GET /api/v1/souscriptions/mes-souscriptions`

**Retourne:**
```json
{
  "total": 3,
  "souscriptions": [
    {
      "SouscriptionID": 2001,
      "instrument": {
        "Nom": "Obligation Verte Énergie 2024",
        "Code": "OBL-VERT-2024"
      },
      "MontantInvesti": 10000.00,
      "TauxSouscription": 4.0,
      "ValeurActuelle": 10800.00,
      "DateSouscription": "2021-01-09",
      "DateMaturite": "2024-01-09",
      "StatutSouscription": "MATURE"
    },
    ...
  ]
}
```

**Alimente:**
- Cartes "Obligation Verte Énergie 2024"
  - Montant Investi: 10 000,00 $US
  - Taux à la souscription: 4%
  - Valeur Actuelle: 10 800,00 $US
  - Souscription: 09/01/2021
  - Maturité: 09/01/2024
  - Statut: MATURE (badge vert)

---

### Visual 4: Transactions
**Endpoint:** `GET /api/v1/transactions/mes-transactions`

**Retourne:**
```json
{
  "total": 3,
  "transactions": [
    {
      "TransactionID": 1,
      "TypeTransaction": "RETRAIT",
      "Description": "Retrait en ligne",
      "Montant": -1000.00,
      "Devise": "USD",
      "DateCreation": "2024-07-25T00:00:00",
      "StatutTransaction": "EN_ATTENTE",
      "CompteSource": "INV-2023-00001",
      "CompteDestination": null
    },
    ...
  ]
}
```

**Alimente:**
- Tableau avec colonnes:
  - DATE: 25/07/2024
  - DESCRIPTION: Retrait en ligne
  - COMPTE SOURCE: INV-2023-00001
  - COMPTE DEST.: N/A
  - MONTANT: -1000,00 $US
  - STATUT: En Attente Validation (badge orange)

---

### Visual 5: Profil KYC
**Endpoint:** `GET /api/v1/profil`

**Retourne:**
```json
{
  "client_id": 1,
  "client_type": "INDIVIDUEL",
  "nom_complet": "Jean Dupont",
  "email": "jean.dupont@email.ht",
  "telephone": "+509 3812 5678",
  "adresse": {
    "ligne1": "45 Rue Grégoire, Pétion-Ville",
    "ville": "Port-au-Prince",
    "code_postal": "HT6140",
    "pays": "Haïti",
    "complete": "45 Rue Grégoire, Pétion-Ville, HT6140 Port-au-Prince, Haïti"
  },
  "profil_investisseur": {
    "statut": "Personne physique",
    "niveau_risque": "Modéré",
    "horizon_investissement": "Moyen terme",
    "revenu_annuel": "50k-75k USD"
  },
  "informations_individuel": {
    "prenom": "Jean",
    "nom": "Dupont",
    "date_naissance": "1985-03-15",
    "nationalite": "Haïtienne",
    "type_identite": "CIN",
    "numero_identite": "CIN-001-2020-12345",
    "profession": "Entrepreneur",
    "source_revenus": "Commerce et Investissements",
    "revenu_annuel_estime": 85000.00
  }
}
```

**Alimente:**
- Section "Informations personnelles"
  - Nom complet: Jean Dupont
  - Type de client: Individuel
  - Adresse email: jean.dupont@email.ht
  - Numéro de téléphone: +509 3812 5678
  - Adresse: 45 Rue Grégoire, Pétion-Ville, HT6140 Port-au-Prince, Haïti

- Section "Profil investisseur"
  - Statut: Personne physique
  - Niveau de risque accepté: Modéré
  - Horizon d'investissement: Moyen terme
  - Revenu annuel: 50k-75k USD

---

## 🚀 DÉMARRAGE RAPIDE

### 1. Installer les dépendances

```bash
pip install -r requirements.txt
```

### 2. Configurer la base de données

Vérifiez que votre fichier [app/core/config.py](app/core/config.py:25) contient les bonnes informations de connexion:

```python
DATABASE_URL: str = "mssql+pyodbc://sqladmin:Tsukuyomi777*@finance777.database.windows.net/Db_test?driver=ODBC+Driver+17+for+SQL+Server&TrustServerCertificate=yes"
```

### 3. Démarrer le serveur

```bash
python main.py
```

ou

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 4. Accéder à la documentation

- **Swagger UI:** http://localhost:8000/api/v1/docs
- **ReDoc:** http://localhost:8000/api/v1/redoc

---

## 🔑 AUTHENTIFICATION

Tous les endpoints (sauf `/auth/*`) nécessitent un Bearer token JWT.

### Exemple de flux d'authentification

#### 1. Login
```bash
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "marceus.jethro@email.ht",
    "password": "password123"
  }'
```

**Réponse:**
```json
{
  "success": true,
  "message": "Connexion réussie",
  "tokens": {
    "access_token": "eyJhbGciOiJIUzI1NiIs...",
    "refresh_token": "dGhpcyBpcyBhIHJlZnJl...",
    "token_type": "bearer",
    "expires_in": 1800
  },
  "client": {
    "client_id": 1,
    "email": "marceus.jethro@email.ht",
    "client_type": "INDIVIDUEL",
    "prenom": "Marceus",
    "nom": "Jethro"
  }
}
```

#### 2. Utiliser le token
```bash
curl -X GET "http://localhost:8000/api/v1/dashboard/overview" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIs..."
```

---

## 📝 EXEMPLES D'APPELS API

### Dashboard Complet
```javascript
// React/Next.js
const response = await fetch('http://localhost:8000/api/v1/dashboard/complet', {
  headers: {
    'Authorization': `Bearer ${accessToken}`
  }
});

const dashboard = await response.json();

// Utiliser dans votre composant
<DashboardOverview data={dashboard.overview} />
<RecentTransactions data={dashboard.transactions_recentes} />
<ActiveInvestments data={dashboard.investissements_actifs} />
<MonthlyChart data={dashboard.statistiques_mensuelles} />
```

### Profil Client
```javascript
const response = await fetch('http://localhost:8000/api/v1/profil', {
  headers: {
    'Authorization': `Bearer ${accessToken}`
  }
});

const profil = await response.json();

// Afficher les informations
<ProfileSection>
  <h3>{profil.nom_complet}</h3>
  <p>{profil.email}</p>
  <p>{profil.adresse.complete}</p>
</ProfileSection>
```

### Mes Comptes
```javascript
const response = await fetch('http://localhost:8000/api/v1/comptes/mes-comptes', {
  headers: {
    'Authorization': `Bearer ${accessToken}`
  }
});

const { comptes } = await response.json();

// Afficher les cartes de comptes
{comptes.map(compte => (
  <CompteCard
    key={compte.CompteID}
    numero={compte.NumeroCompte}
    type={compte.TypeCompte}
    solde={compte.Solde}
    devise={compte.Devise}
  />
))}
```

---

## 🔒 SYSTÈME DE RÔLES

Votre backend gère les rôles multi-utilisateurs via la table `ComptesRoles`:

| Rôle | Permissions |
|------|-------------|
| `TITULAIRE_PRINCIPAL` | Toutes les actions |
| `TITULAIRE_SECONDAIRE` | Toutes sauf gestion rôles |
| `MANDATAIRE` | Consultation + opérations |
| `OBSERVATEUR` | Consultation uniquement |
| `ADMINISTRATEUR` | Toutes (pour entreprises) |
| `BENEFICIAIRE` | Aucune (lecture future) |

**Exemple:** Marceus Jethro peut avoir:
- Rôle `TITULAIRE_PRINCIPAL` sur son compte personnel
- Rôle `ADMINISTRATEUR` sur le compte de Hotel Oasis SARL
- Rôle `TITULAIRE_PRINCIPAL` sur le compte joint avec Marie

Les endpoints filtrent automatiquement les données selon le rôle du client sur chaque compte.

---

## 🗄️ VUES SQL UTILISÉES

Les nouveaux endpoints utilisent directement les vues SQL que vous avez créées:

1. **`vw_Dashboard_Overview`** → `/dashboard/overview`
2. **`vw_Dashboard_DernieresTransactions`** → `/dashboard/transactions/recentes`
3. **`vw_Dashboard_InvestissementsActifs`** → `/dashboard/investissements`
4. **`vw_StatistiquesMensuelles`** → `/dashboard/statistiques/mensuelles`
5. **`vw_ProfilClient`** → `/profil`
6. **`vw_MesComptes`** → `/comptes/mes-comptes`
7. **`vw_MesInvestissements`** → `/souscriptions/mes-souscriptions`
8. **`vw_HistoriqueTransactions`** → `/transactions/mes-transactions`

Tous les services utilisent `text()` de SQLAlchemy pour exécuter des requêtes SQL brutes optimisées.

---

## ✅ CHECKLIST DE VÉRIFICATION

Avant de connecter votre frontend:

- [ ] Le serveur FastAPI démarre sans erreur
- [ ] La connexion à la base de données fonctionne
- [ ] Vous pouvez vous connecter avec un utilisateur test (marceus.jethro@email.ht)
- [ ] L'endpoint `/api/v1/dashboard/overview` retourne des données
- [ ] L'endpoint `/api/v1/profil` retourne le profil complet
- [ ] L'endpoint `/api/v1/comptes/mes-comptes` retourne les comptes
- [ ] La documentation Swagger est accessible
- [ ] Les CORS sont configurés pour votre frontend

---

## 🐛 DÉPANNAGE

### Erreur de connexion à la base de données

```
OperationalError: (pyodbc.OperationalError) ('08001', '[08001]...')
```

**Solution:** Vérifiez que:
1. Le serveur SQL est accessible
2. Les credentials sont corrects
3. Le driver ODBC 17 est installé
4. Le firewall autorise la connexion

### Erreur 401 Unauthorized

**Solution:** Vérifiez que:
1. Le token JWT est valide
2. Le token n'est pas expiré
3. Le header `Authorization: Bearer <token>` est présent

### Erreur 403 Forbidden

**Solution:**
Le client n'a pas les permissions nécessaires sur le compte.
Vérifiez le rôle du client dans `ComptesRoles`.

---

## 📚 PROCHAINES ÉTAPES

### Fonctionnalités à Ajouter

1. **Export CSV des transactions** → Endpoint `/transactions/export/csv`
2. **Recherche de transactions** → Query param `?search=salaire`
3. **Filtres avancés** → `?type=DEPOT&statut=EXECUTEE&date_debut=2024-01-01`
4. **Notifications** → Endpoint `/notifications` pour paiements d'intérêts à venir
5. **Documents** → Upload/Download de documents KYC

### Optimisations

1. **Caching Redis** → Cache les résultats du dashboard pour 5 minutes
2. **Pagination** → Ajouter pagination sur toutes les listes
3. **Rate Limiting** → Limiter à 100 requêtes/minute
4. **Logging** → Logger toutes les actions dans `JournalAudit`

---

## 🎉 CONCLUSION

Votre backend FastAPI est maintenant **conforme à votre base de données** et peut **alimenter tous les visuels de votre portail client React**.

**Endpoints disponibles:**
- ✅ Dashboard complet (overview, transactions, investissements, graphique)
- ✅ Profil client (KYC)
- ✅ Mes Comptes
- ✅ Mes Investissements
- ✅ Historique Transactions
- ✅ Authentification

**Tous les endpoints:**
- Respectent le système de rôles multi-utilisateurs
- Utilisent les vues SQL optimisées
- Filtrent les données par ClientID
- Retournent des réponses structurées (Pydantic)
- Sont documentés dans Swagger

**Prêt pour le développement frontend! 🚀**
