-- ============================================================================
-- DONNÉES DE TEST - BANQUE D'INVESTISSEMENT
-- ============================================================================
-- Ce script génère des données réalistes pour tester le système complet
-- ============================================================================

USE Db_test;
GO

PRINT '==================================================================';
PRINT 'INSERTION DES DONNÉES DE TEST';
PRINT '==================================================================';

-- ============================================================================
-- 1. CLIENTS INDIVIDUELS
-- ============================================================================

PRINT 'Insertion des clients individuels...';

-- Client 1: Jean Dupont (Profil Conservateur)
INSERT INTO Clients (ClientType, ProfilRisque, StatutClient)
VALUES ('INDIVIDUEL', 'CONSERVATEUR', 'ACTIF');

DECLARE @ClientID1 INT = SCOPE_IDENTITY();

INSERT INTO ClientsIndividuels (ClientID, Prenom, Nom, DateNaissance, LieuNaissance, Nationalite,
                                TypePieceIdentite, NumeroPieceIdentite, DateExpirationPiece,
                                SituationMatrimoniale, Profession, SourceRevenus, RevenuAnnuelEstime)
VALUES (@ClientID1, 'Jean', 'Dupont', '1985-03-15', 'Port-au-Prince', 'Haïtienne',
        'CIN', 'CIN-001-2024', '2029-03-15',
        'MARIE', 'Ingénieur', 'Salaire', 1200000.00);

INSERT INTO ClientsAuthentification (ClientID, Email, PasswordHash, EstActif)
VALUES (@ClientID1, 'jean.dupont@email.ht', '$2b$12$KxqZBHexample...hash', 1);

INSERT INTO AdressesClients (ClientID, TypeAdresse, AdresseLigne1, Ville, CodePostal, Pays, EstPrincipale)
VALUES (@ClientID1, 'DOMICILE', '15 Rue Lamarre', 'Pétion-Ville', 'HT6140', 'Haïti', 1);

INSERT INTO ContactsClients (ClientID, TypeContact, Valeur, EstPrincipal, EstVerifie)
VALUES (@ClientID1, 'EMAIL', 'jean.dupont@email.ht', 1, 1),
       (@ClientID1, 'MOBILE', '+509 3712-3456', 1, 1);

-- Client 2: Marie Pierre (Profil Modéré)
INSERT INTO Clients (ClientType, ProfilRisque, StatutClient)
VALUES ('INDIVIDUEL', 'MODERE', 'ACTIF');

DECLARE @ClientID2 INT = SCOPE_IDENTITY();

INSERT INTO ClientsIndividuels (ClientID, Prenom, Nom, DateNaissance, LieuNaissance, Nationalite,
                                TypePieceIdentite, NumeroPieceIdentite, DateExpirationPiece,
                                SituationMatrimoniale, Profession, SourceRevenus, RevenuAnnuelEstime)
VALUES (@ClientID2, 'Marie', 'Pierre', '1990-07-20', 'Cap-Haïtien', 'Haïtienne',
        'PASSPORT', 'PASS-HT-789456', '2028-07-20',
        'CELIBATAIRE', 'Médecin', 'Salaire + Consultation privée', 2500000.00);

INSERT INTO ClientsAuthentification (ClientID, Email, PasswordHash, EstActif)
VALUES (@ClientID2, 'marie.pierre@email.ht', '$2b$12$KxqZBHexample...hash', 1);

INSERT INTO AdressesClients (ClientID, TypeAdresse, AdresseLigne1, Ville, CodePostal, Pays, EstPrincipale)
VALUES (@ClientID2, 'DOMICILE', '89 Avenue Christophe', 'Port-au-Prince', 'HT6110', 'Haïti', 1);

INSERT INTO ContactsClients (ClientID, TypeContact, Valeur, EstPrincipal, EstVerifie)
VALUES (@ClientID2, 'EMAIL', 'marie.pierre@email.ht', 1, 1),
       (@ClientID2, 'MOBILE', '+509 3898-7654', 1, 1);

-- Client 3: Pierre Lafontaine (Profil Agressif)
INSERT INTO Clients (ClientType, ProfilRisque, StatutClient)
VALUES ('INDIVIDUEL', 'AGRESSIF', 'ACTIF');

DECLARE @ClientID3 INT = SCOPE_IDENTITY();

INSERT INTO ClientsIndividuels (ClientID, Prenom, Nom, DateNaissance, LieuNaissance, Nationalite,
                                TypePieceIdentite, NumeroPieceIdentite, DateExpirationPiece,
                                SituationMatrimoniale, Profession, SourceRevenus, RevenuAnnuelEstime)
VALUES (@ClientID3, 'Pierre', 'Lafontaine', '1978-11-05', 'Jacmel', 'Haïtienne',
        'CIN', 'CIN-003-2023', '2028-11-05',
        'MARIE', 'Entrepreneur', 'Entreprise', 5000000.00);

INSERT INTO ClientsAuthentification (ClientID, Email, PasswordHash, EstActif)
VALUES (@ClientID3, 'pierre.lafontaine@email.ht', '$2b$12$KxqZBHexample...hash', 1);

INSERT INTO AdressesClients (ClientID, TypeAdresse, AdresseLigne1, Ville, CodePostal, Pays, EstPrincipale)
VALUES (@ClientID3, 'DOMICILE', '45 Boulevard Harry Truman', 'Port-au-Prince', 'HT6120', 'Haïti', 1);

INSERT INTO ContactsClients (ClientID, TypeContact, Valeur, EstPrincipal, EstVerifie)
VALUES (@ClientID3, 'EMAIL', 'pierre.lafontaine@email.ht', 1, 1),
       (@ClientID3, 'MOBILE', '+509 3145-6789', 1, 1);

-- ============================================================================
-- 2. CLIENTS INSTITUTIONNELS
-- ============================================================================

PRINT 'Insertion des clients institutionnels...';

-- Client 4: Entreprise TechHaïti S.A.
INSERT INTO Clients (ClientType, ProfilRisque, StatutClient)
VALUES ('INSTITUTIONNEL', 'MODERE', 'ACTIF');

DECLARE @ClientID4 INT = SCOPE_IDENTITY();

INSERT INTO ClientsInstitutionnels (ClientID, NomEntreprise, NumeroRegistreCommerce, FormeJuridique,
                                    Secteur, DateCreationEntreprise, ChiffreAffairesAnnuel,
                                    NomRepresentantLegal, FonctionRepresentant)
VALUES (@ClientID4, 'TechHaïti S.A.', 'RC-2020-001234', 'Société Anonyme',
        'Technologies de l''information', '2020-01-15', 15000000.00,
        'Jacques Bernard', 'Directeur Général');

INSERT INTO ClientsAuthentification (ClientID, Email, PasswordHash, EstActif)
VALUES (@ClientID4, 'finance@techhaiti.ht', '$2b$12$KxqZBHexample...hash', 1);

INSERT INTO AdressesClients (ClientID, TypeAdresse, AdresseLigne1, Ville, CodePostal, Pays, EstPrincipale)
VALUES (@ClientID4, 'PROFESSIONNELLE', 'Zone Industrielle de Delmas', 'Delmas', 'HT6130', 'Haïti', 1);

INSERT INTO ContactsClients (ClientID, TypeContact, Valeur, EstPrincipal, EstVerifie)
VALUES (@ClientID4, 'EMAIL', 'finance@techhaiti.ht', 1, 1),
       (@ClientID4, 'TELEPHONE', '+509 2812-3456', 1, 1);

-- Client 5: Coopérative AgriProgrès
INSERT INTO Clients (ClientType, ProfilRisque, StatutClient)
VALUES ('INSTITUTIONNEL', 'CONSERVATEUR', 'ACTIF');

DECLARE @ClientID5 INT = SCOPE_IDENTITY();

INSERT INTO ClientsInstitutionnels (ClientID, NomEntreprise, NumeroRegistreCommerce, FormeJuridique,
                                    Secteur, DateCreationEntreprise, ChiffreAffairesAnnuel,
                                    NomRepresentantLegal, FonctionRepresentant)
VALUES (@ClientID5, 'Coopérative AgriProgrès', 'COOP-2018-789', 'Coopérative',
        'Agriculture', '2018-06-10', 8000000.00,
        'Lucie Toussaint', 'Présidente');

INSERT INTO ClientsAuthentification (ClientID, Email, PasswordHash, EstActif)
VALUES (@ClientID5, 'contact@agriprogres.ht', '$2b$12$KxqZBHexample...hash', 1);

INSERT INTO AdressesClients (ClientID, TypeAdresse, AdresseLigne1, Ville, CodePostal, Pays, EstPrincipale)
VALUES (@ClientID5, 'PROFESSIONNELLE', 'Route Nationale 1', 'Saint-Marc', 'HT4230', 'Haïti', 1);

INSERT INTO ContactsClients (ClientID, TypeContact, Valeur, EstPrincipal, EstVerifie)
VALUES (@ClientID5, 'EMAIL', 'contact@agriprogres.ht', 1, 1),
       (@ClientID5, 'TELEPHONE', '+509 2279-4567', 1, 1);

-- ============================================================================
-- 3. COMPTES D'INVESTISSEMENT
-- ============================================================================

PRINT 'Création des comptes d''investissement...';

-- Compte 1: Jean Dupont - Compte Investissement
INSERT INTO Comptes (NumeroCompte, TypeCompte, Devise, Solde, SoldeDisponible, StatutCompte)
VALUES ('INV-20250101-00001', 'INVESTISSEMENT', 'HTG', 500000.00, 500000.00, 'ACTIF');

DECLARE @CompteID1 INT = SCOPE_IDENTITY();

INSERT INTO ComptesRoles (CompteID, ClientID, Role, EstActif)
VALUES (@CompteID1, @ClientID1, 'TITULAIRE_PRINCIPAL', 1);

-- Compte 2: Jean Dupont - Compte Épargne
INSERT INTO Comptes (NumeroCompte, TypeCompte, Devise, Solde, SoldeDisponible, StatutCompte)
VALUES ('INV-20250101-00002', 'EPARGNE', 'HTG', 200000.00, 200000.00, 'ACTIF');

DECLARE @CompteID2 INT = SCOPE_IDENTITY();

INSERT INTO ComptesRoles (CompteID, ClientID, Role, EstActif)
VALUES (@CompteID2, @ClientID1, 'TITULAIRE_PRINCIPAL', 1);

-- Compte 3: Marie Pierre - Compte Investissement
INSERT INTO Comptes (NumeroCompte, TypeCompte, Devise, Solde, SoldeDisponible, StatutCompte)
VALUES ('INV-20250102-00003', 'INVESTISSEMENT', 'HTG', 800000.00, 800000.00, 'ACTIF');

DECLARE @CompteID3 INT = SCOPE_IDENTITY();

INSERT INTO ComptesRoles (CompteID, ClientID, Role, EstActif)
VALUES (@CompteID3, @ClientID2, 'TITULAIRE_PRINCIPAL', 1);

-- Compte 4: Pierre Lafontaine - Compte Investissement
INSERT INTO Comptes (NumeroCompte, TypeCompte, Devise, Solde, SoldeDisponible, StatutCompte)
VALUES ('INV-20250103-00004', 'INVESTISSEMENT', 'HTG', 2000000.00, 2000000.00, 'ACTIF');

DECLARE @CompteID4 INT = SCOPE_IDENTITY();

INSERT INTO ComptesRoles (CompteID, ClientID, Role, EstActif)
VALUES (@CompteID4, @ClientID3, 'TITULAIRE_PRINCIPAL', 1);

-- Compte 5: TechHaïti - Compte Cash
INSERT INTO Comptes (NumeroCompte, TypeCompte, Devise, Solde, SoldeDisponible, StatutCompte)
VALUES ('INV-20250104-00005', 'CASH', 'HTG', 5000000.00, 5000000.00, 'ACTIF');

DECLARE @CompteID5 INT = SCOPE_IDENTITY();

INSERT INTO ComptesRoles (CompteID, ClientID, Role, EstActif)
VALUES (@CompteID5, @ClientID4, 'TITULAIRE_PRINCIPAL', 1);

-- Compte 6: AgriProgrès - Compte Investissement
INSERT INTO Comptes (NumeroCompte, TypeCompte, Devise, Solde, SoldeDisponible, StatutCompte)
VALUES ('INV-20250105-00006', 'INVESTISSEMENT', 'HTG', 3000000.00, 3000000.00, 'ACTIF');

DECLARE @CompteID6 INT = SCOPE_IDENTITY();

INSERT INTO ComptesRoles (CompteID, ClientID, Role, EstActif)
VALUES (@CompteID6, @ClientID5, 'TITULAIRE_PRINCIPAL', 1);

-- ============================================================================
-- 4. INSTRUMENTS FINANCIERS SUPPLÉMENTAIRES
-- ============================================================================

PRINT 'Ajout d''instruments financiers supplémentaires...';

-- Obligations d'État et Corporatives
INSERT INTO Instruments (TypeInstrumentID, Code, Nom, Emetteur, TauxRendementAnnuel,
                        DateEmission, DateMaturite, ValeurNominale, MontantMinimum,
                        Devise, FrequencePaiementInterets, StatutInstrument)
VALUES
-- Obligations d'État
(1, 'OBL-GOUV-2025-5Y', 'Obligation Gouvernement Haïti 7% 2025-2030',
 'République d''Haïti', 7.00, '2025-01-15', '2030-01-15',
 1000.00, 10000.00, 'HTG', 'SEMESTRIEL', 'DISPONIBLE'),

(1, 'OBL-GOUV-2025-3Y', 'Obligation Gouvernement Haïti 5.5% 2025-2028',
 'République d''Haïti', 5.50, '2025-02-01', '2028-02-01',
 1000.00, 5000.00, 'HTG', 'TRIMESTRIEL', 'DISPONIBLE'),

-- Obligations Corporatives
(1, 'OBL-TELECOM-2025', 'Obligation Natcom 8% 2025-2030',
 'Natcom', 8.00, '2025-01-20', '2030-01-20',
 1000.00, 15000.00, 'HTG', 'SEMESTRIEL', 'DISPONIBLE'),

(1, 'OBL-BANQ-2025', 'Obligation Unibank 6.5% 2025-2029',
 'Unibank', 6.50, '2025-03-01', '2029-03-01',
 1000.00, 20000.00, 'HTG', 'TRIMESTRIEL', 'DISPONIBLE'),

-- Dépôts à terme
(4, 'DEPOT-6M', 'Dépôt à terme 6 mois',
 'Banque', 3.50, '2025-01-01', '2025-07-01',
 1.00, 50000.00, 'HTG', 'A_MATURITE', 'DISPONIBLE'),

(4, 'DEPOT-24M', 'Dépôt à terme 24 mois',
 'Banque', 5.00, '2025-01-01', '2027-01-01',
 1.00, 100000.00, 'HTG', 'A_MATURITE', 'DISPONIBLE');

-- ============================================================================
-- 5. TRANSACTIONS - DÉPÔTS INITIAUX
-- ============================================================================

PRINT 'Création des transactions de dépôt initiaux...';

-- Dépôts initiaux pour chaque compte
INSERT INTO Transactions (TypeTransaction, CompteDestination, Montant, Devise,
                         Description, StatutTransaction, DateExecution, EstAutomatique)
VALUES
(@CompteID1, 'DEPOT', NULL, 500000.00, 'HTG', 'Dépôt initial', 'EXECUTEE', GETDATE(), 0),
(@CompteID2, 'DEPOT', NULL, 200000.00, 'HTG', 'Dépôt initial', 'EXECUTEE', GETDATE(), 0),
(@CompteID3, 'DEPOT', NULL, 800000.00, 'HTG', 'Dépôt initial', 'EXECUTEE', GETDATE(), 0),
(@CompteID4, 'DEPOT', NULL, 2000000.00, 'HTG', 'Dépôt initial', 'EXECUTEE', GETDATE(), 0),
(@CompteID5, 'DEPOT', NULL, 5000000.00, 'HTG', 'Dépôt initial - TechHaïti', 'EXECUTEE', GETDATE(), 0),
(@CompteID6, 'DEPOT', NULL, 3000000.00, 'HTG', 'Dépôt initial - AgriProgrès', 'EXECUTEE', GETDATE(), 0);

-- ============================================================================
-- 6. SOUSCRIPTIONS (INVESTISSEMENTS)
-- ============================================================================

PRINT 'Création des souscriptions (investissements)...';

-- Jean Dupont investit dans une obligation BRH (conservateur)
INSERT INTO Souscriptions (CompteID, InstrumentID, MontantInvesti, NombreUnites,
                          TauxSouscription, DateMaturiteEffective, ValeurActuelle,
                          InteretsAccumules, StatutSouscription)
VALUES (@CompteID1, 1, 100000.00, 100, 5.00, '2030-01-01', 100000.00, 0, 'ACTIVE');

DECLARE @SouscID1 INT = SCOPE_IDENTITY();

-- Mettre à jour le solde
UPDATE Comptes SET SoldeDisponible = SoldeDisponible - 100000.00 WHERE CompteID = @CompteID1;

-- Transaction de souscription
INSERT INTO Transactions (TypeTransaction, CompteSource, Montant, Devise,
                         Description, StatutTransaction, DateExecution,
                         EstAutomatique, SouscriptionID)
VALUES ('SOUSCRIPTION', @CompteID1, 100000.00, 'HTG',
        'Souscription Obligation BRH 5%', 'EXECUTEE', GETDATE(), 0, @SouscID1);

-- Marie Pierre investit dans plusieurs instruments (modéré)
-- Obligation EDH
INSERT INTO Souscriptions (CompteID, InstrumentID, MontantInvesti, NombreUnites,
                          TauxSouscription, DateMaturiteEffective, ValeurActuelle,
                          InteretsAccumules, StatutSouscription)
VALUES (@CompteID3, 2, 150000.00, 150, 6.00, '2028-01-01', 150000.00, 0, 'ACTIVE');

DECLARE @SouscID2 INT = SCOPE_IDENTITY();

UPDATE Comptes SET SoldeDisponible = SoldeDisponible - 150000.00 WHERE CompteID = @CompteID3;

INSERT INTO Transactions (TypeTransaction, CompteSource, Montant, Devise,
                         Description, StatutTransaction, DateExecution,
                         EstAutomatique, SouscriptionID)
VALUES ('SOUSCRIPTION', @CompteID3, 150000.00, 'HTG',
        'Souscription Obligation EDH 6%', 'EXECUTEE', GETDATE(), 0, @SouscID2);

-- Obligation Gouvernement
INSERT INTO Souscriptions (CompteID, InstrumentID, MontantInvesti, NombreUnites,
                          TauxSouscription, DateMaturiteEffective, ValeurActuelle,
                          InteretsAccumules, StatutSouscription)
VALUES (@CompteID3, 4, 200000.00, 200, 7.00, '2030-01-15', 200000.00, 0, 'ACTIVE');

DECLARE @SouscID3 INT = SCOPE_IDENTITY();

UPDATE Comptes SET SoldeDisponible = SoldeDisponible - 200000.00 WHERE CompteID = @CompteID3;

INSERT INTO Transactions (TypeTransaction, CompteSource, Montant, Devise,
                         Description, StatutTransaction, DateExecution,
                         EstAutomatique, SouscriptionID)
VALUES ('SOUSCRIPTION', @CompteID3, 200000.00, 'HTG',
        'Souscription Obligation Gouv 7%', 'EXECUTEE', GETDATE(), 0, @SouscID3);

-- Pierre Lafontaine (agressif) - diversifie avec obligations corporatives
-- Obligation Natcom
INSERT INTO Souscriptions (CompteID, InstrumentID, MontantInvesti, NombreUnites,
                          TauxSouscription, DateMaturiteEffective, ValeurActuelle,
                          InteretsAccumules, StatutSouscription)
VALUES (@CompteID4, 6, 500000.00, 500, 8.00, '2030-01-20', 500000.00, 0, 'ACTIVE');

DECLARE @SouscID4 INT = SCOPE_IDENTITY();

UPDATE Comptes SET SoldeDisponible = SoldeDisponible - 500000.00 WHERE CompteID = @CompteID4;

INSERT INTO Transactions (TypeTransaction, CompteSource, Montant, Devise,
                         Description, StatutTransaction, DateExecution,
                         EstAutomatique, SouscriptionID)
VALUES ('SOUSCRIPTION', @CompteID4, 500000.00, 'HTG',
        'Souscription Obligation Natcom 8%', 'EXECUTEE', GETDATE(), 0, @SouscID4);

-- Obligation Unibank
INSERT INTO Souscriptions (CompteID, InstrumentID, MontantInvesti, NombreUnites,
                          TauxSouscription, DateMaturiteEffective, ValeurActuelle,
                          InteretsAccumules, StatutSouscription)
VALUES (@CompteID4, 7, 300000.00, 300, 6.50, '2029-03-01', 300000.00, 0, 'ACTIVE');

DECLARE @SouscID5 INT = SCOPE_IDENTITY();

UPDATE Comptes SET SoldeDisponible = SoldeDisponible - 300000.00 WHERE CompteID = @CompteID4;

INSERT INTO Transactions (TypeTransaction, CompteSource, Montant, Devise,
                         Description, StatutTransaction, DateExecution,
                         EstAutomatique, SouscriptionID)
VALUES ('SOUSCRIPTION', @CompteID4, 300000.00, 'HTG',
        'Souscription Obligation Unibank 6.5%', 'EXECUTEE', GETDATE(), 0, @SouscID5);

-- TechHaïti - Dépôt à terme 24 mois
INSERT INTO Souscriptions (CompteID, InstrumentID, MontantInvesti, NombreUnites,
                          TauxSouscription, DateMaturiteEffective, ValeurActuelle,
                          InteretsAccumules, StatutSouscription)
VALUES (@CompteID5, 9, 1000000.00, 1000000, 5.00, '2027-01-01', 1000000.00, 0, 'ACTIVE');

DECLARE @SouscID6 INT = SCOPE_IDENTITY();

UPDATE Comptes SET SoldeDisponible = SoldeDisponible - 1000000.00 WHERE CompteID = @CompteID5;

INSERT INTO Transactions (TypeTransaction, CompteSource, Montant, Devise,
                         Description, StatutTransaction, DateExecution,
                         EstAutomatique, SouscriptionID)
VALUES ('SOUSCRIPTION', @CompteID5, 1000000.00, 'HTG',
        'Souscription Dépôt 24 mois', 'EXECUTEE', GETDATE(), 0, @SouscID6);

-- AgriProgrès - Obligation Gouvernement (conservateur)
INSERT INTO Souscriptions (CompteID, InstrumentID, MontantInvesti, NombreUnites,
                          TauxSouscription, DateMaturiteEffective, ValeurActuelle,
                          InteretsAccumules, StatutSouscription)
VALUES (@CompteID6, 5, 500000.00, 500, 5.50, '2028-02-01', 500000.00, 0, 'ACTIVE');

DECLARE @SouscID7 INT = SCOPE_IDENTITY();

UPDATE Comptes SET SoldeDisponible = SoldeDisponible - 500000.00 WHERE CompteID = @CompteID6;

INSERT INTO Transactions (TypeTransaction, CompteSource, Montant, Devise,
                         Description, StatutTransaction, DateExecution,
                         EstAutomatique, SouscriptionID)
VALUES ('SOUSCRIPTION', @CompteID6, 500000.00, 'HTG',
        'Souscription Obligation Gouv 5.5%', 'EXECUTEE', GETDATE(), 0, @SouscID7);

-- ============================================================================
-- 7. PAIEMENTS D'INTÉRÊTS (Simulés)
-- ============================================================================

PRINT 'Création de paiements d''intérêts...';

-- Calculer et créer des paiements d'intérêts trimestriels simulés
-- Pour Obligation BRH (Jean Dupont) - Taux 5% annuel, trimestriel
DECLARE @InteretTrimestriel1 DECIMAL(18,2) = 100000.00 * 0.05 / 4;

INSERT INTO PaiementsInterets (SouscriptionID, DatePaiement, MontantInteret, StatutPaiement)
VALUES (@SouscID1, DATEADD(MONTH, 3, GETDATE()), @InteretTrimestriel1, 'PLANIFIE');

-- Pour Obligation EDH (Marie Pierre) - Taux 6% annuel, semestriel
DECLARE @InteretSemestriel1 DECIMAL(18,2) = 150000.00 * 0.06 / 2;

INSERT INTO PaiementsInterets (SouscriptionID, DatePaiement, MontantInteret, StatutPaiement)
VALUES (@SouscID2, DATEADD(MONTH, 6, GETDATE()), @InteretSemestriel1, 'PLANIFIE');

-- ============================================================================
-- 8. TRANSACTIONS SUPPLÉMENTAIRES
-- ============================================================================

PRINT 'Création de transactions supplémentaires...';

-- Transfert entre comptes de Jean Dupont
INSERT INTO Transactions (TypeTransaction, CompteSource, CompteDestination, Montant, Devise,
                         Description, StatutTransaction, DateExecution, EstAutomatique)
VALUES ('TRANSFERT', @CompteID2, @CompteID1, 50000.00, 'HTG',
        'Transfert Épargne vers Investissement', 'EXECUTEE', GETDATE(), 0);

UPDATE Comptes SET Solde = Solde - 50000.00, SoldeDisponible = SoldeDisponible - 50000.00
WHERE CompteID = @CompteID2;

UPDATE Comptes SET Solde = Solde + 50000.00, SoldeDisponible = SoldeDisponible + 50000.00
WHERE CompteID = @CompteID1;

-- Retrait par Marie Pierre
INSERT INTO Transactions (TypeTransaction, CompteSource, Montant, Devise,
                         Description, StatutTransaction, DateExecution, EstAutomatique)
VALUES ('RETRAIT', @CompteID3, 100000.00, 'HTG',
        'Retrait pour dépenses personnelles', 'EXECUTEE', GETDATE(), 0);

UPDATE Comptes SET Solde = Solde - 100000.00, SoldeDisponible = SoldeDisponible - 100000.00
WHERE CompteID = @CompteID3;

-- Nouveau dépôt par Pierre Lafontaine
INSERT INTO Transactions (TypeTransaction, CompteDestination, Montant, Devise,
                         Description, StatutTransaction, DateExecution, EstAutomatique)
VALUES ('DEPOT', @CompteID4, 500000.00, 'HTG',
        'Dépôt supplémentaire', 'EXECUTEE', GETDATE(), 0);

UPDATE Comptes SET Solde = Solde + 500000.00, SoldeDisponible = SoldeDisponible + 500000.00
WHERE CompteID = @CompteID4;

-- ============================================================================
-- RÉSUMÉ DES DONNÉES CRÉÉES
-- ============================================================================

PRINT '';
PRINT '==================================================================';
PRINT 'RÉSUMÉ DES DONNÉES INSÉRÉES:';
PRINT '==================================================================';
PRINT '';

SELECT 'Clients' AS Type, COUNT(*) AS Nombre FROM Clients;
SELECT 'Comptes' AS Type, COUNT(*) AS Nombre FROM Comptes;
SELECT 'Instruments' AS Type, COUNT(*) AS Nombre FROM Instruments;
SELECT 'Souscriptions' AS Type, COUNT(*) AS Nombre FROM Souscriptions;
SELECT 'Transactions' AS Type, COUNT(*) AS Nombre FROM Transactions;
SELECT 'Paiements Intérêts' AS Type, COUNT(*) AS Nombre FROM PaiementsInterets;

PRINT '';
PRINT '==================================================================';
PRINT 'INFORMATIONS DE CONNEXION POUR LES TESTS:';
PRINT '==================================================================';
PRINT 'Client 1: jean.dupont@email.ht (Profil Conservateur)';
PRINT 'Client 2: marie.pierre@email.ht (Profil Modéré)';
PRINT 'Client 3: pierre.lafontaine@email.ht (Profil Agressif)';
PRINT 'Client 4: finance@techhaiti.ht (Institutionnel - Tech)';
PRINT 'Client 5: contact@agriprogres.ht (Institutionnel - Agri)';
PRINT '';
PRINT 'Mot de passe pour tous les comptes: utilisez le hash bcrypt approprié';
PRINT '==================================================================';

GO

PRINT '';
PRINT 'DONNÉES DE TEST INSÉRÉES AVEC SUCCÈS!';
PRINT '';
