from datetime import date, datetime
from decimal import Decimal
from typing import Any, Literal

from pydantic import AliasChoices, BaseModel, ConfigDict, EmailStr, Field, field_validator


class APIModel(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class RegisterRequest(APIModel):
    client_type: Literal["INDIVIDUEL", "INSTITUTIONNEL"]
    email: EmailStr
    password: str = Field(min_length=8)
    prenom: str | None = None
    nom: str | None = None
    date_naissance: date | str | None = None
    numero_piece_identite: str | None = None
    type_piece_identite: str | None = "CIN"
    nationalite: str | None = "Haïtienne"
    profession: str | None = None
    source_revenus: str | None = None
    revenu_annuel_estime: Decimal | None = None
    nom_entreprise: str | None = None
    numero_registre_commerce: str | None = None
    nom_representant_legal: str | None = None
    forme_juridique: str | None = None
    secteur: str | None = None
    chiffre_affaires_annuel: Decimal | None = None
    adresse_ligne1: str | None = None
    ville: str | None = None
    code_postal: str | None = None
    pays: str | None = "Haïti"
    telephone: str | None = None
    profil_risque: str | None = "MODERE"
    devise: str | None = "USD"

    @field_validator("date_naissance", mode="before")
    @classmethod
    def normalize_birth_date(cls, value):
        return value.isoformat() if isinstance(value, date) else value


class LoginRequest(APIModel):
    email: EmailStr
    password: str


class RefreshRequest(APIModel):
    refresh_token: str


class ClientInfo(APIModel):
    client_id: int = Field(validation_alias=AliasChoices("client_id", "id"))
    email: str
    client_type: str
    prenom: str | None = None
    nom: str | None = None
    nom_entreprise: str | None = None


class TokenResponse(APIModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class LoginResponse(APIModel):
    success: bool = True
    message: str
    tokens: TokenResponse
    client: ClientInfo


class RegisterResponse(APIModel):
    success: bool = True
    message: str
    client_id: int
    email: str
    account_number: str


class AccountOut(APIModel):
    id: int
    account_number: str
    account_type: str
    currency: str
    balance: Decimal
    available_balance: Decimal
    status: str
    role: str | None = None


class AccountCreate(APIModel):
    account_type: Literal["INVESTISSEMENT", "EPARGNE", "CASH"] = "INVESTISSEMENT"
    currency: str = Field(min_length=3, max_length=3)


class InstrumentOut(APIModel):
    id: int
    code: str
    name: str
    description: str | None
    issuer: str
    annual_yield: Decimal
    entry_fee_rate: Decimal = Decimal("0")
    issue_date: date
    maturity_date: date
    nominal_value: Decimal
    minimum_amount: Decimal
    currency: str
    interest_frequency: str
    status: str
    instrument_type: str | None = None


class SubscriptionCreate(APIModel):
    account_id: int = Field(validation_alias=AliasChoices("account_id", "CompteID"))
    instrument_id: int = Field(validation_alias=AliasChoices("instrument_id", "InstrumentID"))
    invested_amount: Decimal = Field(gt=0, validation_alias=AliasChoices("invested_amount", "MontantInvesti"))
    units: Decimal | None = Field(default=None, gt=0, validation_alias=AliasChoices("units", "NombreUnites"))


class SubscriptionOut(APIModel):
    id: int
    account_id: int
    instrument_id: int
    invested_amount: Decimal
    units: Decimal
    subscribed_at: datetime
    effective_maturity_date: date
    subscription_yield: Decimal
    current_value: Decimal
    accrued_interest: Decimal
    fee_amount: Decimal = Decimal("0")
    status: str
    instrument_name: str | None = None
    instrument_code: str | None = None
    currency: str | None = None


class InvestmentOrderCreate(APIModel):
    account_id: int
    instrument_id: int
    amount: Decimal = Field(gt=0)
    units: Decimal | None = Field(default=None, gt=0)
    client_comment: str | None = Field(default=None, max_length=1000)


class OrderStepOut(APIModel):
    step_code: str
    status: str
    actor_profile: str
    notes: str | None = None
    completed_at: datetime | None = None


class OrderStepDecision(APIModel):
    decision: Literal["APPROVE", "REJECT"]
    notes: str | None = Field(default=None, max_length=1000)


class InvestmentOrderOut(APIModel):
    id: int
    client_id: int
    account_id: int
    instrument_id: int
    order_type: str
    amount: Decimal
    units: Decimal | None
    currency: str
    status: str
    client_comment: str | None
    rejection_reason: str | None
    created_at: datetime
    updated_at: datetime
    submitted_by_client_id: int
    checked_by_client_id: int | None
    executed_transaction_id: int | None
    executed_subscription_id: int | None
    instrument_name: str | None = None
    instrument_code: str | None = None
    account_number: str | None = None
    steps: list[OrderStepOut] = Field(default_factory=list)


class TransactionCreate(APIModel):
    transaction_type: Literal["DEPOT", "RETRAIT", "TRANSFERT"] = Field(validation_alias=AliasChoices("transaction_type", "TypeTransaction"))
    amount: Decimal = Field(gt=0, validation_alias=AliasChoices("amount", "Montant"))
    currency: str = Field(min_length=3, max_length=3, validation_alias=AliasChoices("currency", "Devise"))
    source_account_id: int | None = Field(default=None, validation_alias=AliasChoices("source_account_id", "CompteSource"))
    destination_account_id: int | None = Field(default=None, validation_alias=AliasChoices("destination_account_id", "CompteDestination"))
    description: str | None = None


class TransactionReject(APIModel):
    reason: str = Field(min_length=3, max_length=500)


class TransactionReverse(APIModel):
    reason: str = Field(min_length=3, max_length=500)


class TransactionOut(APIModel):
    id: int
    transaction_type: str
    source_account_id: int | None
    destination_account_id: int | None
    amount: Decimal
    currency: str
    description: str | None
    status: str
    created_at: datetime
    executed_at: datetime | None
    is_automatic: bool
    subscription_id: int | None = None
    created_by_client_id: int
    approved_by_client_id: int | None = None
    rejection_reason: str | None = None
    version: int = 1
    reversal_of_transaction_id: int | None = None
    reversed_at: datetime | None = None
    reversal_reason: str | None = None
    source_account_number: str | None = None
    destination_account_number: str | None = None


class InterestPaymentOut(APIModel):
    id: int
    subscription_id: int
    payment_date: datetime
    amount: Decimal
    status: str
    transaction_id: int | None = None
    instrument_code: str | None = None
    currency: str | None = None


class TransactionList(APIModel):
    total: int
    transactions: list[TransactionOut]


class ProfileOut(APIModel):
    client_id: int
    client_type: str
    email: str
    status: str
    risk_profile: str
    full_name: str
    phone: str | None = None
    address: dict[str, Any] | None = None
    individual: dict[str, Any] | None = None
    institutional: dict[str, Any] | None = None


class ProfileUpdate(APIModel):
    telephone: str | None = None
    adresse_ligne1: str | None = None
    ville: str | None = None
    code_postal: str | None = None


class PaginatedInstruments(APIModel):
    total: int
    instruments: list[InstrumentOut]


class DashboardOverview(APIModel):
    total_value: Decimal
    total_invested: Decimal
    total_return: Decimal
    return_percentage: Decimal
    active_subscriptions: int
    accounts: list[AccountOut]
    currency: str
