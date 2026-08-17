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
    InterestPayment,
    InstitutionalProfile,
    Instrument,
    InstrumentType,
    InvestmentOrder,
    OrderWorkflowStep,
    Subscription,
    Transaction,
)
from app.services.transaction_service import TransactionService


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


def grant_role(db, account_item: Account, client: Client, role: str) -> AccountRole:
    existing = db.scalar(select(AccountRole).where(AccountRole.account_id == account_item.id, AccountRole.client_id == client.id))
    if existing:
        return existing
    assignment = AccountRole(account=account_item, client=client, role=role, is_active=True)
    db.add(assignment)
    db.flush()
    return assignment


def account(db, number: str, client: Client, currency: str, balance: str, account_type: str = "INVESTISSEMENT", role: str = "TITULAIRE_PRINCIPAL") -> Account:
    item = db.scalar(select(Account).where(Account.account_number == number))
    if item:
        grant_role(db, item, client, role)
        return item
    item = Account(account_number=number, account_type=account_type, currency=currency, balance=Decimal(balance), available_balance=Decimal(balance), status="ACTIF")
    db.add(item)
    db.flush()
    grant_role(db, item, client, role)
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
    elif transaction_type == "PAIEMENT_INTERET" and destination:
        db.add_all([
            AccountingEntry(transaction_id=item.id, account_code="INTEREST_EXPENSE", direction="DEBIT", amount=Decimal(amount), currency=currency),
            AccountingEntry(transaction_id=item.id, account_code=f"CLIENT_{destination.id}", direction="CREDIT", amount=Decimal(amount), currency=currency),
        ])
    elif transaction_type == "FRAIS" and source:
        db.add_all([
            AccountingEntry(transaction_id=item.id, account_code=f"CLIENT_{source.id}", direction="DEBIT", amount=Decimal(amount), currency=currency),
            AccountingEntry(transaction_id=item.id, account_code="FEE_REVENUE", direction="CREDIT", amount=Decimal(amount), currency=currency),
        ])
    return item


def seed_coupon(db, subscription: Subscription, payment_date: date, status: str, client: Client) -> None:
    existing = db.scalar(select(InterestPayment).where(InterestPayment.subscription_id == subscription.id, InterestPayment.payment_date == payment_date))
    if existing:
        return
    periods = Decimal("2") if subscription.instrument.interest_frequency == "SEMESTRIEL" else Decimal("1")
    amount = (Decimal(subscription.invested_amount) * Decimal(subscription.subscription_yield) / Decimal("100") / periods).quantize(Decimal("0.01"))
    if status == "PAYE":
        transaction = executed_transaction(db, "PAIEMENT_INTERET", str(amount), subscription.instrument.currency, None, subscription.account, f"Coupon {subscription.instrument.code} - {payment_date.isoformat()}", client, datetime.combine(payment_date, datetime.min.time(), tzinfo=timezone.utc), subscription.id)
        subscription.account.balance += amount
        subscription.account.available_balance += amount
        payment = InterestPayment(subscription_id=subscription.id, payment_date=payment_date, amount=amount, status="PAYE", transaction_id=transaction.id)
    elif status == "EN_ATTENTE":
        transaction = Transaction(transaction_type="PAIEMENT_INTERET", destination_account_id=subscription.account_id, amount=amount, currency=subscription.instrument.currency, description=f"Coupon {subscription.instrument.code} - {payment_date.isoformat()}", status="PENDING_APPROVAL", is_automatic=True, subscription_id=subscription.id)
        db.add(transaction)
        db.flush()
        payment = InterestPayment(subscription_id=subscription.id, payment_date=payment_date, amount=amount, status="EN_ATTENTE", transaction_id=transaction.id)
    else:
        payment = InterestPayment(subscription_id=subscription.id, payment_date=payment_date, amount=amount, status="PLANIFIE")
    db.add(payment)


def main() -> None:
    Base.metadata.create_all(engine)
    db = SessionLocal()
    try:
        marie = find_or_create_client(db, "marie.jean@demo.profin.ht", client_type="INDIVIDUEL", risk_profile="MODERE", first_name="Marie", last_name="Jean", birth_date=date(1990, 3, 20), identity_number="CIN-DEMO-001", profession="Directrice commerciale", income_source="Salaire et placements", income=Decimal("78000"), address="45 Rue Grégoire", city="Pétion-Ville", postal_code="HT6140", phone="+509 3812 5678")
        caribe = find_or_create_client(db, "caribe.invest@demo.profin.ht", client_type="INSTITUTIONNEL", risk_profile="AGRESSIF", company_name="Caribe Investissements S.A.", registration_number="RC-DEMO-2024-014", legal_form="Société anonyme", sector="Gestion d'actifs", revenue=Decimal("12500000"), representative="Lucien Pierre", address="12 Boulevard Toussaint Louverture", city="Port-au-Prince", postal_code="HT6110", phone="+509 3700 1122")
        paul = find_or_create_client(db, "paul.observer@demo.profin.ht", client_type="INDIVIDUEL", risk_profile="CONSERVATEUR", first_name="Paul", last_name="Joseph", birth_date=date(1986, 7, 11), identity_number="CIN-DEMO-003", profession="Architecte", income_source="Honoraires professionnels", income=Decimal("54000"), address="8 Rue Lambert", city="Pétion-Ville", postal_code="HT6140", phone="+509 3622 8899")

        sophie = find_or_create_client(db, "sophie.checker@demo.profin.ht", client_type="INDIVIDUEL", risk_profile="MODERE", first_name="Sophie", last_name="Laurent", birth_date=date(1988, 9, 14), identity_number="CIN-DEMO-004", profession="Administratrice de portefeuille", income_source="Salaire et placements", income=Decimal("96000"), address="22 Rue Rigaud", city="Petion-Ville", postal_code="HT6140", phone="+509 3844 7711")
        nadia = find_or_create_client(db, "nadia.checker@demo.profin.ht", client_type="INDIVIDUEL", risk_profile="MODERE", first_name="Nadia", last_name="Bernard", birth_date=date(1985, 4, 5), identity_number="CIN-DEMO-005", profession="Responsable opérations", income_source="Salaire", income=Decimal("88000"), address="17 Rue Panaméricaine", city="Pétion-Ville", postal_code="HT6140", phone="+509 3666 4422")
        nexa = find_or_create_client(db, "nexa.patrimoine@demo.profin.ht", client_type="INSTITUTIONNEL", risk_profile="MODERE", company_name="Nexa Patrimoine S.A.", registration_number="RC-DEMO-2025-031", legal_form="Société anonyme", sector="Gestion de trésorerie", revenue=Decimal("8400000"), representative="Élodie Saint-Fleur", address="31 Avenue Lamartinière", city="Delmas", postal_code="HT6120", phone="+509 3990 2244")
        julien = find_or_create_client(db, "julien.bernard@demo.profin.ht", client_type="INDIVIDUEL", risk_profile="CONSERVATEUR", first_name="Julien", last_name="Bernard", birth_date=date(1979, 11, 2), identity_number="CIN-DEMO-006", profession="Ingenieur civil", income_source="Salaire et epargne", income=Decimal("69000"), address="14 Rue Panamericaine", city="Petion-Ville", postal_code="HT6140", phone="+509 3711 2034")
        aline = find_or_create_client(db, "aline.michel@demo.profin.ht", client_type="INDIVIDUEL", risk_profile="MODERE", first_name="Aline", last_name="Michel", birth_date=date(1993, 2, 18), identity_number="CIN-DEMO-007", profession="Medecin", income_source="Revenus professionnels", income=Decimal("82000"), address="9 Rue Capois", city="Port-au-Prince", postal_code="HT6110", phone="+509 3888 1045")
        marie_usd = account(db, "INV-2026-00001", marie, "USD", "35000")
        marie_htg = account(db, "SVG-2026-00002", marie, "HTG", "420000", "EPARGNE")
        shared_htg = account(db, "JNT-2026-00003", marie, "HTG", "185000", "INVESTISSEMENT")
        grant_role(db, shared_htg, paul, "OBSERVATEUR")
        grant_role(db, shared_htg, sophie, "MANDATAIRE")
        caribe_usd = account(db, "INV-2026-00004", caribe, "USD", "150000")
        grant_role(db, caribe_usd, sophie, "MANDATAIRE")
        grant_role(db, caribe_usd, paul, "OBSERVATEUR")
        grant_role(db, marie_usd, sophie, "MANDATAIRE")
        grant_role(db, marie_usd, nadia, "MANDATAIRE")
        nexa_usd = account(db, "INV-2026-00005", nexa, "USD", "180000")
        nexa_htg = account(db, "TRE-2026-00006", nexa, "HTG", "950000", "TRESORERIE")
        grant_role(db, nexa_usd, sophie, "MANDATAIRE")
        grant_role(db, nexa_usd, paul, "OBSERVATEUR")
        grant_role(db, nexa_htg, nadia, "MANDATAIRE")
        julien_usd = account(db, "INV-2026-00007", julien, "USD", "60000")
        aline_usd = account(db, "INV-2026-00008", aline, "USD", "50000")
        grant_role(db, julien_usd, sophie, "MANDATAIRE")
        grant_role(db, julien_usd, paul, "OBSERVATEUR")
        grant_role(db, aline_usd, sophie, "MANDATAIRE")

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

        maturity_bond = instrument(db, "OBL-BRH-2026", bond_type, name="Obligation BRH 2026 - Serie B", description="Obligation souveraine a echeance proche.", issuer="Banque de la Republique d'Haiti", annual_yield=Decimal("4.7500"), issue_date=date(2025, 9, 15), maturity_date=date(2026, 10, 15), nominal_value=Decimal("1000"), minimum_amount=Decimal("5000"), currency="USD", interest_frequency="ANNUEL", status="DISPONIBLE")
        caribbean_bond = instrument(db, "OBL-CARAIBES-2029", bond_type, name="Obligation Caraïbes 2029", description="Financement régional avec coupon annuel et échéance intermédiaire.", issuer="Banque de développement des Caraïbes", annual_yield=Decimal("6.9000"), issue_date=date(2026, 2, 1), maturity_date=date(2029, 2, 1), nominal_value=Decimal("1000"), minimum_amount=Decimal("25000"), currency="USD", interest_frequency="ANNUEL", status="DISPONIBLE")
        brh.entry_fee_rate = Decimal("0.50")
        edh.entry_fee_rate = Decimal("0.40")
        fund.entry_fee_rate = Decimal("0.75")
        maturity_bond.entry_fee_rate = Decimal("0.50")
        caribbean_bond.entry_fee_rate = Decimal("0.60")

        if not db.scalar(select(Subscription).where(Subscription.account_id == marie_usd.id)):
            sub1 = Subscription(account=marie_usd, instrument=brh, invested_amount=Decimal("20000"), units=Decimal("20"), subscribed_at=datetime(2025, 7, 8, tzinfo=timezone.utc), effective_maturity_date=brh.maturity_date, subscription_yield=brh.annual_yield, current_value=Decimal("21100"), accrued_interest=Decimal("1100"), status="ACTIVE")
            sub2 = Subscription(account=marie_usd, instrument=edh, invested_amount=Decimal("15000"), units=Decimal("15"), subscribed_at=datetime(2026, 1, 20, tzinfo=timezone.utc), effective_maturity_date=edh.maturity_date, subscription_yield=edh.annual_yield, current_value=Decimal("15586"), accrued_interest=Decimal("586"), status="ACTIVE")
            db.add_all([sub1, sub2])
            db.flush()
            tx1 = executed_transaction(db, "SOUSCRIPTION", "20000", "USD", marie_usd, None, "Souscription Obligation BRH 2027 - Série A", marie, datetime(2025, 7, 8, tzinfo=timezone.utc), sub1.id)
            tx1.subscription_id = sub1.id
            tx2 = executed_transaction(db, "SOUSCRIPTION", "15000", "USD", marie_usd, None, "Souscription Obligation Énergie EDH 2028", marie, datetime(2026, 1, 20, tzinfo=timezone.utc), sub2.id)
            tx2.subscription_id = sub2.id
        if not db.scalar(select(Subscription).where(Subscription.account_id == marie_usd.id, Subscription.instrument_id == maturity_bond.id)):
            maturity_sub = Subscription(account=marie_usd, instrument=maturity_bond, invested_amount=Decimal("5000"), units=Decimal("5"), subscribed_at=datetime(2025, 10, 15, tzinfo=timezone.utc), effective_maturity_date=maturity_bond.maturity_date, subscription_yield=maturity_bond.annual_yield, current_value=Decimal("5075"), accrued_interest=Decimal("75"), status="ACTIVE")
            db.add(maturity_sub)
            db.flush()
            maturity_tx = executed_transaction(db, "SOUSCRIPTION", "5000", "USD", marie_usd, None, "Souscription Obligation BRH 2026 - Serie B", marie, datetime(2025, 10, 15, tzinfo=timezone.utc), maturity_sub.id)
            maturity_tx.subscription_id = maturity_sub.id
        if not db.scalar(select(Subscription).where(Subscription.account_id == caribe_usd.id)):
            sub3 = Subscription(account=caribe_usd, instrument=fund, invested_amount=Decimal("100000"), units=Decimal("1000"), subscribed_at=datetime(2026, 2, 3, tzinfo=timezone.utc), effective_maturity_date=fund.maturity_date, subscription_yield=fund.annual_yield, current_value=Decimal("104700"), accrued_interest=Decimal("4700"), status="ACTIVE")
            db.add(sub3)
            db.flush()
            tx3 = executed_transaction(db, "SOUSCRIPTION", "100000", "USD", caribe_usd, None, "Souscription Fonds Croissance Caraïbes", caribe, datetime(2026, 2, 3, tzinfo=timezone.utc), sub3.id)
            tx3.subscription_id = sub3.id
        if not db.scalar(select(Subscription).where(Subscription.account_id == nexa_usd.id, Subscription.instrument_id == caribbean_bond.id)):
            nexa_subscription = Subscription(account=nexa_usd, instrument=caribbean_bond, invested_amount=Decimal("75000"), units=Decimal("75"), subscribed_at=datetime(2026, 2, 12, tzinfo=timezone.utc), effective_maturity_date=caribbean_bond.maturity_date, subscription_yield=caribbean_bond.annual_yield, current_value=Decimal("76200"), accrued_interest=Decimal("1200"), status="ACTIVE")
            db.add(nexa_subscription)
            db.flush()
            nexa_subscription_tx = executed_transaction(db, "SOUSCRIPTION", "75000", "USD", nexa_usd, None, "Souscription Obligation Caraïbes 2029", nexa, datetime(2026, 2, 12, tzinfo=timezone.utc), nexa_subscription.id)
            nexa_subscription_tx.subscription_id = nexa_subscription.id
            nexa_usd.balance -= Decimal("75000")
            nexa_usd.available_balance -= Decimal("75000")
        if not db.scalar(select(Subscription).where(Subscription.account_id == julien_usd.id, Subscription.instrument_id == brh.id)):
            julien_subscription = Subscription(account=julien_usd, instrument=brh, invested_amount=Decimal("10000"), units=Decimal("10"), subscribed_at=datetime(2026, 3, 8, tzinfo=timezone.utc), effective_maturity_date=brh.maturity_date, subscription_yield=brh.annual_yield, current_value=Decimal("10250"), accrued_interest=Decimal("250"), status="ACTIVE")
            db.add(julien_subscription)
            db.flush()
            julien_subscription_tx = executed_transaction(db, "SOUSCRIPTION", "10000", "USD", julien_usd, None, "Souscription Obligation BRH 2027 - Julien Bernard", julien, datetime(2026, 3, 8, tzinfo=timezone.utc), julien_subscription.id)
            julien_subscription_tx.subscription_id = julien_subscription.id
            julien_usd.balance -= Decimal("10000")
            julien_usd.available_balance -= Decimal("10000")
        if not db.scalar(select(Subscription).where(Subscription.account_id == aline_usd.id, Subscription.instrument_id == edh.id)):
            aline_subscription = Subscription(account=aline_usd, instrument=edh, invested_amount=Decimal("18000"), units=Decimal("18"), subscribed_at=datetime(2026, 4, 22, tzinfo=timezone.utc), effective_maturity_date=edh.maturity_date, subscription_yield=edh.annual_yield, current_value=Decimal("18220"), accrued_interest=Decimal("220"), status="ACTIVE")
            db.add(aline_subscription)
            db.flush()
            aline_subscription_tx = executed_transaction(db, "SOUSCRIPTION", "18000", "USD", aline_usd, None, "Souscription Obligation EDH 2028 - Aline Michel", aline, datetime(2026, 4, 22, tzinfo=timezone.utc), aline_subscription.id)
            aline_subscription_tx.subscription_id = aline_subscription.id
            aline_usd.balance -= Decimal("18000")
            aline_usd.available_balance -= Decimal("18000")
        for seeded_subscription in db.scalars(select(Subscription).where(Subscription.account_id.in_([marie_usd.id, caribe_usd.id]))).all():
            if not seeded_subscription.fee_amount:
                seeded_subscription.fee_amount = (Decimal(seeded_subscription.invested_amount) * Decimal(seeded_subscription.instrument.entry_fee_rate) / Decimal("100")).quantize(Decimal("0.01"))
        nexa_subscription = db.scalar(select(Subscription).where(Subscription.account_id == nexa_usd.id, Subscription.instrument_id == caribbean_bond.id))
        if nexa_subscription and not nexa_subscription.fee_amount:
            nexa_subscription.fee_amount = (Decimal(nexa_subscription.invested_amount) * Decimal(nexa_subscription.instrument.entry_fee_rate) / Decimal("100")).quantize(Decimal("0.01"))
        julien_subscription = db.scalar(select(Subscription).where(Subscription.account_id == julien_usd.id, Subscription.instrument_id == brh.id))
        if julien_subscription and not julien_subscription.fee_amount:
            julien_subscription.fee_amount = (Decimal(julien_subscription.invested_amount) * Decimal(julien_subscription.instrument.entry_fee_rate) / Decimal("100")).quantize(Decimal("0.01"))
        aline_subscription = db.scalar(select(Subscription).where(Subscription.account_id == aline_usd.id, Subscription.instrument_id == edh.id))
        if aline_subscription and not aline_subscription.fee_amount:
            aline_subscription.fee_amount = (Decimal(aline_subscription.invested_amount) * Decimal(aline_subscription.instrument.entry_fee_rate) / Decimal("100")).quantize(Decimal("0.01"))
        brh_subscription = db.scalar(select(Subscription).where(Subscription.account_id == marie_usd.id, Subscription.instrument_id == brh.id))
        edh_subscription = db.scalar(select(Subscription).where(Subscription.account_id == marie_usd.id, Subscription.instrument_id == edh.id))
        if brh_subscription:
            seed_coupon(db, brh_subscription, date(2026, 1, 8), "PAYE", marie)
            seed_coupon(db, brh_subscription, date(2026, 7, 8), "EN_ATTENTE", marie)
        if edh_subscription:
            seed_coupon(db, edh_subscription, date(2027, 1, 20), "PLANIFIE", marie)
        maturity_subscription = db.scalar(select(Subscription).where(Subscription.account_id == marie_usd.id, Subscription.instrument_id == maturity_bond.id))
        if maturity_subscription:
            seed_coupon(db, maturity_subscription, date(2026, 10, 15), "PLANIFIE", marie)
        if nexa_subscription:
            seed_coupon(db, nexa_subscription, date(2027, 2, 12), "PLANIFIE", nexa)
        if julien_subscription:
            seed_coupon(db, julien_subscription, date(2026, 7, 8), "EN_ATTENTE", julien)
        if aline_subscription:
            seed_coupon(db, aline_subscription, date(2027, 4, 22), "PLANIFIE", aline)

        if not db.scalar(select(Transaction).where(Transaction.description == "Dépôt initial Marie Jean")):
            executed_transaction(db, "DEPOT", "50000", "USD", None, marie_usd, "Dépôt initial Marie Jean", marie, datetime(2025, 6, 15, tzinfo=timezone.utc))
            executed_transaction(db, "DEPOT", "500000", "HTG", None, marie_htg, "Dépôt d'épargne initial", marie, datetime(2025, 6, 18, tzinfo=timezone.utc))
            executed_transaction(db, "DEPOT", "250000", "USD", None, caribe_usd, "Apport initial Caribe Investissements", caribe, datetime(2026, 1, 5, tzinfo=timezone.utc))
            executed_transaction(db, "RETRAIT", "15000", "USD", marie_usd, None, "Règlement de souscription BRH", marie, datetime(2025, 7, 8, tzinfo=timezone.utc))
            executed_transaction(db, "RETRAIT", "15000", "USD", marie_usd, None, "Règlement de souscription EDH", marie, datetime(2026, 1, 20, tzinfo=timezone.utc))
        if not db.scalar(select(Transaction).where(Transaction.description == "Apport initial Nexa Patrimoine")):
            executed_transaction(db, "DEPOT", "250000", "USD", None, nexa_usd, "Apport initial Nexa Patrimoine", nexa, datetime(2026, 1, 9, tzinfo=timezone.utc))
            executed_transaction(db, "DEPOT", "1200000", "HTG", None, nexa_htg, "Réserve de trésorerie Nexa Patrimoine", nexa, datetime(2026, 1, 10, tzinfo=timezone.utc))
        if not db.scalar(select(Transaction).where(Transaction.description == "Dépôt initial Julien Bernard")):
            executed_transaction(db, "DEPOT", "60000", "USD", None, julien_usd, "Dépôt initial Julien Bernard", julien, datetime(2026, 3, 1, tzinfo=timezone.utc))
        if not db.scalar(select(Transaction).where(Transaction.description == "Dépôt initial Aline Michel")):
            executed_transaction(db, "DEPOT", "50000", "USD", None, aline_usd, "Dépôt initial Aline Michel", aline, datetime(2026, 4, 10, tzinfo=timezone.utc))

        fee_description = "Frais de tenue de compte - février 2026"
        fee_transaction = db.scalar(select(Transaction).where(Transaction.description == fee_description))
        if not fee_transaction:
            fee_transaction = executed_transaction(db, "FRAIS", "125", "USD", marie_usd, None, fee_description, marie, datetime(2026, 2, 14, tzinfo=timezone.utc))
            marie_usd.balance -= Decimal("125")
            marie_usd.available_balance -= Decimal("125")
        reversal = db.scalar(select(Transaction).where(Transaction.reversal_of_transaction_id == fee_transaction.id)) if fee_transaction else None
        if fee_transaction and not reversal:
            TransactionService.reverse(db, fee_transaction.id, sophie.id, "Correction d'un frais appliqué par erreur")

        withdrawal_description = "Retrait de trésorerie Nexa en attente"
        if not db.scalar(select(Transaction).where(Transaction.description == withdrawal_description)):
            db.add(Transaction(transaction_type="RETRAIT", source_account_id=nexa_usd.id, amount=Decimal("25000"), currency="USD", description=withdrawal_description, status="PENDING_APPROVAL", created_by_client_id=nexa.id))
            nexa_usd.available_balance -= Decimal("25000")
        rejected_description = "Retrait Nexa refusé - justificatif requis"
        if not db.scalar(select(Transaction).where(Transaction.description == rejected_description)):
            db.add(Transaction(transaction_type="RETRAIT", source_account_id=nexa_usd.id, amount=Decimal("12000"), currency="USD", description=rejected_description, status="REJECTED", rejection_reason="Justificatif de provenance des fonds requis", created_by_client_id=nexa.id))

        if not db.scalar(select(InvestmentOrder).where(InvestmentOrder.submitted_by_client_id == marie.id, InvestmentOrder.status == "SUBMITTED")):
            order = InvestmentOrder(client_id=marie.id, account_id=marie_usd.id, instrument_id=brh.id, order_type="SOUSCRIPTION", amount=Decimal("10000"), units=Decimal("10"), currency="USD", status="SUBMITTED", client_comment="Allocation obligataire à valider", submitted_by_client_id=marie.id)
            marie_usd.available_balance -= order.amount
            db.add(order)
            db.flush()
            db.add_all([OrderWorkflowStep(order_id=order.id, step_code=code, actor_profile=profile) for code, profile in (("CONFORMITE", "CONFORMITE"), ("BACK_OFFICE", "BACK_OFFICE"), ("CHECKER", "SUPERVISEUR"))])
        if not db.scalar(select(InvestmentOrder).where(InvestmentOrder.client_id == caribe.id, InvestmentOrder.client_comment == "Réallocation en attente du contrôle back-office")):
            caribe_order = InvestmentOrder(client_id=caribe.id, account_id=caribe_usd.id, instrument_id=brh.id, order_type="SOUSCRIPTION", amount=Decimal("30000"), units=Decimal("30"), currency="USD", status="BACK_OFFICE_REVIEW", client_comment="Réallocation en attente du contrôle back-office", submitted_by_client_id=caribe.id)
            caribe_usd.available_balance -= caribe_order.amount
            db.add(caribe_order)
            db.flush()
            db.add_all([
                OrderWorkflowStep(order_id=caribe_order.id, step_code="CONFORMITE", actor_profile="CONFORMITE", status="APPROVED", completed_at=datetime(2026, 2, 15, tzinfo=timezone.utc), notes="Dossier conforme"),
                OrderWorkflowStep(order_id=caribe_order.id, step_code="BACK_OFFICE", actor_profile="BACK_OFFICE"),
                OrderWorkflowStep(order_id=caribe_order.id, step_code="CHECKER", actor_profile="SUPERVISEUR"),
            ])
        if not db.scalar(select(InvestmentOrder).where(InvestmentOrder.client_id == nexa.id, InvestmentOrder.rejection_reason == "Allocation hors mandat approuvé")):
            rejected_order = InvestmentOrder(client_id=nexa.id, account_id=nexa_usd.id, instrument_id=caribbean_bond.id, order_type="SOUSCRIPTION", amount=Decimal("50000"), units=Decimal("50"), currency="USD", status="REJECTED", rejection_reason="Allocation hors mandat approuvé", client_comment="Demande de diversification à revoir", submitted_by_client_id=nexa.id)
            db.add(rejected_order)
            db.flush()
            db.add_all([
                OrderWorkflowStep(order_id=rejected_order.id, step_code="CONFORMITE", actor_profile="CONFORMITE", status="REJECTED", completed_at=datetime(2026, 2, 13, tzinfo=timezone.utc), notes="Allocation hors mandat approuvé"),
                OrderWorkflowStep(order_id=rejected_order.id, step_code="BACK_OFFICE", actor_profile="BACK_OFFICE"),
                OrderWorkflowStep(order_id=rejected_order.id, step_code="CHECKER", actor_profile="SUPERVISEUR"),
            ])

        db.commit()
        print("Seed ProFin terminé : 8 clients, 8 comptes, 5 instruments, positions, coupons, rôles multi-utilisateurs, frais, contrepassation, rejets et parcours maker/checker.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
