

-- ============================================================================
-- VUES SQL POUR LE PORTAIL CLIENT - PROFIN BANK
-- ============================================================================

PRINT 'Création des vues pour le portail client...';
GO

-- ============================================================================
-- VUE 1 : DASHBOARD - Vue d'ensemble du portefeuille
-- ============================================================================

-- Récupère les statistiques globales pour un client donné
CREATE OR ALTER VIEW vw_Dashboard_Overview AS
SELECT 
    cr.ClientID,
    cr.CompteID,
    cpt.NumeroCompte,
    cpt.Devise AS DeviseCompte,
    
    -- Valeur totale du portefeuille
    ISNULL(SUM(s.ValeurActuelle), 0) AS ValeurTotale,
    
    -- Rendement total (intérêts accumulés)
    ISNULL(SUM(s.InteretsAccumules), 0) AS RendementTotal,
    
    -- Pourcentage de rendement
    CASE 
        WHEN SUM(s.MontantInvesti) > 0 
        THEN (SUM(s.InteretsAccumules) / SUM(s.MontantInvesti)) * 100
        ELSE 0 
    END AS PourcentageRendement,
    
    -- Nombre de souscriptions actives
    COUNT(s.SouscriptionID) AS NombreSouscriptionsActives,
    
    -- Total investi
    ISNULL(SUM(s.MontantInvesti), 0) AS TotalInvesti

FROM ComptesRoles cr
INNER JOIN Comptes cpt ON cr.CompteID = cpt.CompteID
LEFT JOIN Souscriptions s ON cpt.CompteID = s.CompteID AND s.StatutSouscription = 'ACTIVE'
WHERE cr.EstActif = 1 
    AND cpt.StatutCompte = 'ACTIF'
    AND cr.Role IN ('TITULAIRE_PRINCIPAL', 'MANDATAIRE', 'OBSERVATEUR')
GROUP BY cr.ClientID, cr.CompteID, cpt.NumeroCompte, cpt.Devise;
GO

-- ============================================================================
-- VUE 2 : DASHBOARD - Dernières transactions (3 dernières)
-- ============================================================================

CREATE OR ALTER VIEW vw_Dashboard_DernieresTransactions AS
SELECT 
    cr.ClientID,
    cr.CompteID,
    t.TransactionID,
    t.TypeTransaction,
    t.Description,
    t.Montant,
    t.Devise,
    t.DateCreation,
    t.DateExecution,
    t.StatutTransaction,
    cptSrc.NumeroCompte AS CompteSource,
    cptDest.NumeroCompte AS CompteDestination,
    
    -- Numéro de ligne pour limiter aux 3 dernières
    ROW_NUMBER() OVER (PARTITION BY cr.ClientID, cr.CompteID ORDER BY ISNULL(t.DateExecution, t.DateCreation) DESC) AS RowNum

FROM ComptesRoles cr
INNER JOIN Comptes cpt ON cr.CompteID = cpt.CompteID
LEFT JOIN Transactions t ON (t.CompteSource = cpt.CompteID OR t.CompteDestination = cpt.CompteID)
LEFT JOIN Comptes cptSrc ON t.CompteSource = cptSrc.CompteID
LEFT JOIN Comptes cptDest ON t.CompteDestination = cptDest.CompteID
WHERE cr.EstActif = 1 
    AND cr.Role IN ('TITULAIRE_PRINCIPAL', 'MANDATAIRE', 'OBSERVATEUR');
GO

-- ============================================================================
-- VUE 3 : DASHBOARD - Investissements actifs (aperçu)
-- ============================================================================

CREATE OR ALTER VIEW vw_Dashboard_InvestissementsActifs AS
SELECT 
    cr.ClientID,
    cr.CompteID,
    s.SouscriptionID,
    i.Nom AS NomInstrument,
    i.Code AS CodeInstrument,
    s.MontantInvesti,
    s.ValeurActuelle,
    s.TauxSouscription,
    s.DateMaturiteEffective,
    s.InteretsAccumules,
    
    -- Calcul progression vers maturité (%)
    CASE 
        WHEN DATEDIFF(DAY, s.DateSouscription, s.DateMaturiteEffective) > 0
        THEN CAST(DATEDIFF(DAY, s.DateSouscription, GETDATE()) AS FLOAT) / 
             DATEDIFF(DAY, s.DateSouscription, s.DateMaturiteEffective) * 100
        ELSE 0
    END AS ProgressionMaturite

FROM ComptesRoles cr
INNER JOIN Comptes cpt ON cr.CompteID = cpt.CompteID
INNER JOIN Souscriptions s ON cpt.CompteID = s.CompteID
INNER JOIN Instruments i ON s.InstrumentID = i.InstrumentID
WHERE cr.EstActif = 1
    AND s.StatutSouscription = 'ACTIVE'
    AND cr.Role IN ('TITULAIRE_PRINCIPAL', 'MANDATAIRE', 'OBSERVATEUR');
GO

-- ============================================================================
-- VUE 4 : MES COMPTES - Liste des comptes avec soldes
-- ============================================================================

CREATE OR ALTER VIEW vw_MesComptes AS
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
    
    -- Nom du titulaire principal (pour affichage)
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
WHERE cr.EstActif = 1 
    AND cpt.StatutCompte = 'ACTIF';
GO

-- ============================================================================
-- VUE 5 : MES INVESTISSEMENTS - Détails complets
-- ============================================================================

CREATE OR ALTER VIEW vw_MesInvestissements AS
SELECT 
    cr.ClientID,
    cr.CompteID,
    s.SouscriptionID,
    s.StatutSouscription,
    
    -- Informations instrument
    i.InstrumentID,
    i.Code AS CodeInstrument,
    i.Nom AS NomInstrument,
    i.Emetteur,
    i.TypeInstrumentID,
    ti.Nom AS TypeInstrument,
    
    -- Montants et valeurs
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
    i.DateMaturite AS DateMaturiteInstrument,
    
    -- Calculs
    DATEDIFF(DAY, GETDATE(), s.DateMaturiteEffective) AS JoursRestants,
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
WHERE cr.EstActif = 1
    AND cr.Role IN ('TITULAIRE_PRINCIPAL', 'MANDATAIRE', 'OBSERVATEUR');
GO

-- ============================================================================
-- VUE 6 : HISTORIQUE TRANSACTIONS - Complet avec filtres
-- ============================================================================

CREATE OR ALTER VIEW vw_HistoriqueTransactions AS
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
    
    -- Souscription liée (si applicable)
    s.SouscriptionID,
    i.Code AS CodeInstrument,
    i.Nom AS NomInstrument,
    
    -- Date effective pour tri
    ISNULL(t.DateExecution, t.DateCreation) AS DateEffective

FROM ComptesRoles cr
INNER JOIN Comptes cptClient ON cr.CompteID = cptClient.CompteID
LEFT JOIN Transactions t ON (t.CompteSource = cptClient.CompteID OR t.CompteDestination = cptClient.CompteID)
LEFT JOIN Comptes cptSrc ON t.CompteSource = cptSrc.CompteID
LEFT JOIN Comptes cptDest ON t.CompteDestination = cptDest.CompteID
LEFT JOIN Souscriptions s ON t.SouscriptionID = s.SouscriptionID
LEFT JOIN Instruments i ON s.InstrumentID = i.InstrumentID
WHERE cr.EstActif = 1
    AND cr.Role IN ('TITULAIRE_PRINCIPAL', 'MANDATAIRE', 'OBSERVATEUR', 'ADMINISTRATEUR');
GO

-- ============================================================================
-- VUE 7 : PROFIL KYC CLIENT - Informations personnelles
-- ============================================================================

CREATE OR ALTER VIEW vw_ProfilClient AS
SELECT 
    c.ClientID,
    c.ClientType,
    c.ProfilRisque,
    c.StatutClient,
    c.DateCreation,
    
    -- CLIENT INDIVIDUEL
    ci.Prenom,
    ci.Nom,
    CONCAT(ci.Prenom, ' ', ci.Nom) AS NomComplet,
    ci.DateNaissance,
    ci.Nationalite,
    ci.TypePieceIdentite,
    ci.NumeroPieceIdentite,
    ci.Profession,
    ci.RevenuAnnuelEstime,
    
    -- CLIENT INSTITUTIONNEL
    cin.NomEntreprise,
    cin.NumeroRegistreCommerce,
    cin.FormeJuridique,
    cin.Secteur,
    cin.DateCreationEntreprise,
    cin.ChiffreAffairesAnnuel,
    cin.NomRepresentantLegal,
    
    -- ADRESSE PRINCIPALE
    adr.AdresseLigne1,
    adr.AdresseLigne2,
    adr.Ville,
    adr.CodePostal,
    adr.Pays,
    CONCAT(adr.AdresseLigne1, 
           CASE WHEN adr.AdresseLigne2 IS NOT NULL THEN ', ' + adr.AdresseLigne2 ELSE '' END,
           ', ', adr.CodePostal, ' ', adr.Ville, ', ', adr.Pays) AS AdresseComplete,
    
    -- CONTACT PRINCIPAL EMAIL
    ctEmail.Valeur AS Email,
    
    -- CONTACT PRINCIPAL TÉLÉPHONE
    ctTel.Valeur AS Telephone,
    
    -- AUTHENTIFICATION
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
LEFT JOIN ClientsAuthentification auth ON c.ClientID = auth.ClientID;
GO

-- ============================================================================
-- VUE 8 : LISTE DES COMPTES ACCESSIBLES PAR CLIENT
-- (Pour le sélecteur de compte en haut à droite)
-- ============================================================================

CREATE OR ALTER VIEW vw_ComptesAccessibles AS
SELECT 
    cr.ClientID,
    cr.CompteID,
    cr.Role,
    cpt.NumeroCompte,
    cpt.TypeCompte,
    cpt.Devise,
    
    -- Nom/Label du compte pour affichage
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
    
    -- Est-ce le compte personnel du client ?
    CASE WHEN cr.Role = 'TITULAIRE_PRINCIPAL' THEN 1 ELSE 0 END AS EstComptePersonnel

FROM ComptesRoles cr
INNER JOIN Comptes cpt ON cr.CompteID = cpt.CompteID
LEFT JOIN ComptesRoles crTit ON cpt.CompteID = crTit.CompteID 
    AND crTit.Role = 'TITULAIRE_PRINCIPAL' AND crTit.EstActif = 1
LEFT JOIN Clients cTit ON crTit.ClientID = cTit.ClientID
LEFT JOIN ClientsIndividuels ciTit ON cTit.ClientID = ciTit.ClientID
LEFT JOIN ClientsInstitutionnels cinTit ON cTit.ClientID = cinTit.ClientID
WHERE cr.EstActif = 1 
    AND cpt.StatutCompte = 'ACTIF';
GO

-- ============================================================================
-- VUE 9 : STATISTIQUES MENSUELLES (Pour le graphique dashboard)
-- ============================================================================

CREATE OR ALTER VIEW vw_StatistiquesMensuelles AS
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
    
    -- Valeur du portefeuille ce mois-là
    ISNULL(SUM(s.ValeurActuelle), 0) AS ValeurPortefeuille,
    
    -- Nombre de souscriptions actives ce mois
    COUNT(s.SouscriptionID) AS NombreSouscriptions

FROM MoisRecents m
CROSS JOIN ComptesRoles cr
INNER JOIN Comptes cpt ON cr.CompteID = cpt.CompteID
LEFT JOIN Souscriptions s ON cpt.CompteID = s.CompteID 
    AND s.DateSouscription <= EOMONTH(m.DateMois)
    AND (s.DateMaturiteEffective >= m.DateMois OR s.DateMaturiteEffective IS NULL)
    AND s.StatutSouscription = 'ACTIVE'
WHERE cr.EstActif = 1
    AND cr.Role IN ('TITULAIRE_PRINCIPAL', 'MANDATAIRE')
GROUP BY cr.ClientID, cr.CompteID, m.DateMois;
GO

-- ============================================================================
-- VUE 10 : PAIEMENTS D'INTÉRÊTS À VENIR (Pour notifications)
-- ============================================================================

CREATE OR ALTER VIEW vw_ProchainsInterets AS
SELECT 
    cr.ClientID,
    cr.CompteID,
    s.SouscriptionID,
    i.Nom AS NomInstrument,
    i.Code AS CodeInstrument,
    pi.DatePaiement,
    pi.MontantInteret,
    pi.StatutPaiement,
    
    -- Jours avant paiement
    DATEDIFF(DAY, GETDATE(), pi.DatePaiement) AS JoursAvantPaiement

FROM ComptesRoles cr
INNER JOIN Comptes cpt ON cr.CompteID = cpt.CompteID
INNER JOIN Souscriptions s ON cpt.CompteID = s.CompteID
INNER JOIN Instruments i ON s.InstrumentID = i.InstrumentID
INNER JOIN PaiementsInterets pi ON s.SouscriptionID = pi.SouscriptionID
WHERE cr.EstActif = 1
    AND s.StatutSouscription = 'ACTIVE'
    AND pi.StatutPaiement IN ('PLANIFIE', 'EN_ATTENTE')
    AND pi.DatePaiement >= GETDATE()
    AND cr.Role IN ('TITULAIRE_PRINCIPAL', 'MANDATAIRE', 'OBSERVATEUR');
GO

-- ============================================================================
-- INDEX POUR OPTIMISATION DES VUES
-- ============================================================================

PRINT 'Création des index pour optimisation...';
GO

-- Index sur ComptesRoles pour filtrage rapide
IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_ComptesRoles_ClientID_EstActif' AND object_id = OBJECT_ID('ComptesRoles'))
    CREATE INDEX IX_ComptesRoles_ClientID_EstActif ON ComptesRoles(ClientID, EstActif) INCLUDE (CompteID, Role);

-- Index sur Souscriptions pour recherches fréquentes
IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_Souscriptions_CompteID_Statut' AND object_id = OBJECT_ID('Souscriptions'))
    CREATE INDEX IX_Souscriptions_CompteID_Statut ON Souscriptions(CompteID, StatutSouscription) 
    INCLUDE (MontantInvesti, ValeurActuelle, InteretsAccumules, TMA_Reel);

-- Index sur Transactions pour historique
IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_Transactions_Comptes_Date' AND object_id = OBJECT_ID('Transactions'))
    CREATE INDEX IX_Transactions_Comptes_Date ON Transactions(CompteSource, CompteDestination, DateCreation DESC);

PRINT '✓ Index créés';
GO

-- ============================================================================
-- RÉSUMÉ DES VUES CRÉÉES
-- ============================================================================

PRINT '';
PRINT '=================================================================';
PRINT 'VUES CRÉÉES AVEC SUCCÈS POUR LE PORTAIL CLIENT!';
PRINT '=================================================================';
PRINT '';
PRINT 'Dashboard (3 vues):';
PRINT '  ✓ vw_Dashboard_Overview';
PRINT '  ✓ vw_Dashboard_DernieresTransactions';
PRINT '  ✓ vw_Dashboard_InvestissementsActifs';
PRINT '';
PRINT 'Comptes:';
PRINT '  ✓ vw_MesComptes';
PRINT '  ✓ vw_ComptesAccessibles (pour sélecteur)';
PRINT '';
PRINT 'Investissements:';
PRINT '  ✓ vw_MesInvestissements';
PRINT '  ✓ vw_ProchainsInterets';
PRINT '';
PRINT 'Transactions:';
PRINT '  ✓ vw_HistoriqueTransactions';
PRINT '';
PRINT 'Profil:';
PRINT '  ✓ vw_ProfilClient';
PRINT '';
PRINT 'Analytics:';
PRINT '  ✓ vw_StatistiquesMensuelles (graphique)';
PRINT '';
PRINT '=================================================================';
GO