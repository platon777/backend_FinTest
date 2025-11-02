# MAPPING VUES SQL → ENDPOINTS API
## Guide d'utilisation des vues SQL existantes dans l'API

---

## APERÇU

Ce document explique comment chaque vue SQL créée dans `vue_sql.sql` est utilisée par les endpoints API pour alimenter le frontend React.

---

## 1. VUE: `vw_Dashboard_Overview`

### Description
Vue agrégée qui calcule les statistiques globales du portefeuille pour un client donné.

### Colonnes
- `ClientID` - ID du client
- `CompteID` - ID du compte
- `NumeroCompte` - Numéro du compte
- `DeviseCompte` - Devise du compte
- `ValeurTotale` - Valeur totale du portefeuille
- `RendementTotal` - Total des intérêts accumulés
- `PourcentageRendement` - Rendement en %
- `NombreSouscriptionsActives` - Nombre d'investissements actifs
- `TotalInvesti` - Montant total investi

### Utilisée par l'Endpoint
**GET** `/api/v1/dashboard/overview`

### Requête SQL dans le Controller
```sql
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
WHERE cr.ClientID = @clientId
  AND cr.EstActif = 1
  AND cpt.StatutCompte = 'ACTIF'
  AND cr.Role IN ('TITULAIRE_PRINCIPAL', 'MANDATAIRE', 'OBSERVATEUR')
GROUP BY cr.ClientID, cr.CompteID, cpt.NumeroCompte, cpt.Devise
```

### Alimente la Vue Frontend
**Dashboard** - Section "Vue d'ensemble du portefeuille"
- Valeur totale: 50 000,00 $US
- Rendement total: +2 600,00 $US (5.2%)
- Souscriptions actives: 2

---

## 2. VUE: `vw_Dashboard_DernieresTransactions`

### Description
Retourne les dernières transactions pour chaque compte du client, avec un numéro de ligne pour faciliter la limitation.

### Colonnes
- `ClientID` - ID du client
- `CompteID` - ID du compte
- `TransactionID` - ID de la transaction
- `TypeTransaction` - Type (DEPOT, RETRAIT, etc.)
- `Description` - Description
- `Montant` - Montant
- `Devise` - Devise
- `DateCreation` - Date de création
- `DateExecution` - Date d'exécution
- `StatutTransaction` - Statut
- `CompteSource` - Numéro compte source
- `CompteDestination` - Numéro compte destination
- `RowNum` - Numéro de ligne (pour TOP N)

### Utilisée par l'Endpoint
**GET** `/api/v1/dashboard/transactions/recentes`

### Requête SQL dans le Controller
```sql
SELECT TOP (@limit)
  t.TransactionID,
  t.TypeTransaction,
  t.Description,
  t.Montant,
  t.Devise,
  t.DateCreation,
  t.DateExecution,
  t.StatutTransaction,
  cptSrc.NumeroCompte AS CompteSource,
  cptDest.NumeroCompte AS CompteDestination
FROM ComptesRoles cr
INNER JOIN Comptes cpt ON cr.CompteID = cpt.CompteID
LEFT JOIN Transactions t ON (t.CompteSource = cpt.CompteID OR t.CompteDestination = cpt.CompteID)
LEFT JOIN Comptes cptSrc ON t.CompteSource = cptSrc.CompteID
LEFT JOIN Comptes cptDest ON t.CompteDestination = cptDest.CompteID
WHERE cr.ClientID = @clientId
  AND cr.EstActif = 1
  AND cr.Role IN ('TITULAIRE_PRINCIPAL', 'MANDATAIRE', 'OBSERVATEUR')
ORDER BY ISNULL(t.DateExecution, t.DateCreation) DESC
```

### Alimente la Vue Frontend
**Dashboard** - Section "Dernières transactions"
- Liste des 3 dernières transactions avec date, description, montant, statut

---

## 3. VUE: `vw_Dashboard_InvestissementsActifs`

### Description
Aperçu des investissements actifs avec progression vers la maturité.

### Colonnes
- `ClientID` - ID du client
- `CompteID` - ID du compte
- `SouscriptionID` - ID de la souscription
- `NomInstrument` - Nom de l'instrument
- `CodeInstrument` - Code de l'instrument
- `MontantInvesti` - Montant investi
- `ValeurActuelle` - Valeur actuelle
- `TauxSouscription` - Taux à la souscription
- `DateMaturiteEffective` - Date de maturité
- `InteretsAccumules` - Intérêts accumulés
- `ProgressionMaturite` - Progression en % vers maturité

### Utilisée par l'Endpoint
**GET** `/api/v1/dashboard/investissements`

### Requête SQL dans le Controller
```sql
SELECT
  s.SouscriptionID,
  cr.CompteID,
  i.Nom AS NomInstrument,
  i.Code AS CodeInstrument,
  s.MontantInvesti,
  s.ValeurActuelle,
  s.TauxSouscription,
  s.DateMaturiteEffective,
  s.InteretsAccumules,
  CASE
    WHEN DATEDIFF(DAY, s.DateSouscription, s.DateMaturiteEffective) > 0
    THEN CAST(DATEDIFF(DAY, s.DateSouscription, GETDATE()) AS FLOAT) /
         DATEDIFF(DAY, s.DateSouscription, s.DateMaturiteEffective) * 100
    ELSE 0
  END AS ProgressionMaturite,
  s.StatutSouscription
FROM ComptesRoles cr
INNER JOIN Comptes cpt ON cr.CompteID = cpt.CompteID
INNER JOIN Souscriptions s ON cpt.CompteID = s.CompteID
INNER JOIN Instruments i ON s.InstrumentID = i.InstrumentID
WHERE cr.ClientID = @clientId
  AND cr.EstActif = 1
  AND s.StatutSouscription = 'ACTIVE'
  AND cr.Role IN ('TITULAIRE_PRINCIPAL', 'MANDATAIRE', 'OBSERVATEUR')
```

### Alimente la Vue Frontend
**Dashboard** - Section "Investissements Actifs"
- Obligation BRH 5.5% 2025
- Montant: 20 000,00 $US
- Maturité: 14/06/2025
- Progression: 75%

---

## 4. VUE: `vw_MesComptes`

### Description
Liste complète des comptes accessibles par le client avec leurs soldes et rôles.

### Colonnes
- `ClientID` - ID du client
- `CompteID` - ID du compte
- `Role` - Rôle sur le compte
- `NumeroCompte` - Numéro du compte
- `TypeCompte` - Type (INVESTISSEMENT, EPARGNE, etc.)
- `Devise` - Devise
- `SoldeTotal` - Solde total
- `SoldeDisponible` - Solde disponible
- `DateOuverture` - Date d'ouverture
- `StatutCompte` - Statut
- `NomTitulaire` - Nom du titulaire principal

### Utilisée par l'Endpoint
**GET** `/api/v1/comptes`

### Requête SQL dans le Controller
```sql
SELECT
  cr.ClientID,
  cr.CompteID,
  cr.Role,
  cpt.NumeroCompte,
  cpt.TypeCompte,
  cpt.Devise,
  cpt.Solde AS SoldeTotal,
  cpt.SoldeDisponible,
  cpt.DateOuverture,
  cpt.StatutCompte,
  CASE
    WHEN ci.Nom IS NOT NULL THEN ci.Prenom + ' ' + ci.Nom
    ELSE cin.NomEntreprise
  END AS NomTitulaire
FROM ComptesRoles cr
INNER JOIN Comptes cpt ON cr.CompteID = cpt.CompteID
LEFT JOIN ComptesRoles crPrincipal ON cpt.CompteID = crPrincipal.CompteID
  AND crPrincipal.Role = 'TITULAIRE_PRINCIPAL'
  AND crPrincipal.EstActif = 1
LEFT JOIN Clients cTit ON crPrincipal.ClientID = cTit.ClientID
LEFT JOIN ClientsIndividuels ci ON cTit.ClientID = ci.ClientID
LEFT JOIN ClientsInstitutionnels cin ON cTit.ClientID = cin.ClientID
WHERE cr.ClientID = @clientId
  AND cr.EstActif = 1
  AND cpt.StatutCompte = 'ACTIF'
```

### Alimente la Vue Frontend
**Mes Comptes** - Liste de tous les comptes
- Investissement INV-2023-00001 (USD)
  - Solde Total: 52 600,00 $US
  - Solde Disponible: 2 600,00 $US
  - Statut: ACTIF

---

## 5. VUE: `vw_MesInvestissements`

### Description
Vue détaillée de tous les investissements avec calculs de gain/perte et progression.

### Colonnes Principales
- `ClientID`, `CompteID`, `SouscriptionID`
- **Instrument:** `InstrumentID`, `CodeInstrument`, `NomInstrument`, `Emetteur`, `TypeInstrument`
- **Montants:** `MontantInvesti`, `ValeurActuelle`, `InteretsAccumules`, `NombreUnites`
- **Taux:** `TauxSouscription`, `TMA_Reel`, `TauxInstrument`, `FrequencePaiementInterets`
- **Dates:** `DateSouscription`, `DateMaturiteEffective`, `JoursRestants`
- **Calculs:** `ProgressionPourcentage`, `GainPerte`, `GainPertePourcentage`

### Utilisée par les Endpoints
1. **GET** `/api/v1/investissements` - Liste paginée
2. **GET** `/api/v1/investissements/:id` - Détails d'un investissement

### Requête SQL dans le Controller (Liste)
```sql
SELECT
  cr.ClientID,
  cr.CompteID,
  s.SouscriptionID,
  s.StatutSouscription,
  -- Instrument
  i.InstrumentID,
  i.Code AS CodeInstrument,
  i.Nom AS NomInstrument,
  i.Emetteur,
  ti.Nom AS TypeInstrument,
  -- Montants
  s.MontantInvesti,
  s.ValeurActuelle,
  s.InteretsAccumules,
  s.NombreUnites,
  -- Taux
  s.TauxSouscription,
  s.TMA_Reel,
  i.TauxRendementAnnuel AS TauxInstrument,
  i.FrequencePaiementInterets,
  -- Dates
  s.DateSouscription,
  s.DateMaturiteEffective,
  DATEDIFF(DAY, GETDATE(), s.DateMaturiteEffective) AS JoursRestants,
  -- Progression
  CASE
    WHEN DATEDIFF(DAY, s.DateSouscription, s.DateMaturiteEffective) > 0
    THEN CAST(DATEDIFF(DAY, s.DateSouscription, GETDATE()) AS FLOAT) /
         DATEDIFF(DAY, s.DateSouscription, s.DateMaturiteEffective) * 100
    ELSE 0
  END AS ProgressionPourcentage,
  -- Gain/Perte
  (s.ValeurActuelle - s.MontantInvesti) AS GainPerte,
  CASE
    WHEN s.MontantInvesti > 0
    THEN ((s.ValeurActuelle - s.MontantInvesti) / s.MontantInvesti) * 100
    ELSE 0
  END AS GainPertePourcentage
FROM ComptesRoles cr
INNER JOIN Comptes cpt ON cr.CompteID = cpt.CompteID
INNER JOIN Souscriptions s ON cpt.CompteID = s.CompteID
INNER JOIN Instruments i ON s.InstrumentID = i.InstrumentID
INNER JOIN TypesInstruments ti ON i.TypeInstrumentID = ti.TypeInstrumentID
WHERE cr.ClientID = @clientId
  AND cr.EstActif = 1
  AND cr.Role IN ('TITULAIRE_PRINCIPAL', 'MANDATAIRE', 'OBSERVATEUR')
  -- Filtres optionnels
  AND (@statut IS NULL OR s.StatutSouscription = @statut)
  AND (@compteId IS NULL OR cr.CompteID = @compteId)
ORDER BY s.DateMaturiteEffective
```

### Alimente la Vue Frontend
**Mes Investissements** - Liste détaillée avec filtres
- Obligation BRH 5.5% 2025
  - Souscription ID: 2001
  - Montant Investi: 20 000,00 $US
  - Taux à la souscription: 5.5%
  - Valeur Actuelle: 20 900,00 $US
  - Souscription: 14/06/2023
  - Maturité: 14/06/2025
  - Progression: 75%
  - Statut: ACTIVE

---

## 6. VUE: `vw_HistoriqueTransactions`

### Description
Vue complète de toutes les transactions accessibles par le client avec informations de comptes et souscriptions liées.

### Colonnes
- `ClientID`, `TransactionID`
- `TypeTransaction`, `Description`, `Montant`, `Devise`
- `StatutTransaction`, `DateCreation`, `DateExecution`, `EstAutomatique`
- `CompteSource`, `NumeroCompteSource`, `TypeCompteSource`
- `CompteDestination`, `NumeroCompteDestination`, `TypeCompteDestination`
- `SouscriptionID`, `CodeInstrument`, `NomInstrument`
- `DateEffective` - Date effective pour tri (DateExecution ou DateCreation)

### Utilisée par les Endpoints
1. **GET** `/api/v1/transactions` - Historique complet
2. **GET** `/api/v1/transactions/:id` - Détails d'une transaction
3. **GET** `/api/v1/transactions/export/csv` - Export CSV

### Requête SQL dans le Controller (Historique)
```sql
SELECT
  cr.ClientID,
  t.TransactionID,
  t.TypeTransaction,
  t.Description,
  t.Montant,
  t.Devise,
  t.StatutTransaction,
  t.DateCreation,
  t.DateExecution,
  t.EstAutomatique,
  t.Commentaires,
  -- Comptes
  t.CompteSource,
  cptSrc.NumeroCompte AS NumeroCompteSource,
  cptSrc.TypeCompte AS TypeCompteSource,
  t.CompteDestination,
  cptDest.NumeroCompte AS NumeroCompteDestination,
  cptDest.TypeCompte AS TypeCompteDestination,
  -- Souscription liée
  s.SouscriptionID,
  i.Code AS CodeInstrument,
  i.Nom AS NomInstrument,
  -- Date effective
  ISNULL(t.DateExecution, t.DateCreation) AS DateEffective
FROM ComptesRoles cr
INNER JOIN Comptes cptClient ON cr.CompteID = cptClient.CompteID
LEFT JOIN Transactions t ON (t.CompteSource = cptClient.CompteID OR t.CompteDestination = cptClient.CompteID)
LEFT JOIN Comptes cptSrc ON t.CompteSource = cptSrc.CompteID
LEFT JOIN Comptes cptDest ON t.CompteDestination = cptDest.CompteID
LEFT JOIN Souscriptions s ON t.SouscriptionID = s.SouscriptionID
LEFT JOIN Instruments i ON s.InstrumentID = i.InstrumentID
WHERE cr.ClientID = @clientId
  AND cr.EstActif = 1
  AND cr.Role IN ('TITULAIRE_PRINCIPAL', 'MANDATAIRE', 'OBSERVATEUR', 'ADMINISTRATEUR')
  -- Filtres optionnels
  AND (@typeTransaction IS NULL OR t.TypeTransaction = @typeTransaction)
  AND (@statut IS NULL OR t.StatutTransaction = @statut)
  AND (@dateDebut IS NULL OR t.DateCreation >= @dateDebut)
  AND (@dateFin IS NULL OR t.DateCreation <= @dateFin)
  AND (@search IS NULL OR t.Description LIKE '%' + @search + '%')
ORDER BY DateEffective DESC
OFFSET @offset ROWS FETCH NEXT @limit ROWS ONLY
```

### Alimente la Vue Frontend
**Historique des Transactions** - Tableau avec recherche et filtres
- 25/07/2024 | Retrait en ligne | INV-2023-00001 | N/A | -1000,00 $US | En Attente Validation
- 20/07/2024 | Virement entrant salaire | N/A | INV-2023-00001 | 5000,00 $US | Executée
- Bouton: **Exporter en CSV**

---

## 7. VUE: `vw_ProfilClient`

### Description
Informations complètes du profil client incluant données personnelles, adresse, contacts et authentification.

### Colonnes
- **Client:** `ClientID`, `ClientType`, `ProfilRisque`, `StatutClient`, `DateCreation`
- **Individuel:** `Prenom`, `Nom`, `NomComplet`, `DateNaissance`, `Nationalite`, `TypePieceIdentite`, `NumeroPieceIdentite`, `Profession`, `RevenuAnnuelEstime`
- **Institutionnel:** `NomEntreprise`, `NumeroRegistreCommerce`, `FormeJuridique`, `Secteur`, `DateCreationEntreprise`, `ChiffreAffairesAnnuel`, `NomRepresentantLegal`
- **Adresse:** `AdresseLigne1`, `AdresseLigne2`, `Ville`, `CodePostal`, `Pays`, `AdresseComplete`
- **Contact:** `Email`, `Telephone`
- **Auth:** `EmailConnexion`, `DateDerniereConnexion`

### Utilisée par l'Endpoint
**GET** `/api/v1/profil`

### Requête SQL dans le Controller
```sql
SELECT
  c.ClientID,
  c.ClientType,
  c.ProfilRisque,
  c.StatutClient,
  c.DateCreation,
  -- Individuel
  ci.Prenom,
  ci.Nom,
  CONCAT(ci.Prenom, ' ', ci.Nom) AS NomComplet,
  ci.DateNaissance,
  ci.Nationalite,
  ci.TypePieceIdentite,
  ci.NumeroPieceIdentite,
  ci.Profession,
  ci.RevenuAnnuelEstime,
  -- Institutionnel
  cin.NomEntreprise,
  cin.NumeroRegistreCommerce,
  cin.FormeJuridique,
  cin.Secteur,
  cin.DateCreationEntreprise,
  cin.ChiffreAffairesAnnuel,
  cin.NomRepresentantLegal,
  -- Adresse
  adr.AdresseLigne1,
  adr.AdresseLigne2,
  adr.Ville,
  adr.CodePostal,
  adr.Pays,
  CONCAT(adr.AdresseLigne1,
         CASE WHEN adr.AdresseLigne2 IS NOT NULL THEN ', ' + adr.AdresseLigne2 ELSE '' END,
         ', ', adr.CodePostal, ' ', adr.Ville, ', ', adr.Pays) AS AdresseComplete,
  -- Contact
  ctEmail.Valeur AS Email,
  ctTel.Valeur AS Telephone,
  -- Auth
  auth.Email AS EmailConnexion,
  auth.DateDerniereConnexion
FROM Clients c
LEFT JOIN ClientsIndividuels ci ON c.ClientID = ci.ClientID
LEFT JOIN ClientsInstitutionnels cin ON c.ClientID = cin.ClientID
LEFT JOIN AdressesClients adr ON c.ClientID = adr.ClientID AND adr.EstPrincipale = 1
LEFT JOIN ContactsClients ctEmail ON c.ClientID = ctEmail.ClientID
  AND ctEmail.TypeContact = 'EMAIL' AND ctEmail.EstPrincipal = 1
LEFT JOIN ContactsClients ctTel ON c.ClientID = ctTel.ClientID
  AND ctTel.TypeContact IN ('TELEPHONE', 'MOBILE') AND ctTel.EstPrincipal = 1
LEFT JOIN ClientsAuthentification auth ON c.ClientID = auth.ClientID
WHERE c.ClientID = @clientId
```

### Alimente la Vue Frontend
**Profil KYC** - Informations personnelles

**Informations personnelles:**
- Nom complet: Jean Dupont
- Type de client: Individuel
- Adresse email: jean.dupont@email.com
- Numéro de téléphone: +33 6 12 34 56 78
- Adresse: 123 Rue de la République, 75001 Paris, France

**Profil investisseur:**
- Statut: Personne physique
- Niveau de risque accepté: Modéré
- Horizon d'investissement: Moyen terme
- Revenu annuel: 50k-75k USD

---

## 8. VUE: `vw_ComptesAccessibles`

### Description
Liste simplifiée des comptes accessibles pour le sélecteur de compte (dropdown) dans le header.

### Colonnes
- `ClientID`, `CompteID`, `Role`
- `NumeroCompte`, `TypeCompte`, `Devise`
- `LabelCompte` - Label formaté pour affichage
- `TypeRelation` - Relation en français (Personnel, Mandataire, etc.)
- `EstComptePersonnel` - Boolean (1 si TITULAIRE_PRINCIPAL, 0 sinon)

### Utilisée par l'Endpoint
**GET** `/api/v1/comptes` (avec paramètre `?minimal=true`)

### Requête SQL dans le Controller
```sql
SELECT
  cr.ClientID,
  cr.CompteID,
  cr.Role,
  cpt.NumeroCompte,
  cpt.TypeCompte,
  cpt.Devise,
  -- Label formaté
  CASE
    WHEN ciTit.Nom IS NOT NULL THEN
      CONCAT(ciTit.Prenom, ' ', ciTit.Nom, ' - ', cpt.TypeCompte)
    WHEN cinTit.NomEntreprise IS NOT NULL THEN
      CONCAT(cinTit.NomEntreprise, ' - ', cpt.TypeCompte)
    ELSE
      CONCAT(cpt.TypeCompte, ' - ', cpt.NumeroCompte)
  END AS LabelCompte,
  -- Type de relation
  CASE
    WHEN cr.Role = 'TITULAIRE_PRINCIPAL' THEN 'Personnel'
    WHEN cr.Role = 'MANDATAIRE' THEN 'Mandataire'
    WHEN cr.Role = 'OBSERVATEUR' THEN 'Observateur'
    WHEN cr.Role = 'ADMINISTRATEUR' THEN 'Administrateur'
    ELSE cr.Role
  END AS TypeRelation,
  -- Est compte personnel ?
  CASE WHEN cr.Role = 'TITULAIRE_PRINCIPAL' THEN 1 ELSE 0 END AS EstComptePersonnel
FROM ComptesRoles cr
INNER JOIN Comptes cpt ON cr.CompteID = cpt.CompteID
LEFT JOIN ComptesRoles crTit ON cpt.CompteID = crTit.CompteID
  AND crTit.Role = 'TITULAIRE_PRINCIPAL' AND crTit.EstActif = 1
LEFT JOIN Clients cTit ON crTit.ClientID = cTit.ClientID
LEFT JOIN ClientsIndividuels ciTit ON cTit.ClientID = ciTit.ClientID
LEFT JOIN ClientsInstitutionnels cinTit ON cTit.ClientID = cinTit.ClientID
WHERE cr.ClientID = @clientId
  AND cr.EstActif = 1
  AND cpt.StatutCompte = 'ACTIF'
ORDER BY EstComptePersonnel DESC, LabelCompte
```

### Alimente la Vue Frontend
**Header** - Sélecteur de compte (dropdown)
```
Jean Dupont
Personnel ▼

┌─────────────────────────────────────┐
│ Marceus Jethro - INVESTISSEMENT     │ <- TITULAIRE_PRINCIPAL
│ Hotel Oasis SARL - INVESTISSEMENT   │ <- ADMINISTRATEUR
│ Marceus & Marie - INVESTISSEMENT    │ <- TITULAIRE_PRINCIPAL
└─────────────────────────────────────┘
```

---

## 9. VUE: `vw_StatistiquesMensuelles`

### Description
Génère les statistiques mensuelles (12 derniers mois) pour le graphique du dashboard.

### Colonnes
- `ClientID`, `CompteID`
- `DateMois` - Premier jour du mois
- `NomMois` - Nom du mois
- `ValeurPortefeuille` - Valeur totale du portefeuille ce mois
- `NombreSouscriptions` - Nombre de souscriptions actives ce mois

### Utilisée par l'Endpoint
**GET** `/api/v1/dashboard/statistiques/mensuelles`

### Requête SQL dans le Controller
```sql
WITH MoisRecents AS (
  -- Générer les 12 derniers mois
  SELECT DATEADD(MONTH, -n, DATEFROMPARTS(YEAR(GETDATE()), MONTH(GETDATE()), 1)) AS DateMois
  FROM (
    SELECT 0 AS n UNION ALL SELECT 1 UNION ALL SELECT 2 UNION ALL
    SELECT 3 UNION ALL SELECT 4 UNION ALL SELECT 5 UNION ALL
    SELECT 6 UNION ALL SELECT 7 UNION ALL SELECT 8 UNION ALL
    SELECT 9 UNION ALL SELECT 10 UNION ALL SELECT 11
  ) AS Nombres
)
SELECT
  cr.ClientID,
  cr.CompteID,
  m.DateMois,
  DATENAME(MONTH, m.DateMois) AS NomMois,
  ISNULL(SUM(s.ValeurActuelle), 0) AS ValeurPortefeuille,
  COUNT(s.SouscriptionID) AS NombreSouscriptions
FROM MoisRecents m
CROSS JOIN ComptesRoles cr
INNER JOIN Comptes cpt ON cr.CompteID = cpt.CompteID
LEFT JOIN Souscriptions s ON cpt.CompteID = s.CompteID
  AND s.DateSouscription <= EOMONTH(m.DateMois)
  AND (s.DateMaturiteEffective >= m.DateMois OR s.DateMaturiteEffective IS NULL)
  AND s.StatutSouscription = 'ACTIVE'
WHERE cr.ClientID = @clientId
  AND cr.EstActif = 1
  AND cr.Role IN ('TITULAIRE_PRINCIPAL', 'MANDATAIRE')
  AND (@compteId IS NULL OR cr.CompteID = @compteId)
GROUP BY cr.ClientID, cr.CompteID, m.DateMois
ORDER BY m.DateMois
```

### Alimente la Vue Frontend
**Dashboard** - Graphique "Vue d'ensemble du portefeuille"

Graphique à barres affichant la valeur du portefeuille pour chaque mois:
```
60k ┤
    │         ███
45k ┤   ███   ███   ███   ███   ███   ███
    │   ███   ███   ███   ███   ███   ███
30k ┤   ███   ███   ███   ███   ███   ███
    │   ███   ███   ███   ███   ███   ███
15k ┤   ███   ███   ███   ███   ███   ███
    │   ███   ███   ███   ███   ███   ███
 0k └───┴───┴───┴───┴───┴───┴───┴───┴───
     Jan Fév Mar Avr Mai Juin
```

---

## 10. VUE: `vw_ProchainsInterets`

### Description
Liste des paiements d'intérêts planifiés à venir (pour notifications).

### Colonnes
- `ClientID`, `CompteID`, `SouscriptionID`
- `NomInstrument`, `CodeInstrument`
- `DatePaiement`, `MontantInteret`, `StatutPaiement`
- `JoursAvantPaiement` - Nombre de jours avant le paiement

### Utilisée par l'Endpoint
**GET** `/api/v1/notifications` (optionnel, future feature)

### Requête SQL dans le Controller
```sql
SELECT
  cr.ClientID,
  cr.CompteID,
  s.SouscriptionID,
  i.Nom AS NomInstrument,
  i.Code AS CodeInstrument,
  pi.DatePaiement,
  pi.MontantInteret,
  pi.StatutPaiement,
  DATEDIFF(DAY, GETDATE(), pi.DatePaiement) AS JoursAvantPaiement
FROM ComptesRoles cr
INNER JOIN Comptes cpt ON cr.CompteID = cpt.CompteID
INNER JOIN Souscriptions s ON cpt.CompteID = s.CompteID
INNER JOIN Instruments i ON s.InstrumentID = i.InstrumentID
INNER JOIN PaiementsInterets pi ON s.SouscriptionID = pi.SouscriptionID
WHERE cr.ClientID = @clientId
  AND cr.EstActif = 1
  AND s.StatutSouscription = 'ACTIVE'
  AND pi.StatutPaiement IN ('PLANIFIE', 'EN_ATTENTE')
  AND pi.DatePaiement >= GETDATE()
  AND cr.Role IN ('TITULAIRE_PRINCIPAL', 'MANDATAIRE', 'OBSERVATEUR')
ORDER BY pi.DatePaiement
```

### Alimente la Vue Frontend
**Notifications** (optionnel) - Prochains paiements d'intérêts
- "Paiement d'intérêts prévu dans 5 jours: 250,00 $US (OBL-BRH-2025)"

---

## RÉSUMÉ DU MAPPING

| Vue SQL | Endpoint API | Vue Frontend |
|---------|-------------|--------------|
| `vw_Dashboard_Overview` | `GET /dashboard/overview` | Dashboard - Vue d'ensemble |
| `vw_Dashboard_DernieresTransactions` | `GET /dashboard/transactions/recentes` | Dashboard - Dernières transactions |
| `vw_Dashboard_InvestissementsActifs` | `GET /dashboard/investissements` | Dashboard - Investissements actifs |
| `vw_MesComptes` | `GET /comptes` | Mes Comptes - Liste |
| `vw_MesInvestissements` | `GET /investissements` | Mes Investissements - Liste |
| `vw_HistoriqueTransactions` | `GET /transactions` | Historique - Tableau |
| `vw_ProfilClient` | `GET /profil` | Profil KYC |
| `vw_ComptesAccessibles` | `GET /comptes?minimal=true` | Header - Sélecteur |
| `vw_StatistiquesMensuelles` | `GET /dashboard/statistiques/mensuelles` | Dashboard - Graphique |
| `vw_ProchainsInterets` | `GET /notifications` | Notifications |

---

## NOTES IMPORTANTES

### 1. Filtrage par ClientID
**TOUTES les requêtes doivent ABSOLUMENT filtrer par `ClientID`** pour la sécurité:
```sql
WHERE cr.ClientID = @clientId
```

### 2. Filtrage par Rôle
Les vues de consultation incluent généralement:
```sql
AND cr.Role IN ('TITULAIRE_PRINCIPAL', 'MANDATAIRE', 'OBSERVATEUR')
```

Pour les actions d'administration:
```sql
AND cr.Role IN ('TITULAIRE_PRINCIPAL', 'ADMINISTRATEUR')
```

### 3. Comptes Actifs
Toujours filtrer les comptes et rôles actifs:
```sql
AND cr.EstActif = 1
AND cpt.StatutCompte = 'ACTIF'
```

### 4. Pagination
Pour les listes longues, utiliser `OFFSET` et `FETCH`:
```sql
ORDER BY DateEffective DESC
OFFSET @offset ROWS FETCH NEXT @limit ROWS ONLY
```

### 5. Requêtes Paramétrées
Toujours utiliser des paramètres pour éviter les injections SQL:
```javascript
await sequelize.query(query, {
  replacements: { clientId, compteId },
  type: sequelize.QueryTypes.SELECT
});
```

---

## OPTIMISATIONS RECOMMANDÉES

### Index Existants (créés dans vue_sql.sql)
- `IX_ComptesRoles_ClientID_EstActif` sur `ComptesRoles(ClientID, EstActif)`
- `IX_Souscriptions_CompteID_Statut` sur `Souscriptions(CompteID, StatutSouscription)`
- `IX_Transactions_Comptes_Date` sur `Transactions(CompteSource, CompteDestination, DateCreation)`

### Autres Index Recommandés
```sql
-- Pour filtrage rapide des transactions par client
CREATE INDEX IX_Transactions_ClientSource
ON Transactions(CompteSource, DateCreation DESC)
INCLUDE (TypeTransaction, StatutTransaction);

-- Pour recherche d'instruments
CREATE INDEX IX_Instruments_Statut
ON Instruments(StatutInstrument)
INCLUDE (Code, Nom, TauxRendementAnnuel);
```

---

## CONCLUSION

Ce mapping vous permet de:
✅ **Utiliser efficacement** les 10 vues SQL existantes
✅ **Filtrer correctement** les données selon le rôle du client
✅ **Optimiser les performances** avec les index appropriés
✅ **Sécuriser** les accès multi-rôles
✅ **Alimenter le frontend** React avec toutes les données nécessaires
