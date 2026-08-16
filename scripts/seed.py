"""Jeu de données de démonstration idempotent pour le prototype ProFin."""

from datetime import date, datetime, timezone
from decimal import Decimal

from sqlalchemy import select

from app.core.security import hash_password
from app.db.database import Base, SessionLocal, engine
from app.models.models import (
    Account,
    AccountRole,
    AccountingEntry,
    Client,
    ClientAddress,
    ClientAuthentication,
    ClientContact,
    IndividualProfile,
    InstitutionalProfile,
    Instrument,
    InstrumentType,
    InvestmentOrder,
    OrderWorkflowStep,
    Subscription,
    Transaction,
)


PASSWORD = "ProfinDemo!2026"


def find_or_create_client(db, email: str, **kwargs) -> Client:
    auth = db.scalar(select(ClientAuthentication).where(ClientAuthentication.email == email))
    if auth:
        return auth.client
    client = Client(client_type=kwargs["client_type"], risk_profile=kwargs["risk_profile"], status="ACTIF")
    client.auth = ClientAuthentication(email=email, password_hash=hash_password(PASSWORD), is_active=True)
    if kwargs["client_type"] == "INDIVIDUEL":
        client.individual_profile = IndividualProfile(
            first_name=kwargs["first_name"], last_name=kwargs["last_name"], birth_date=kwargs["birth_date"],
            nationality="Haïtienne", identity_type="CIN", identity_number=kwargs["identity_number"],
            profession=kwargs["profession"], income_source=kwargs["income_source"], estimated_annual_income=kwargs["income"],
        )
    else:
        client.institutional_profile = InstitutionalProfile(
            company_name=kwargs["company_name"], registration_number=kwargs["registration_number"],
            legal_form=kwargs["legal_form"], sector=kwargs["sector"], annual_revenue=kwargs["revenue"],
            legal_representative=kwargs["representative"],
        )
    client.addresses.append(ClientAddress(line1=kwargs["address"], city=kwargs["city"], postal_code=kwargs["postal_code"], country="Haïti", is_primary=True))
    client.contacts.append(ClientContact(contact_type="TELEPHONE", value=kwargs["phone"], is_primary=True, is_verified=True))
    db.add(client)
    db.flush()
    return client


def account(db, number: str, client: Client, currency: str, balance: str, account_type: str = "INVESTISSEMENT", role: str = "TITULAIRE_PRINCIPAL") -> Account:
    item = db.scalar(select(Account).where(Account.account_number == number))
    if item:
        return item
    item = Account(account_number=number, account_type=account_type, currency=currency, balance=Decimal(balance), available_balance=Decimal(balance), status="ACTIF")
    item.roles.append(AccountRole(client=client, role=role, is_active=True))
    db.add(item)
    db.flush()
    return item


def instrument(db, code: str, type_item: InstrumentType, **kwargs) -> Instrument:
    item = db.scalar(select(Instrument).where(Instrument.code == code))
    if item:
        return item
    item = Instrument(code=code, instrument_type=type_item, **kwargs)
    db.add(item)
    db.flush()
    return item


def executed_transaction(db, transaction_type: str, amount: str, currency: str, source: Account | None, destination: Account | None, description: str, client: Client, when: datetime, subscription_id: int | None = None) -> Transaction:
    item = Transaction(transaction_type=transaction_type, amount=Decimal(amount), currency=currency, source_account_id=source.id if source else None, destination_account_id=destination.id if destination else None, description=description, status="EXECUTED", created_at=when, executed_at=when, created_by_client_id=client.id, approved_by_client_id=client.id)
    db.add(item)
    db.flush()
    if transaction_type == "DEPOT" and destination:
        db.add_all([
            AccountingEntry(transaction_id=item.id, account_code="BANK_SETTLEMENT", direction="DEBIT", amount=Decimal(amount), currency=currency),
            AccountingEntry(transaction_id=item.id, account_code=f"CLIENT_{destination.id}", direction="CREDIT", amount=Decimal(amount), currency=currency),
        ])
    elif transaction_type == "RETRAIT" and source:
        db.add_all([
            AccountingEntry(transaction_id=item.id, account_code=f"CLIENT_{source.id}", direction="DEBIT", amount=Decimal(amount), currency=currency),
            AccountingEntry(transaction_id=item.id, account_code="BANK_SETTLEMENT", direction="CREDIT", amount=Decimal(amount), currency=currency),
        ])
    elif transaction_type == "SOUSCRIPTION" and source:
        db.add_all([
            AccountingEntry(transaction_id=item.id, account_code=f"CLIENT_{source.id}", direction="CREDIT", amount=Decimal(amount), currency=currency),
            AccountingEntry(transaction_id=item.id, account_code="INVESTMENT_POSITION", direction="DEBIT", amount=Decimal(amount), currency=currency),
        ])
    return item


def main() -> None:
    Base.metadata.create_all(engine)
    db = SessionLocal()
    try:
        marie = find_or_create_client(db, "marie.jean@demo.profin.ht", client_type="INDIVIDUEL", risk_profile="MODERE", first_name="Marie", last_name="Jean", birth_date=date(1990, 3, 20), identity_number="CIN-DEMO-001", profession="Directrice commerciale", income_source="Salaire et placements", income=Decimal("78000"), address="45 Rue Grégoire", city="Pétion-Ville", postal_code="HT6140", phone="+509 3812 5678")
        caribe = find_or_create_client(db, "caribe.invest@demo.profin.ht", client_type="INSTITUTIONNEL", risk_profile="AGRESSIF", company_name="Caribe Investissements S.A.", registration_number="RC-DEMO-2024-014", legal_form="Société anonyme", sector="Gestion d'actifs", revenue=Decimal("12500000"), representative="Lucien Pierre", address="12 Boulevard Toussaint Louverture", city="Port-au-Prince", postal_code="HT6110", phone="+509 3700 1122")
        paul = find_or_create_client(db, "paul.observer@demo.profin.ht", client_type="INDIVIDUEL", risk_profile="CONSERVATEUR", first_name="Paul", last_name="Joseph", birth_date=date(1986, 7, 11), identity_number="CIN-DEMO-003", profession="Architecte", income_source="Honoraires professionnels", income=Decimal("54000"), address="8 Rue Lambert", city="Pétion-Ville", postal_code="HT6140", phone="+509 3622 8899")

        sophie = find_or_create_client(db, "sophie.checker@demo.profin.ht", client_type="INDIVIDUEL", risk_profile="MODERE", first_name="Sophie", last_name="Laurent", birth_date=date(1988, 9, 14), identity_number="CIN-DEMO-004", profession="Administratrice de portefeuille", income_source="Salaire et placements", income=Decimal("96000"), address="22 Rue Rigaud", city="Petion-Ville", postal_code="HT6140", phone="+509 3844 7711")
        marie_usd = account(db, "INV-2026-00001", marie, "USD", "35000")
        marie_htg = account(db, "SVG-2026-00002", marie, "HTG", "420000", "EPARGNE")
        shared_htg = account(db, "JNT-2026-00003", marie, "HTG", "185000", "INVESTISSEMENT")
        if not db.scalar(select(AccountRole).where(AccountRole.account_id == shared_htg.id, AccountRole.client_id == paul.id)):
            shared_htg.roles.append(AccountRole(client=paul, role="OBSERVATEUR", is_active=True))
        caribe_usd = account(db, "INV-2026-00004", caribe, "USD", "150000")
        if not db.scalar(select(AccountRole).where(AccountRole.account_id == marie_usd.id, AccountRole.client_id == sophie.id)):
            marie_usd.roles.append(AccountRole(client=sophie, role="MANDATAIRE", is_active=True))

        bond_type = db.scalar(select(InstrumentType).where(InstrumentType.code == "OBL"))
        if not bond_type:
            bond_type = InstrumentType(code="OBL", name="Obligation", description="Titres de dette à revenu fixe")
            db.add(bond_type)
            db.flush()
        fund_type = db.scalar(select(InstrumentType).where(InstrumentType.code == "FONDS"))
        if not fund_type:
            fund_type = InstrumentType(code="FONDS", name="Fonds commun", description="Fonds diversifié")
            db.add(fund_type)
            db.flush()
        brh = instrument(db, "OBL-BRH-2027", bond_type, name="Obligation BRH 2027 - Série A", description="Obligation souveraine en USD, coupon annuel fixe.", issuer="Banque de la République d'Haïti", annual_yield=Decimal("5.5000"), issue_date=date(2025, 6, 30), maturity_date=date(2027, 6, 30), nominal_value=Decimal("1000"), minimum_amount=Decimal("10000"), currency="USD", interest_frequency="SEMESTRIEL", status="DISPONIBLE")
        edh = instrument(db, "OBL-EDH-2028", bond_type, name="Obligation Énergie EDH 2028", description="Financement d'infrastructures énergétiques nationales.", issuer="Électricité d'Haïti", annual_yield=Decimal("6.2500"), issue_date=date(2025, 12, 15), maturity_date=date(2028, 12, 15), nominal_value=Decimal("1000"), minimum_amount=Decimal("15000"), currency="USD", interest_frequency="ANNUEL", status="DISPONIBLE")
        fund = instrument(db, "FND-CARAIBE-2030", fund_type, name="Fonds Croissance Caraïbes", description="Fonds diversifié de croissance régionale.", issuer="ProFin Asset Management", annual_yield=Decimal("7.8000"), issue_date=date(2026, 1, 15), maturity_date=date(2030, 1, 15), nominal_value=Decimal("100"), minimum_amount=Decimal("25000"), currency="USD", interest_frequency="ANNUEL", status="DISPONIBLE")

        if not db.scalar(select(Subscription).where(Subscription.account_id == marie_usd.id)):
            sub1 = Subscription(account=marie_usd, instrument=brh, invested_amount=Decimal("20000"), units=Decimal("20"), subscribed_at=datetime(2025, 7, 8, tzinfo=timezone.utc), effective_maturity_date=brh.maturity_date, subscription_yield=brh.annual_yield, current_value=Decimal("21100"), accrued_interest=Decimal("1100"), status="ACTIVE")
            sub2 = Subscription(account=marie_usd, instrument=edh, invested_amount=Decimal("15000"), units=Decimal("15"), subscribed_at=datetime(2026, 1, 20, tzinfo=timezone.utc), effective_maturity_date=edh.maturity_date, subscription_yield=edh.annual_yield, current_value=Decimal("15586"), accrued_interest=Decimal("586"), status="ACTIVE")
            db.add_all([sub1, sub2])
            db.flush()
            tx1 = executed_transaction(db, "SOUSCRIPTION", "20000", "USD", marie_usd, None, "Souscription Obligation BRH 2027 - Série A", marie, datetime(2025, 7, 8, tzinfo=timezone.utc), sub1.id)
            tx1.subscription_id = sub1.id
            tx2 = executed_transaction(db, "SOUSCRIPTION", "15000", "USD", marie_usd, None, "Souscription Obligation Énergie EDH 2028", marie, datetime(2026, 1, 20, tzinfo=timezone.utc), sub2.id)
            tx2.subscription_id = sub2.id
        if not db.scalar(select(Subscription).where(Subscription.account_id == caribe_usd.id)):
            sub3 = Subscription(account=caribe_usd, instrument=fund, invested_amount=Decimal("100000"), units=Decimal("1000"), subscribed_at=datetime(2026, 2, 3, tzinfo=timezone.utc), effective_maturity_date=fund.maturity_date, subscription_yield=fund.annual_yield, current_value=Decimal("104700"), accrued_interest=Decimal("4700"), status="ACTIVE")
            db.add(sub3)
            db.flush()
            tx3 = executed_transaction(db, "SOUSCRIPTION", "100000", "USD", caribe_usd, None, "Souscription Fonds Croissance Caraïbes", caribe, datetime(2026, 2, 3, tzinfo=timezone.utc), sub3.id)
            tx3.subscription_id = sub3.id

        if not db.scalar(select(Transaction).where(Transaction.description == "Dépôt initial Marie Jean")):
            executed_transaction(db, "DEPOT", "50000", "USD", None, marie_usd, "Dépôt initial Marie Jean", marie, datetime(2025, 6, 15, tzinfo=timezone.utc))
            executed_transaction(db, "DEPOT", "500000", "HTG", None, marie_htg, "Dépôt d'épargne initial", marie, datetime(2025, 6, 18, tzinfo=timezone.utc))
            executed_transaction(db, "DEPOT", "250000", "USD", None, caribe_usd, "Apport initial Caribe Investissements", caribe, datetime(2026, 1, 5, tzinfo=timezone.utc))
            executed_transaction(db, "RETRAIT", "15000", "USD", marie_usd, None, "Règlement de souscription BRH", marie, datetime(2025, 7, 8, tzinfo=timezone.utc))
            executed_transaction(db, "RETRAIT", "15000", "USD", marie_usd, None, "Règlement de souscription EDH", marie, datetime(2026, 1, 20, tzinfo=timezone.utc))

        if not db.scalar(select(InvestmentOrder).where(InvestmentOrder.submitted_by_client_id == marie.id, InvestmentOrder.status == "SUBMITTED")):
            order = InvestmentOrder(client_id=marie.id, account_id=marie_usd.id, instrument_id=brh.id, order_type="SOUSCRIPTION", amount=Decimal("10000"), units=Decimal("10"), currency="USD", status="SUBMITTED", client_comment="Allocation obligataire à valider", submitted_by_client_id=marie.id)
            marie_usd.available_balance -= order.amount
            db.add(order)
            db.flush()
            db.add_all([OrderWorkflowStep(order_id=order.id, step_code=code, actor_profile=profile) for code, profile in (("CONFORMITE", "CONFORMITE"), ("BACK_OFFICE", "BACK_OFFICE"), ("CHECKER", "SUPERVISEUR"))])

        db.commit()
        print("Seed ProFin terminé : 4 clients, 4 comptes, 3 instruments, 3 souscriptions, un ordre en attente et historique métier.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
