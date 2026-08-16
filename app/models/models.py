"""Modèle relationnel du Core Investment Platform ProFin.

Les noms SQL sont en snake_case pour rester portables entre PostgreSQL, SQLite
(tests) et les futurs outils de reporting.
"""

from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Index, Integer, Numeric, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.db.database import Base


class Client(Base):
    __tablename__ = "clients"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    client_type: Mapped[str] = mapped_column(String(20), nullable=False)
    risk_profile: Mapped[str] = mapped_column(String(20), default="MODERE", nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="ACTIF", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    auth: Mapped["ClientAuthentication"] = relationship(back_populates="client", uselist=False, cascade="all, delete-orphan")
    individual_profile: Mapped["IndividualProfile | None"] = relationship(back_populates="client", uselist=False, cascade="all, delete-orphan")
    institutional_profile: Mapped["InstitutionalProfile | None"] = relationship(back_populates="client", uselist=False, cascade="all, delete-orphan")
    addresses: Mapped[list["ClientAddress"]] = relationship(back_populates="client", cascade="all, delete-orphan")
    contacts: Mapped[list["ClientContact"]] = relationship(back_populates="client", cascade="all, delete-orphan")
    account_roles: Mapped[list["AccountRole"]] = relationship(back_populates="client", cascade="all, delete-orphan")
    created_transactions: Mapped[list["Transaction"]] = relationship(foreign_keys="Transaction.created_by_client_id", back_populates="maker")
    approved_transactions: Mapped[list["Transaction"]] = relationship(foreign_keys="Transaction.approved_by_client_id", back_populates="checker")
    refresh_tokens: Mapped[list["RefreshToken"]] = relationship(back_populates="client", cascade="all, delete-orphan")


class IndividualProfile(Base):
    __tablename__ = "individual_profiles"

    client_id: Mapped[int] = mapped_column(ForeignKey("clients.id", ondelete="CASCADE"), primary_key=True)
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    birth_date: Mapped[date] = mapped_column(Date, nullable=False)
    nationality: Mapped[str | None] = mapped_column(String(80))
    identity_type: Mapped[str | None] = mapped_column(String(50))
    identity_number: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    profession: Mapped[str | None] = mapped_column(String(200))
    income_source: Mapped[str | None] = mapped_column(String(500))
    estimated_annual_income: Mapped[Decimal | None] = mapped_column(Numeric(18, 2))

    client: Mapped[Client] = relationship(back_populates="individual_profile")


class InstitutionalProfile(Base):
    __tablename__ = "institutional_profiles"

    client_id: Mapped[int] = mapped_column(ForeignKey("clients.id", ondelete="CASCADE"), primary_key=True)
    company_name: Mapped[str] = mapped_column(String(200), nullable=False)
    registration_number: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    legal_form: Mapped[str | None] = mapped_column(String(80))
    sector: Mapped[str | None] = mapped_column(String(200))
    annual_revenue: Mapped[Decimal | None] = mapped_column(Numeric(18, 2))
    legal_representative: Mapped[str] = mapped_column(String(200), nullable=False)

    client: Mapped[Client] = relationship(back_populates="institutional_profile")


class ClientAddress(Base):
    __tablename__ = "client_addresses"

    id: Mapped[int] = mapped_column(primary_key=True)
    client_id: Mapped[int] = mapped_column(ForeignKey("clients.id", ondelete="CASCADE"), nullable=False)
    address_type: Mapped[str] = mapped_column(String(30), default="PRINCIPALE", nullable=False)
    line1: Mapped[str] = mapped_column(String(200), nullable=False)
    city: Mapped[str] = mapped_column(String(100), nullable=False)
    postal_code: Mapped[str | None] = mapped_column(String(20))
    country: Mapped[str] = mapped_column(String(100), default="Haïti", nullable=False)
    is_primary: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    client: Mapped[Client] = relationship(back_populates="addresses")


class ClientContact(Base):
    __tablename__ = "client_contacts"

    id: Mapped[int] = mapped_column(primary_key=True)
    client_id: Mapped[int] = mapped_column(ForeignKey("clients.id", ondelete="CASCADE"), nullable=False)
    contact_type: Mapped[str] = mapped_column(String(30), nullable=False)
    value: Mapped[str] = mapped_column(String(200), nullable=False)
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    client: Mapped[Client] = relationship(back_populates="contacts")


class ClientAuthentication(Base):
    __tablename__ = "client_authentications"

    id: Mapped[int] = mapped_column(primary_key=True)
    client_id: Mapped[int] = mapped_column(ForeignKey("clients.id", ondelete="CASCADE"), unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    client: Mapped[Client] = relationship(back_populates="auth")


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id: Mapped[int] = mapped_column(primary_key=True)
    client_id: Mapped[int] = mapped_column(ForeignKey("clients.id", ondelete="CASCADE"), nullable=False)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    ip_address: Mapped[str | None] = mapped_column(String(64))

    client: Mapped[Client] = relationship(back_populates="refresh_tokens")


class Account(Base):
    __tablename__ = "accounts"

    id: Mapped[int] = mapped_column(primary_key=True)
    account_number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    account_type: Mapped[str] = mapped_column(String(30), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    balance: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=0, nullable=False)
    available_balance: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=0, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="ACTIF", nullable=False)
    opened_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    roles: Mapped[list["AccountRole"]] = relationship(back_populates="account", cascade="all, delete-orphan")
    subscriptions: Mapped[list["Subscription"]] = relationship(back_populates="account")


class AccountRole(Base):
    __tablename__ = "account_roles"
    __table_args__ = (UniqueConstraint("account_id", "client_id", name="uq_account_client_role"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    account_id: Mapped[int] = mapped_column(ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False)
    client_id: Mapped[int] = mapped_column(ForeignKey("clients.id", ondelete="CASCADE"), nullable=False)
    role: Mapped[str] = mapped_column(String(30), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    account: Mapped[Account] = relationship(back_populates="roles")
    client: Mapped[Client] = relationship(back_populates="account_roles")


class InstrumentType(Base):
    __tablename__ = "instrument_types"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    instruments: Mapped[list["Instrument"]] = relationship(back_populates="instrument_type")


class Instrument(Base):
    __tablename__ = "instruments"
    __table_args__ = (Index("ix_instruments_status_currency", "status", "currency"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    instrument_type_id: Mapped[int] = mapped_column(ForeignKey("instrument_types.id"), nullable=False)
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    issuer: Mapped[str] = mapped_column(String(200), nullable=False)
    annual_yield: Mapped[Decimal] = mapped_column(Numeric(7, 4), nullable=False)
    entry_fee_rate: Mapped[Decimal] = mapped_column(Numeric(7, 4), default=0, nullable=False)
    issue_date: Mapped[date] = mapped_column(Date, nullable=False)
    maturity_date: Mapped[date] = mapped_column(Date, nullable=False)
    nominal_value: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    minimum_amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    interest_frequency: Mapped[str] = mapped_column(String(30), default="ANNUEL", nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="DISPONIBLE", nullable=False)

    instrument_type: Mapped[InstrumentType] = relationship(back_populates="instruments")
    subscriptions: Mapped[list["Subscription"]] = relationship(back_populates="instrument")


class Subscription(Base):
    __tablename__ = "subscriptions"

    id: Mapped[int] = mapped_column(primary_key=True)
    account_id: Mapped[int] = mapped_column(ForeignKey("accounts.id"), nullable=False)
    instrument_id: Mapped[int] = mapped_column(ForeignKey("instruments.id"), nullable=False)
    invested_amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    units: Mapped[Decimal] = mapped_column(Numeric(18, 6), nullable=False)
    subscribed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    effective_maturity_date: Mapped[date] = mapped_column(Date, nullable=False)
    subscription_yield: Mapped[Decimal] = mapped_column(Numeric(7, 4), nullable=False)
    current_value: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    accrued_interest: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=0, nullable=False)
    fee_amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=0, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="ACTIVE", nullable=False)

    account: Mapped[Account] = relationship(back_populates="subscriptions")
    instrument: Mapped[Instrument] = relationship(back_populates="subscriptions")
    interest_payments: Mapped[list["InterestPayment"]] = relationship(back_populates="subscription")


class InterestPayment(Base):
    __tablename__ = "interest_payments"
    __table_args__ = (UniqueConstraint("subscription_id", "payment_date", name="uq_interest_payment_subscription_date"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    subscription_id: Mapped[int] = mapped_column(ForeignKey("subscriptions.id"), nullable=False)
    payment_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="PLANIFIE", nullable=False)
    transaction_id: Mapped[int | None] = mapped_column(ForeignKey("transactions.id"))

    subscription: Mapped[Subscription] = relationship(back_populates="interest_payments")


class Transaction(Base):
    __tablename__ = "transactions"
    __table_args__ = (
        Index("ix_transactions_source_created", "source_account_id", "created_at"),
        Index("ix_transactions_destination_created", "destination_account_id", "created_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    transaction_type: Mapped[str] = mapped_column(String(40), nullable=False)
    source_account_id: Mapped[int | None] = mapped_column(ForeignKey("accounts.id"))
    destination_account_id: Mapped[int | None] = mapped_column(ForeignKey("accounts.id"))
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(30), default="PENDING_APPROVAL", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    executed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    is_automatic: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    subscription_id: Mapped[int | None] = mapped_column(ForeignKey("subscriptions.id"))
    created_by_client_id: Mapped[int | None] = mapped_column(ForeignKey("clients.id"))
    approved_by_client_id: Mapped[int | None] = mapped_column(ForeignKey("clients.id"))
    rejection_reason: Mapped[str | None] = mapped_column(Text)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    reversal_of_transaction_id: Mapped[int | None] = mapped_column(ForeignKey("transactions.id"))
    reversed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    reversal_reason: Mapped[str | None] = mapped_column(Text)

    maker: Mapped[Client | None] = relationship(foreign_keys=[created_by_client_id], back_populates="created_transactions")
    checker: Mapped[Client | None] = relationship(foreign_keys=[approved_by_client_id], back_populates="approved_transactions")


class InvestmentOrder(Base):
    """Ordre soumis par un client avant toute écriture de position.

    L'ordre garde le parcours métier séparé de la transaction financière : une
    soumission ne débite jamais le compte. La position et le mouvement
    comptable ne sont créés qu'après validation maker/checker.
    """

    __tablename__ = "investment_orders"
    __table_args__ = (
        Index("ix_investment_orders_client_created", "client_id", "created_at"),
        Index("ix_investment_orders_status", "status"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    client_id: Mapped[int] = mapped_column(ForeignKey("clients.id", ondelete="CASCADE"), nullable=False)
    account_id: Mapped[int] = mapped_column(ForeignKey("accounts.id"), nullable=False)
    instrument_id: Mapped[int] = mapped_column(ForeignKey("instruments.id"), nullable=False)
    order_type: Mapped[str] = mapped_column(String(20), default="SOUSCRIPTION", nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    units: Mapped[Decimal | None] = mapped_column(Numeric(18, 6))
    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="SUBMITTED", nullable=False)
    client_comment: Mapped[str | None] = mapped_column(Text)
    rejection_reason: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    submitted_by_client_id: Mapped[int] = mapped_column(ForeignKey("clients.id"), nullable=False)
    checked_by_client_id: Mapped[int | None] = mapped_column(ForeignKey("clients.id"))
    executed_transaction_id: Mapped[int | None] = mapped_column(ForeignKey("transactions.id"))
    executed_subscription_id: Mapped[int | None] = mapped_column(ForeignKey("subscriptions.id"))

    account: Mapped[Account] = relationship()
    instrument: Mapped[Instrument] = relationship()
    steps: Mapped[list["OrderWorkflowStep"]] = relationship(cascade="all, delete-orphan", order_by="OrderWorkflowStep.id")


class OrderWorkflowStep(Base):
    """Étapes internes simulées dans le prototype, sans connecteur externe."""

    __tablename__ = "order_workflow_steps"
    __table_args__ = (UniqueConstraint("order_id", "step_code", name="uq_order_workflow_step"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("investment_orders.id", ondelete="CASCADE"), nullable=False)
    step_code: Mapped[str] = mapped_column(String(30), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="PENDING", nullable=False)
    actor_profile: Mapped[str] = mapped_column(String(40), nullable=False)
    notes: Mapped[str | None] = mapped_column(Text)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class AccountingEntry(Base):
    __tablename__ = "accounting_entries"

    id: Mapped[int] = mapped_column(primary_key=True)
    transaction_id: Mapped[int] = mapped_column(ForeignKey("transactions.id", ondelete="CASCADE"), nullable=False)
    account_code: Mapped[str] = mapped_column(String(30), nullable=False)
    direction: Mapped[str] = mapped_column(String(10), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    posting_version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    is_reversal: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    client_id: Mapped[int | None] = mapped_column(ForeignKey("clients.id"))
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(80), nullable=False)
    entity_id: Mapped[str | None] = mapped_column(String(80))
    metadata_json: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
