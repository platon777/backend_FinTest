"""
Modèles SQLAlchemy - Version simplifiée (CLIENTS UNIQUEMENT)
Les CLIENTS sont les utilisateurs du système
"""
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Numeric, Date, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.database import Base


# ============================================================================
# CLIENTS
# ============================================================================

class Client(Base):
    __tablename__ = "Clients"

    ClientID = Column(Integer, primary_key=True, autoincrement=True)
    ClientType = Column(String(20), nullable=False)
    ProfilRisque = Column(String(20))
    StatutClient = Column(String(20), default='ACTIF')
    DateCreation = Column(DateTime, server_default=func.getdate())
    DerniereMiseAJour = Column(DateTime, server_default=func.getdate())

    # Relationships
    auth = relationship("ClientAuthentification", back_populates="client", uselist=False)
    individuel = relationship("ClientIndividuel", back_populates="client", uselist=False)
    institutionnel = relationship("ClientInstitutionnel", back_populates="client", uselist=False)
    adresses = relationship("AdresseClient", back_populates="client")
    contacts = relationship("ContactClient", back_populates="client")
    comptes_roles = relationship("CompteRole", back_populates="client")
    refresh_tokens = relationship("RefreshToken", back_populates="client")


class ClientIndividuel(Base):
    __tablename__ = "ClientsIndividuels"

    ClientID = Column(Integer, ForeignKey('Clients.ClientID'), primary_key=True)
    Prenom = Column(String(100), nullable=False)
    Nom = Column(String(100), nullable=False)
    DateNaissance = Column(Date, nullable=False)
    LieuNaissance = Column(String(200))
    Nationalite = Column(String(50))
    TypePieceIdentite = Column(String(50))
    NumeroPieceIdentite = Column(String(100), unique=True, nullable=False)
    DateExpirationPiece = Column(Date)
    SituationMatrimoniale = Column(String(20))
    Profession = Column(String(200))
    SourceRevenus = Column(String(500))
    RevenuAnnuelEstime = Column(Numeric(18, 2))

    client = relationship("Client", back_populates="individuel")


class ClientInstitutionnel(Base):
    __tablename__ = "ClientsInstitutionnels"

    ClientID = Column(Integer, ForeignKey('Clients.ClientID'), primary_key=True)
    NomEntreprise = Column(String(200), nullable=False)
    NumeroRegistreCommerce = Column(String(100), unique=True, nullable=False)
    FormeJuridique = Column(String(50))
    Secteur = Column(String(200))
    DateCreationEntreprise = Column(Date)
    ChiffreAffairesAnnuel = Column(Numeric(18, 2))
    NomRepresentantLegal = Column(String(200))
    FonctionRepresentant = Column(String(100))

    client = relationship("Client", back_populates="institutionnel")


class AdresseClient(Base):
    __tablename__ = "AdressesClients"

    AdresseID = Column(Integer, primary_key=True, autoincrement=True)
    ClientID = Column(Integer, ForeignKey('Clients.ClientID'), nullable=False)
    TypeAdresse = Column(String(20))
    AdresseLigne1 = Column(String(200))
    AdresseLigne2 = Column(String(200))
    Ville = Column(String(100))
    CodePostal = Column(String(20))
    Pays = Column(String(100))
    EstPrincipale = Column(Boolean, default=False)

    client = relationship("Client", back_populates="adresses")


class ContactClient(Base):
    __tablename__ = "ContactsClients"

    ContactID = Column(Integer, primary_key=True, autoincrement=True)
    ClientID = Column(Integer, ForeignKey('Clients.ClientID'), nullable=False)
    TypeContact = Column(String(20))
    Valeur = Column(String(200), nullable=False)
    EstPrincipal = Column(Boolean, default=False)
    EstVerifie = Column(Boolean, default=False)

    client = relationship("Client", back_populates="contacts")


# ============================================================================
# AUTHENTIFICATION
# ============================================================================

class ClientAuthentification(Base):
    __tablename__ = "ClientsAuthentification"

    AuthID = Column(Integer, primary_key=True, autoincrement=True)
    ClientID = Column(Integer, ForeignKey('Clients.ClientID', ondelete='CASCADE'), unique=True, nullable=False)
    Email = Column(String(200), unique=True, nullable=False, index=True)
    PasswordHash = Column(String(255), nullable=False)
    EstActif = Column(Boolean, default=True)
    DateCreation = Column(DateTime, server_default=func.getdate())
    DateDerniereConnexion = Column(DateTime)

    client = relationship("Client", back_populates="auth")


class RefreshToken(Base):
    __tablename__ = "RefreshTokens"

    TokenID = Column(Integer, primary_key=True, autoincrement=True)
    ClientID = Column(Integer, ForeignKey('Clients.ClientID', ondelete='CASCADE'), nullable=False)
    Token = Column(String(500), unique=True, nullable=False, index=True)
    DateCreation = Column(DateTime, server_default=func.getdate())
    DateExpiration = Column(DateTime, nullable=False)
    EstRevoque = Column(Boolean, default=False)
    AdresseIP = Column(String(50))

    client = relationship("Client", back_populates="refresh_tokens")


# ============================================================================
# COMPTES
# ============================================================================

class Compte(Base):
    __tablename__ = "Comptes"

    CompteID = Column(Integer, primary_key=True, autoincrement=True)
    NumeroCompte = Column(String(50), unique=True, nullable=False)
    TypeCompte = Column(String(30))
    Devise = Column(String(3), default='HTG')
    Solde = Column(Numeric(18, 2), default=0)
    SoldeDisponible = Column(Numeric(18, 2), default=0)
    DateOuverture = Column(DateTime, server_default=func.getdate())
    DateFermeture = Column(DateTime)
    StatutCompte = Column(String(20), default='ACTIF')

    roles = relationship("CompteRole", back_populates="compte")
    souscriptions = relationship("Souscription", back_populates="compte")


class CompteRole(Base):
    __tablename__ = "ComptesRoles"

    CompteRoleID = Column(Integer, primary_key=True, autoincrement=True)
    CompteID = Column(Integer, ForeignKey('Comptes.CompteID'), nullable=False)
    ClientID = Column(Integer, ForeignKey('Clients.ClientID'), nullable=False)
    Role = Column(String(30))
    DateDebut = Column(DateTime, server_default=func.getdate())
    DateFin = Column(DateTime)
    EstActif = Column(Boolean, default=True)

    compte = relationship("Compte", back_populates="roles")
    client = relationship("Client", back_populates="comptes_roles")


# ============================================================================
# INSTRUMENTS
# ============================================================================

class TypeInstrument(Base):
    __tablename__ = "TypesInstruments"

    TypeInstrumentID = Column(Integer, primary_key=True, autoincrement=True)
    Code = Column(String(50), unique=True, nullable=False)
    Nom = Column(String(200))
    Description = Column(Text)

    instruments = relationship("Instrument", back_populates="type_instrument")


class Instrument(Base):
    __tablename__ = "Instruments"

    InstrumentID = Column(Integer, primary_key=True, autoincrement=True)
    TypeInstrumentID = Column(Integer, ForeignKey('TypesInstruments.TypeInstrumentID'), nullable=False)
    Code = Column(String(50), unique=True, nullable=False)
    Nom = Column(String(200), nullable=False)
    Description = Column(Text)
    Emetteur = Column(String(200))
    TauxRendementAnnuel = Column(Numeric(5, 2))
    DateEmission = Column(Date)
    DateMaturite = Column(Date)
    ValeurNominale = Column(Numeric(18, 2))
    MontantMinimum = Column(Numeric(18, 2))
    Devise = Column(String(3))
    FrequencePaiementInterets = Column(String(20))
    StatutInstrument = Column(String(20), default='DISPONIBLE')

    type_instrument = relationship("TypeInstrument", back_populates="instruments")
    souscriptions = relationship("Souscription", back_populates="instrument")


# ============================================================================
# SOUSCRIPTIONS
# ============================================================================

class Souscription(Base):
    __tablename__ = "Souscriptions"

    SouscriptionID = Column(Integer, primary_key=True, autoincrement=True)
    CompteID = Column(Integer, ForeignKey('Comptes.CompteID'), nullable=False)
    InstrumentID = Column(Integer, ForeignKey('Instruments.InstrumentID'), nullable=False)
    MontantInvesti = Column(Numeric(18, 2), nullable=False)
    NombreUnites = Column(Numeric(18, 6))
    DateSouscription = Column(DateTime, server_default=func.getdate())
    DateMaturiteEffective = Column(Date)
    TauxSouscription = Column(Numeric(5, 2))
    ValeurActuelle = Column(Numeric(18, 2))
    InteretsAccumules = Column(Numeric(18, 2), default=0)
    StatutSouscription = Column(String(20), default='ACTIVE')

    compte = relationship("Compte", back_populates="souscriptions")
    instrument = relationship("Instrument", back_populates="souscriptions")
    paiements = relationship("PaiementInteret", back_populates="souscription")


class PaiementInteret(Base):
    __tablename__ = "PaiementsInterets"

    PaiementID = Column(Integer, primary_key=True, autoincrement=True)
    SouscriptionID = Column(Integer, ForeignKey('Souscriptions.SouscriptionID'), nullable=False)
    DatePaiement = Column(DateTime)
    MontantInteret = Column(Numeric(18, 2))
    StatutPaiement = Column(String(20))
    TransactionID = Column(Integer)

    souscription = relationship("Souscription", back_populates="paiements")


# ============================================================================
# TRANSACTIONS
# ============================================================================

class Transaction(Base):
    __tablename__ = "Transactions"

    TransactionID = Column(Integer, primary_key=True, autoincrement=True)
    TypeTransaction = Column(String(50))
    CompteSource = Column(Integer, ForeignKey('Comptes.CompteID'))
    CompteDestination = Column(Integer, ForeignKey('Comptes.CompteID'))
    Montant = Column(Numeric(18, 2), nullable=False)
    Devise = Column(String(3), nullable=False)
    Description = Column(Text)
    StatutTransaction = Column(String(30), default='EN_ATTENTE')
    DateCreation = Column(DateTime, server_default=func.getdate())
    DateExecution = Column(DateTime)
    EstAutomatique = Column(Boolean, default=False)
    SouscriptionID = Column(Integer)
