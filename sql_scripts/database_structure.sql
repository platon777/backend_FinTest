-- ============================================================================
-- BASE DE DONNÉES - SYSTÈME DE GESTION DE PORTEFEUILLE CLIENTS
-- Version simplifiée : UNIQUEMENT DES CLIENTS
-- ============================================================================
--
-- Les CLIENTS sont les utilisateurs qui:
--   - Se connectent au portail web
--   - Voient leurs comptes, obligations, transactions
--   - Gèrent leurs investissements
--
-- Il n'y a PAS d'employés/back-office dans cette version
-- ============================================================================

USE Db_test;
GO

-- ============================================================================
-- 1. CLIENTS (Les utilisateurs du système)
-- ============================================================================

-- Table parent pour tous les clients
CREATE TABLE Clients (
    ClientID INT PRIMARY KEY IDENTITY(1,1),
    ClientType VARCHAR(20) CHECK (ClientType IN ('INDIVIDUEL', 'INSTITUTIONNEL')),
    ProfilRisque VARCHAR(20) CHECK (ProfilRisque IN ('CONSERVATEUR', 'MODERE', 'AGRESSIF')),
    StatutClient VARCHAR(20) CHECK (StatutClient IN ('ACTIF', 'SUSPENDU', 'FERME')) DEFAULT 'ACTIF',
    DateCreation DATETIME DEFAULT GETDATE(),
    DerniereMiseAJour DATETIME DEFAULT GETDATE()
);

-- Clients individuels (personnes physiques)
CREATE TABLE ClientsIndividuels (
    ClientID INT PRIMARY KEY,
    Prenom NVARCHAR(100) NOT NULL,
    Nom NVARCHAR(100) NOT NULL,
    DateNaissance DATE NOT NULL,
    LieuNaissance NVARCHAR(200),
    Nationalite NVARCHAR(50),
    TypePieceIdentite VARCHAR(50),
    NumeroPieceIdentite NVARCHAR(100) UNIQUE NOT NULL,
    DateExpirationPiece DATE,
    SituationMatrimoniale VARCHAR(20),
    Profession NVARCHAR(200),
    SourceRevenus NVARCHAR(500),
    RevenuAnnuelEstime DECIMAL(18,2),
    CONSTRAINT FK_ClientsIndiv_Clients FOREIGN KEY (ClientID) REFERENCES Clients(ClientID)
);

-- Clients institutionnels (personnes morales)
CREATE TABLE ClientsInstitutionnels (
    ClientID INT PRIMARY KEY,
    NomEntreprise NVARCHAR(200) NOT NULL,
    NumeroRegistreCommerce NVARCHAR(100) UNIQUE NOT NULL,
    FormeJuridique VARCHAR(50),
    Secteur NVARCHAR(200),
    DateCreationEntreprise DATE,
    ChiffreAffairesAnnuel DECIMAL(18,2),
    NomRepresentantLegal NVARCHAR(200),
    FonctionRepresentant NVARCHAR(100),
    CONSTRAINT FK_ClientsInst_Clients FOREIGN KEY (ClientID) REFERENCES Clients(ClientID)
);

-- Adresses des clients
CREATE TABLE AdressesClients (
    AdresseID INT PRIMARY KEY IDENTITY(1,1),
    ClientID INT NOT NULL,
    TypeAdresse VARCHAR(20) CHECK (TypeAdresse IN ('DOMICILE', 'PROFESSIONNELLE', 'POSTALE')),
    AdresseLigne1 NVARCHAR(200),
    AdresseLigne2 NVARCHAR(200),
    Ville NVARCHAR(100),
    CodePostal NVARCHAR(20),
    Pays NVARCHAR(100),
    EstPrincipale BIT DEFAULT 0,
    CONSTRAINT FK_Adresses_Clients FOREIGN KEY (ClientID) REFERENCES Clients(ClientID)
);

-- Contacts des clients
CREATE TABLE ContactsClients (
    ContactID INT PRIMARY KEY IDENTITY(1,1),
    ClientID INT NOT NULL,
    TypeContact VARCHAR(20) CHECK (TypeContact IN ('EMAIL', 'TELEPHONE', 'MOBILE')),
    Valeur NVARCHAR(200) NOT NULL,
    EstPrincipal BIT DEFAULT 0,
    EstVerifie BIT DEFAULT 0,
    CONSTRAINT FK_Contacts_Clients FOREIGN KEY (ClientID) REFERENCES Clients(ClientID)
);

-- ============================================================================
-- 2. AUTHENTIFICATION CLIENTS
-- ============================================================================

-- Authentification pour que les clients se connectent
CREATE TABLE ClientsAuthentification (
    AuthID INT PRIMARY KEY IDENTITY(1,1),
    ClientID INT NOT NULL UNIQUE,
    Email NVARCHAR(200) UNIQUE NOT NULL,
    PasswordHash NVARCHAR(255) NOT NULL,
    EstActif BIT DEFAULT 1,
    DateCreation DATETIME DEFAULT GETDATE(),
    DateDerniereConnexion DATETIME NULL,
    CONSTRAINT FK_ClientsAuth_Clients FOREIGN KEY (ClientID) REFERENCES Clients(ClientID) ON DELETE CASCADE
);

CREATE INDEX IX_ClientsAuth_Email ON ClientsAuthentification(Email);
CREATE INDEX IX_ClientsAuth_ClientID ON ClientsAuthentification(ClientID);

-- Refresh tokens pour les sessions
CREATE TABLE RefreshTokens (
    TokenID INT PRIMARY KEY IDENTITY(1,1),
    ClientID INT NOT NULL,
    Token NVARCHAR(500) UNIQUE NOT NULL,
    DateCreation DATETIME DEFAULT GETDATE(),
    DateExpiration DATETIME NOT NULL,
    EstRevoque BIT DEFAULT 0,
    AdresseIP NVARCHAR(50),
    CONSTRAINT FK_RefreshTokens_Clients FOREIGN KEY (ClientID) REFERENCES Clients(ClientID) ON DELETE CASCADE
);

CREATE INDEX IX_RefreshTokens_ClientID ON RefreshTokens(ClientID);
CREATE INDEX IX_RefreshTokens_Token ON RefreshTokens(Token);

-- ============================================================================
-- 3. COMPTES D'INVESTISSEMENT
-- ============================================================================

CREATE TABLE Comptes (
    CompteID INT PRIMARY KEY IDENTITY(1,1),
    NumeroCompte NVARCHAR(50) UNIQUE NOT NULL,
    TypeCompte VARCHAR(30) CHECK (TypeCompte IN ('INVESTISSEMENT', 'CASH', 'EPARGNE')),
    Devise VARCHAR(3) DEFAULT 'HTG',
    Solde DECIMAL(18,2) DEFAULT 0,
    SoldeDisponible DECIMAL(18,2) DEFAULT 0,
    DateOuverture DATETIME DEFAULT GETDATE(),
    DateFermeture DATETIME NULL,
    StatutCompte VARCHAR(20) CHECK (StatutCompte IN ('ACTIF', 'SUSPENDU', 'FERME')) DEFAULT 'ACTIF',
    CONSTRAINT CHK_Solde CHECK (Solde >= 0)
);

-- Relation Client <-> Compte
CREATE TABLE ComptesRoles (
    CompteRoleID INT PRIMARY KEY IDENTITY(1,1),
    CompteID INT NOT NULL,
    ClientID INT NOT NULL,
    Role VARCHAR(30) CHECK (Role IN (
        'TITULAIRE_PRINCIPAL',
        'TITULAIRE_SECONDAIRE',
        'MANDATAIRE',
        'OBSERVATEUR',
        'ADMINISTRATEUR',
        'BENEFICIAIRE'
    )),
    DateDebut DATETIME DEFAULT GETDATE(),
    DateFin DATETIME NULL,
    EstActif BIT DEFAULT 1,
    CONSTRAINT FK_ComptesRoles_Comptes FOREIGN KEY (CompteID) REFERENCES Comptes(CompteID),
    CONSTRAINT FK_ComptesRoles_Clients FOREIGN KEY (ClientID) REFERENCES Clients(ClientID),
    CONSTRAINT UQ_CompteClient_Role UNIQUE (CompteID, ClientID, Role)
);

-- ============================================================================
-- 4. INSTRUMENTS FINANCIERS
-- ============================================================================

-- Types d'instruments
CREATE TABLE TypesInstruments (
    TypeInstrumentID INT PRIMARY KEY IDENTITY(1,1),
    Code VARCHAR(50) UNIQUE NOT NULL,
    Nom NVARCHAR(200),
    Description NVARCHAR(MAX)
);

-- Instruments spécifiques
CREATE TABLE Instruments (
    InstrumentID INT PRIMARY KEY IDENTITY(1,1),
    TypeInstrumentID INT NOT NULL,
    Code NVARCHAR(50) UNIQUE NOT NULL,
    Nom NVARCHAR(200) NOT NULL,
    Description NVARCHAR(MAX),
    Emetteur NVARCHAR(200),
    TauxRendementAnnuel DECIMAL(5,2),
    DateEmission DATE,
    DateMaturite DATE,
    ValeurNominale DECIMAL(18,2),
    MontantMinimum DECIMAL(18,2),
    Devise VARCHAR(3),
    FrequencePaiementInterets VARCHAR(20),
    StatutInstrument VARCHAR(20) CHECK (StatutInstrument IN ('DISPONIBLE', 'EPUISE', 'EXPIRE')) DEFAULT 'DISPONIBLE',
    CONSTRAINT FK_Instruments_Types FOREIGN KEY (TypeInstrumentID) REFERENCES TypesInstruments(TypeInstrumentID)
);

-- ============================================================================
-- 5. SOUSCRIPTIONS (Investissements)
-- ============================================================================

CREATE TABLE Souscriptions (
    SouscriptionID INT PRIMARY KEY IDENTITY(1,1),
    CompteID INT NOT NULL,
    InstrumentID INT NOT NULL,
    MontantInvesti DECIMAL(18,2) NOT NULL,
    NombreUnites DECIMAL(18,6),
    DateSouscription DATETIME DEFAULT GETDATE(),
    DateMaturiteEffective DATE,
    TauxSouscription DECIMAL(5,2),
    ValeurActuelle DECIMAL(18,2),
    InteretsAccumules DECIMAL(18,2) DEFAULT 0,
    StatutSouscription VARCHAR(20) CHECK (StatutSouscription IN ('ACTIVE', 'MATURE', 'RACHETEE')) DEFAULT 'ACTIVE',
    CONSTRAINT FK_Souscriptions_Comptes FOREIGN KEY (CompteID) REFERENCES Comptes(CompteID),
    CONSTRAINT FK_Souscriptions_Instruments FOREIGN KEY (InstrumentID) REFERENCES Instruments(InstrumentID)
);

-- Paiements d'intérêts
CREATE TABLE PaiementsInterets (
    PaiementID INT PRIMARY KEY IDENTITY(1,1),
    SouscriptionID INT NOT NULL,
    DatePaiement DATETIME,
    MontantInteret DECIMAL(18,2),
    StatutPaiement VARCHAR(20) CHECK (StatutPaiement IN ('PLANIFIE', 'EXECUTE', 'ECHOUE')),
    TransactionID INT,
    CONSTRAINT FK_Paiements_Souscriptions FOREIGN KEY (SouscriptionID) REFERENCES Souscriptions(SouscriptionID)
);

-- ============================================================================
-- 6. TRANSACTIONS
-- ============================================================================

CREATE TABLE Transactions (
    TransactionID INT PRIMARY KEY IDENTITY(1,1),
    TypeTransaction VARCHAR(50) CHECK (TypeTransaction IN (
        'DEPOT',
        'RETRAIT',
        'SOUSCRIPTION',
        'RACHAT',
        'PAIEMENT_INTERET',
        'REMBOURSEMENT_MATURITE',
        'TRANSFERT'
    )),
    CompteSource INT,
    CompteDestination INT,
    Montant DECIMAL(18,2) NOT NULL,
    Devise VARCHAR(3) NOT NULL,
    Description NVARCHAR(MAX),
    StatutTransaction VARCHAR(30) CHECK (StatutTransaction IN (
        'EN_ATTENTE',
        'EXECUTEE',
        'ECHOUEE',
        'ANNULEE'
    )) DEFAULT 'EN_ATTENTE',
    DateCreation DATETIME DEFAULT GETDATE(),
    DateExecution DATETIME,
    EstAutomatique BIT DEFAULT 0,
    SouscriptionID INT,
    CONSTRAINT FK_Trans_CompteSource FOREIGN KEY (CompteSource) REFERENCES Comptes(CompteID),
    CONSTRAINT FK_Trans_CompteDestination FOREIGN KEY (CompteDestination) REFERENCES Comptes(CompteID)
);

-- ============================================================================
-- DONNÉES INITIALES
-- ============================================================================

-- Types d'instruments
INSERT INTO TypesInstruments (Code, Nom, Description)
VALUES
    ('OBL', 'Obligation', 'Titre de créance à taux fixe'),
    ('ACTION', 'Action', 'Part de propriété dans une entreprise'),
    ('FONDS', 'Fonds Commun', 'Portefeuille diversifié géré professionnellement'),
    ('DEPOT', 'Dépôt à Terme', 'Dépôt avec taux fixe et échéance définie');

-- Exemple d'instruments disponibles
INSERT INTO Instruments (TypeInstrumentID, Code, Nom, Emetteur, TauxRendementAnnuel, DateEmission, DateMaturite, ValeurNominale, MontantMinimum, Devise, FrequencePaiementInterets, StatutInstrument)
VALUES
    (1, 'OBL-BRH-2025', 'Obligation BRH 5% 2025-2030', 'Banque de la République d''Haïti', 5.00, '2025-01-01', '2030-01-01', 1000.00, 5000.00, 'HTG', 'TRIMESTRIEL', 'DISPONIBLE'),
    (1, 'OBL-EDH-2025', 'Obligation EDH 6% 2025-2028', 'Électricité d''Haïti', 6.00, '2025-01-01', '2028-01-01', 1000.00, 3000.00, 'HTG', 'SEMESTRIEL', 'DISPONIBLE'),
    (4, 'DEPOT-12M', 'Dépôt à terme 12 mois', 'Banque', 4.50, '2025-01-01', '2026-01-01', 1.00, 10000.00, 'HTG', 'A_MATURITE', 'DISPONIBLE');

GO

PRINT '=================================================================';
PRINT 'Base de données créée avec succès!';
PRINT '';
PRINT 'Structure simplifiée:';
PRINT '- Clients (utilisateurs du système)';
PRINT '- ClientsAuthentification (login portail web)';
PRINT '- Comptes (comptes d''investissement)';
PRINT '- Instruments (obligations, actions, etc.)';
PRINT '- Souscriptions (investissements des clients)';
PRINT '- Transactions (dépôts, retraits, etc.)';
PRINT '';
PRINT 'Les clients peuvent:';
PRINT '  1. S''inscrire et se connecter';
PRINT '  2. Voir leurs comptes';
PRINT '  3. Voir leurs investissements';
PRINT '  4. Voir leurs transactions';
PRINT '=================================================================';
GO





-- Plan comptable simplifié
CREATE TABLE PlanComptable (
    CompteComptableID INT PRIMARY KEY IDENTITY(1,1),
    NumeroCompte NVARCHAR(20) UNIQUE NOT NULL,
    NomCompte NVARCHAR(200) NOT NULL,
    TypeCompte VARCHAR(20) CHECK (TypeCompte IN ('ACTIF', 'PASSIF', 'PRODUIT', 'CHARGE', 'CAPITAUX')),
    EstDebit BIT NOT NULL, -- 1 si nature débitrice, 0 si créditrice
    Description NVARCHAR(500)
);

-- Écritures comptables générées par transactions
CREATE TABLE EcrituresComptables (
    EcritureID INT PRIMARY KEY IDENTITY(1,1),
    TransactionID INT NOT NULL,
    NumeroEcriture NVARCHAR(50) UNIQUE NOT NULL,
    DateEcriture DATETIME DEFAULT GETDATE(),
    Description NVARCHAR(MAX),
    EstEquilibree BIT DEFAULT 0, -- Total Débit = Total Crédit ?
    CONSTRAINT FK_Ecritures_Transactions FOREIGN KEY (TransactionID) REFERENCES Transactions(TransactionID)
);

-- Lignes d'écriture (minimum 2 par écriture: débit + crédit)
CREATE TABLE LignesEcriture (
    LigneEcritureID INT PRIMARY KEY IDENTITY(1,1),
    EcritureID INT NOT NULL,
    CompteComptableID INT NOT NULL,
    TypeMouvement VARCHAR(10) CHECK (TypeMouvement IN ('DEBIT', 'CREDIT')),
    Montant DECIMAL(18,2) NOT NULL,
    Description NVARCHAR(500),
    CONSTRAINT FK_Lignes_Ecritures FOREIGN KEY (EcritureID) REFERENCES EcrituresComptables(EcritureID),
    CONSTRAINT FK_Lignes_Plan FOREIGN KEY (CompteComptableID) REFERENCES PlanComptable(CompteComptableID)
);

-- Index pour performance
CREATE INDEX IX_Ecritures_TransactionID ON EcrituresComptables(TransactionID);
CREATE INDEX IX_Lignes_EcritureID ON LignesEcriture(EcritureID);
CREATE INDEX IX_Lignes_CompteComptableID ON LignesEcriture(CompteComptableID);

PRINT '✓ Module Comptabilité créé';
GO

-- ============================================================================
-- MODULE 2 : AUDIT & CONFORMITÉ
-- ============================================================================

PRINT 'Création Module Audit...';
GO

-- Journal d'audit (TOUT ce qui se passe dans le système)
CREATE TABLE JournalAudit (
    AuditID BIGINT PRIMARY KEY IDENTITY(1,1),
    DateAction DATETIME DEFAULT GETDATE(),
    ClientID INT NULL, -- Qui a fait l'action (NULL si système)
    TypeAction VARCHAR(50) NOT NULL, -- INSERT, UPDATE, DELETE, LOGIN, LOGOUT, VIEW
    TableCiblee NVARCHAR(100),
    EnregistrementID INT,
    AncienneValeur NVARCHAR(MAX), -- JSON de l'état avant
    NouvelleValeur NVARCHAR(MAX), -- JSON de l'état après
    AdresseIP NVARCHAR(50),
    UserAgent NVARCHAR(500),
    CONSTRAINT FK_Audit_Clients FOREIGN KEY (ClientID) REFERENCES Clients(ClientID)
);

-- Vérifications de conformité
CREATE TABLE VerificationsConformite (
    VerificationID INT PRIMARY KEY IDENTITY(1,1),
    ClientID INT NOT NULL,
    TypeVerification VARCHAR(50) NOT NULL, -- KYC, AML, SANCTIONS, RISQUE
    DateVerification DATETIME DEFAULT GETDATE(),
    Resultat VARCHAR(20) CHECK (Resultat IN ('CONFORME', 'NON_CONFORME', 'EN_ATTENTE', 'ENQUETE')),
    Score DECIMAL(5,2), -- Score de risque 0-100
    Commentaires NVARCHAR(MAX),
    DocumentsJoints NVARCHAR(MAX), -- URLs/chemins des documents
    CONSTRAINT FK_Verif_Clients FOREIGN KEY (ClientID) REFERENCES Clients(ClientID)
);

-- Index pour performance
CREATE INDEX IX_Audit_DateAction ON JournalAudit(DateAction);
CREATE INDEX IX_Audit_ClientID ON JournalAudit(ClientID);
CREATE INDEX IX_Audit_TypeAction ON JournalAudit(TypeAction);
CREATE INDEX IX_Verif_ClientID ON VerificationsConformite(ClientID);
CREATE INDEX IX_Verif_DateVerification ON VerificationsConformite(DateVerification);

PRINT '✓ Module Audit créé';
GO

-- ============================================================================
-- MODULE 3 : SYNCHRONISATION INTER-SYSTÈMES (n8n)
-- ============================================================================

PRINT 'Création Module Synchronisation...';
GO

-- Systèmes externes configurés
CREATE TABLE SystemesExternes (
    SystemeID INT PRIMARY KEY IDENTITY(1,1),
    CodeSysteme VARCHAR(50) UNIQUE NOT NULL, -- CRM, BACKOFFICE, AUDIT, REPORTING
    NomSysteme NVARCHAR(200) NOT NULL,
    Description NVARCHAR(500),
    URLEndpoint NVARCHAR(500), -- URL webhook pour notifier le système
    TypeConnexion VARCHAR(20) CHECK (TypeConnexion IN ('HTTP', 'HTTPS', 'VPN')),
    EstActif BIT DEFAULT 1,
    TokenAuthentification NVARCHAR(500), -- API Key ou JWT
    TimeoutSecondes INT DEFAULT 30,
    MaxRetries INT DEFAULT 3,
    DateCreation DATETIME DEFAULT GETDATE(),
    DerniereMiseAJour DATETIME DEFAULT GETDATE()
);

-- Événements à synchroniser
CREATE TABLE EvenementsSync (
    EvenementID BIGINT PRIMARY KEY IDENTITY(1,1),
    TypeEvenement VARCHAR(50) NOT NULL, -- ORDER_CREATED, TRANSACTION_UPDATED, CLIENT_UPDATED, etc.
    EntityType VARCHAR(50), -- Transactions, Clients, Souscriptions, etc.
    EntityID INT NOT NULL, -- ID de l'entité concernée
    Payload NVARCHAR(MAX) NOT NULL, -- JSON des données complètes
    DateCreation DATETIME DEFAULT GETDATE(),
    StatutGlobal VARCHAR(20) CHECK (StatutGlobal IN ('PENDING', 'PROCESSING', 'COMPLETED', 'FAILED')) DEFAULT 'PENDING',
    NombreSystemesCibles INT DEFAULT 0, -- Combien de systèmes doivent recevoir
    NombreSystemesReussis INT DEFAULT 0 -- Combien ont reçu avec succès
);

-- Logs détaillés de synchronisation
CREATE TABLE LogsSynchronisation (
    LogID BIGINT PRIMARY KEY IDENTITY(1,1),
    EvenementID BIGINT NOT NULL,
    SystemeID INT NOT NULL,
    StatutEnvoi VARCHAR(20) CHECK (StatutEnvoi IN ('SUCCESS', 'FAILED', 'RETRY', 'TIMEOUT')) NOT NULL,
    DateEnvoi DATETIME DEFAULT GETDATE(),
    DateReponse DATETIME,
    CodeHTTP INT, -- Code réponse HTTP (200, 404, 500, etc.)
    MessageErreur NVARCHAR(MAX),
    ReponseSysteme NVARCHAR(MAX), -- JSON de la réponse
    NombreTentatives INT DEFAULT 1,
    DureeMS INT, -- Durée en millisecondes
    CONSTRAINT FK_Logs_Evenements FOREIGN KEY (EvenementID) REFERENCES EvenementsSync(EvenementID),
    CONSTRAINT FK_Logs_Systemes FOREIGN KEY (SystemeID) REFERENCES SystemesExternes(SystemeID)
);

-- Index pour performance et monitoring
CREATE INDEX IX_Evenements_StatutGlobal ON EvenementsSync(StatutGlobal);
CREATE INDEX IX_Evenements_DateCreation ON EvenementsSync(DateCreation);
CREATE INDEX IX_Evenements_TypeEvenement ON EvenementsSync(TypeEvenement);
CREATE INDEX IX_Logs_EvenementID ON LogsSynchronisation(EvenementID);
CREATE INDEX IX_Logs_SystemeID ON LogsSynchronisation(SystemeID);
CREATE INDEX IX_Logs_StatutEnvoi ON LogsSynchronisation(StatutEnvoi);
CREATE INDEX IX_Logs_DateEnvoi ON LogsSynchronisation(DateEnvoi);

PRINT '✓ Module Synchronisation créé';
GO

-- ============================================================================
-- MODULE 4 : AMÉLIORATIONS TABLES EXISTANTES
-- ============================================================================

PRINT 'Ajout colonnes manquantes...';
GO

-- Ajouter TMA_Reel dans Souscriptions
IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('Souscriptions') AND name = 'TMA_Reel')
BEGIN
    ALTER TABLE Souscriptions ADD TMA_Reel DECIMAL(10,6) NULL;
    PRINT '✓ Colonne TMA_Reel ajoutée à Souscriptions';
END
GO

-- Ajouter CreePar dans Transactions (référence au client qui a créé)
IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('Transactions') AND name = 'CreePar')
BEGIN
    ALTER TABLE Transactions ADD CreePar INT NULL;
    ALTER TABLE Transactions ADD CONSTRAINT FK_Trans_CreePar FOREIGN KEY (CreePar) REFERENCES Clients(ClientID);
    PRINT '✓ Colonne CreePar ajoutée à Transactions';
END
GO

-- Ajouter commentaires dans Transactions
IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('Transactions') AND name = 'Commentaires')
BEGIN
    ALTER TABLE Transactions ADD Commentaires NVARCHAR(MAX) NULL;
    PRINT '✓ Colonne Commentaires ajoutée à Transactions';
END
GO

-- ============================================================================
-- DONNÉES INITIALES - PLAN COMPTABLE DE BASE
-- ============================================================================

PRINT 'Insertion plan comptable de base...';
GO

-- Plan comptable simplifié haïtien
INSERT INTO PlanComptable (NumeroCompte, NomCompte, TypeCompte, EstDebit, Description) VALUES
-- ACTIFS (Débits)
('5101', 'Caisse - Espèces HTG', 'ACTIF', 1, 'Argent liquide en gourdes'),
('5102', 'Caisse - Espèces USD', 'ACTIF', 1, 'Argent liquide en dollars'),
('5110', 'Banque - Compte Courant', 'ACTIF', 1, 'Compte bancaire principal'),
('5120', 'Placements Court Terme', 'ACTIF', 1, 'Obligations et placements'),

-- PASSIFS (Crédits)
('2100', 'Dépôts Clientèle', 'PASSIF', 0, 'Argent dû aux clients'),
('2110', 'Comptes Investissement Clients', 'PASSIF', 0, 'Soldes investissements clients'),

-- PRODUITS (Crédits)
('7100', 'Intérêts Reçus', 'PRODUIT', 0, 'Revenus d''intérêts'),
('7110', 'Commissions Gestion', 'PRODUIT', 0, 'Frais de gestion'),

-- CHARGES (Débits)
('6100', 'Intérêts Versés', 'CHARGE', 1, 'Intérêts payés aux clients'),
('6110', 'Frais Bancaires', 'CHARGE', 1, 'Frais et commissions bancaires');

PRINT '✓ Plan comptable initialisé';
GO

-- ============================================================================
-- DONNÉES INITIALES - SYSTÈMES EXTERNES
-- ============================================================================

PRINT 'Configuration systèmes externes (exemples)...';
GO

INSERT INTO SystemesExternes (CodeSysteme, NomSysteme, Description, URLEndpoint, TypeConnexion, EstActif, TimeoutSecondes, MaxRetries) VALUES
('CRM', 'CRM Conseillers', 'Système CRM des conseillers en placement', 'https://crm.advisor.example.ht/api/webhook', 'HTTPS', 0, 30, 3),
('BACKOFFICE', 'Back-Office Interne', 'Système de traitement back-office', 'http://10.0.0.100/api/webhook', 'HTTP', 1, 30, 3),
('AUDIT', 'Système Audit Externe', 'Plateforme audit et conformité', 'https://audit.compliance.example.com/api/webhook', 'HTTPS', 0, 45, 5),
('REPORTING', 'Système Reporting', 'Plateforme analytics et dashboards', 'http://10.0.0.110/api/webhook', 'HTTP', 1, 20, 3);

PRINT '✓ Systèmes externes configurés (désactivés par défaut)';
GO

-- ============================================================================
-- PROCÉDURES STOCKÉES UTILES
-- ============================================================================

PRINT 'Création procédures stockées...';
GO

-- Procédure : Calculer TMA approximatif
CREATE OR ALTER PROCEDURE sp_CalculerTMA
    @SouscriptionID INT
AS
BEGIN
    DECLARE @PrixAchat DECIMAL(18,2);
    DECLARE @ValeurNominale DECIMAL(18,2);
    DECLARE @TauxCoupon DECIMAL(5,2);
    DECLARE @DureeAnnees INT;
    DECLARE @TMA DECIMAL(10,6);

    -- Récupérer les données
    SELECT 
        @PrixAchat = s.MontantInvesti,
        @ValeurNominale = s.MontantInvesti, -- Simplifié
        @TauxCoupon = i.TauxRendementAnnuel,
        @DureeAnnees = DATEDIFF(YEAR, s.DateSouscription, s.DateMaturiteEffective)
    FROM Souscriptions s
    INNER JOIN Instruments i ON s.InstrumentID = i.InstrumentID
    WHERE s.SouscriptionID = @SouscriptionID;

    -- Calcul approximatif du TMA
    IF @PrixAchat > 0 AND @DureeAnnees > 0
    BEGIN
        -- Formule simplifiée
        SET @TMA = ((@TauxCoupon + ((@ValeurNominale - @PrixAchat) / @DureeAnnees)) / 
                   ((@ValeurNominale + @PrixAchat) / 2)) * 100;
        
        -- Mettre à jour
        UPDATE Souscriptions SET TMA_Reel = @TMA WHERE SouscriptionID = @SouscriptionID;
        
        SELECT @TMA AS TMA_Calcule;
    END
END;
GO

-- Procédure : Créer événement de synchronisation
CREATE OR ALTER PROCEDURE sp_CreerEvenementSync
    @TypeEvenement VARCHAR(50),
    @EntityType VARCHAR(50),
    @EntityID INT,
    @Payload NVARCHAR(MAX)
AS
BEGIN
    DECLARE @EvenementID BIGINT;
    DECLARE @NbSystemes INT;

    -- Compter systèmes actifs
    SELECT @NbSystemes = COUNT(*) FROM SystemesExternes WHERE EstActif = 1;

    -- Créer événement
    INSERT INTO EvenementsSync (TypeEvenement, EntityType, EntityID, Payload, NombreSystemesCibles)
    VALUES (@TypeEvenement, @EntityType, @EntityID, @Payload, @NbSystemes);

    SET @EvenementID = SCOPE_IDENTITY();

    -- Retourner l'ID
    SELECT @EvenementID AS EvenementID, @NbSystemes AS SystemesCibles;
END;
GO

-- Procédure : Audit automatique
CREATE OR ALTER PROCEDURE sp_AuditAction
    @ClientID INT = NULL,
    @TypeAction VARCHAR(50),
    @TableCiblee NVARCHAR(100),
    @EnregistrementID INT = NULL,
    @AncienneValeur NVARCHAR(MAX) = NULL,
    @NouvelleValeur NVARCHAR(MAX) = NULL,
    @AdresseIP NVARCHAR(50) = NULL
AS
BEGIN
    INSERT INTO JournalAudit (ClientID, TypeAction, TableCiblee, EnregistrementID, AncienneValeur, NouvelleValeur, AdresseIP)
    VALUES (@ClientID, @TypeAction, @TableCiblee, @EnregistrementID, @AncienneValeur, @NouvelleValeur, @AdresseIP);
END;
GO

PRINT '✓ Procédures stockées créées';
GO

-- ============================================================================
-- VUES UTILES POUR REPORTING
-- ============================================================================

PRINT 'Création vues de reporting...';
GO

-- Vue : Performance portefeuille par client
CREATE OR ALTER VIEW vw_PerformancePortefeuille AS
SELECT 
    c.ClientID,
    CASE 
        WHEN ci.Nom IS NOT NULL THEN ci.Prenom + ' ' + ci.Nom
        ELSE cin.NomEntreprise
    END AS NomClient,
    COUNT(DISTINCT cpt.CompteID) AS NombreComptes,
    COUNT(s.SouscriptionID) AS NombreSouscriptions,
    SUM(s.MontantInvesti) AS TotalInvesti,
    SUM(s.ValeurActuelle) AS ValeurActuelle,
    SUM(s.InteretsAccumules) AS InteretsTotaux,
    AVG(s.TMA_Reel) AS TMA_Moyen
FROM Clients c
LEFT JOIN ClientsIndividuels ci ON c.ClientID = ci.ClientID
LEFT JOIN ClientsInstitutionnels cin ON c.ClientID = cin.ClientID
LEFT JOIN ComptesRoles cr ON c.ClientID = cr.ClientID AND cr.Role = 'TITULAIRE_PRINCIPAL'
LEFT JOIN Comptes cpt ON cr.CompteID = cpt.CompteID
LEFT JOIN Souscriptions s ON cpt.CompteID = s.CompteID AND s.StatutSouscription = 'ACTIVE'
GROUP BY c.ClientID, ci.Prenom, ci.Nom, cin.NomEntreprise;
GO

-- Vue : Statut synchronisation
CREATE OR ALTER VIEW vw_StatutSynchronisation AS
SELECT 
    e.EvenementID,
    e.TypeEvenement,
    e.EntityType,
    e.DateCreation,
    e.StatutGlobal,
    e.NombreSystemesCibles,
    e.NombreSystemesReussis,
    CASE 
        WHEN e.NombreSystemesReussis = e.NombreSystemesCibles THEN 'Complet'
        WHEN e.NombreSystemesReussis > 0 THEN 'Partiel'
        ELSE 'Échec'
    END AS EtatSynchronisation,
    DATEDIFF(MINUTE, e.DateCreation, GETDATE()) AS MinutesDepuisCreation
FROM EvenementsSync e
WHERE e.StatutGlobal IN ('PENDING', 'PROCESSING', 'FAILED');
GO

PRINT '✓ Vues de reporting créées';
GO

-- ============================================================================
-- TRIGGERS POUR AUDIT AUTOMATIQUE
-- ============================================================================

PRINT 'Création triggers d''audit...';
GO

-- Trigger : Audit connexions
CREATE OR ALTER TRIGGER trg_AuditConnexion
ON ClientsAuthentification
AFTER UPDATE
AS
BEGIN
    IF UPDATE(DateDerniereConnexion)
    BEGIN
        INSERT INTO JournalAudit (ClientID, TypeAction, TableCiblee, EnregistrementID, NouvelleValeur)
        SELECT 
            i.ClientID,
            'LOGIN',
            'ClientsAuthentification',
            i.AuthID,
            CONCAT('Connexion à ', FORMAT(i.DateDerniereConnexion, 'yyyy-MM-dd HH:mm:ss'))
        FROM inserted i;
    END
END;
GO

-- Trigger : Audit modifications clients
CREATE OR ALTER TRIGGER trg_AuditClients
ON Clients
AFTER UPDATE
AS
BEGIN
    INSERT INTO JournalAudit (ClientID, TypeAction, TableCiblee, EnregistrementID, AncienneValeur, NouvelleValeur)
    SELECT 
        i.ClientID,
        'UPDATE',
        'Clients',
        i.ClientID,
        (SELECT d.* FOR JSON PATH, WITHOUT_ARRAY_WRAPPER),
        (SELECT i.* FOR JSON PATH, WITHOUT_ARRAY_WRAPPER)
    FROM inserted i
    INNER JOIN deleted d ON i.ClientID = d.ClientID;
END;
GO

PRINT '✓ Triggers d''audit créés';
GO

-- ============================================================================
-- RÉSUMÉ FINAL
-- ============================================================================

PRINT '';
PRINT '=================================================================';
PRINT 'AJOUTS TERMINÉS AVEC SUCCÈS!';
PRINT '=================================================================';
PRINT '';
PRINT 'Nouvelles tables créées:';
PRINT '  ✓ PlanComptable (10 comptes)';
PRINT '  ✓ EcrituresComptables';
PRINT '  ✓ LignesEcriture';
PRINT '  ✓ JournalAudit';
PRINT '  ✓ VerificationsConformite';
PRINT '  ✓ SystemesExternes (4 systèmes configurés)';
PRINT '  ✓ EvenementsSync';
PRINT '  ✓ LogsSynchronisation';
PRINT '';
PRINT 'Améliorations:';
PRINT '  ✓ TMA_Reel ajouté à Souscriptions';
PRINT '  ✓ CreePar ajouté à Transactions';
PRINT '  ✓ Commentaires ajouté à Transactions';
PRINT '';
PRINT 'Procédures stockées:';
PRINT '  ✓ sp_CalculerTMA';
PRINT '  ✓ sp_CreerEvenementSync';
PRINT '  ✓ sp_AuditAction';
PRINT '';
PRINT 'Vues:';
PRINT '  ✓ vw_PerformancePortefeuille';
PRINT '  ✓ vw_StatutSynchronisation';
PRINT '';
PRINT 'Triggers:';
PRINT '  ✓ trg_AuditConnexion';
PRINT '  ✓ trg_AuditClients';
PRINT '';
PRINT 'Votre base de données est maintenant complète et conforme';
PRINT 'à la documentation préparée!';
PRINT '=================================================================';
GO

-- Vérification finale
SELECT 
    'Clients' AS Module,
    (SELECT COUNT(*) FROM Clients) AS NombreEnregistrements
UNION ALL
SELECT 'Instruments', COUNT(*) FROM Instruments
UNION ALL
SELECT 'Plan Comptable', COUNT(*) FROM PlanComptable
UNION ALL
SELECT 'Systèmes Externes', COUNT(*) FROM SystemesExternes;
GO
