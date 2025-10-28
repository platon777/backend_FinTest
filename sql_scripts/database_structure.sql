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
