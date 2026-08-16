from datetime import date, datetime, timedelta, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.core.config import settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_access_token,
    hash_password,
    hash_refresh_token,
    verify_password,
)
from app.models.models import (
    Account,
    AccountRole,
    Client,
    ClientAddress,
    ClientAuthentication,
    ClientContact,
    IndividualProfile,
    InstitutionalProfile,
    RefreshToken,
)


class AuthService:
    @staticmethod
    def register_client(db: Session, data: Any) -> Client:
        email = str(data.email).lower()
        if db.scalar(select(ClientAuthentication).where(ClientAuthentication.email == email)):
            raise ValueError("Cette adresse email est déjà utilisée")

        client_type = data.client_type.upper()
        if client_type == "INDIVIDUEL":
            required = {"prenom": data.prenom, "nom": data.nom, "date_naissance": data.date_naissance, "numero_piece_identite": data.numero_piece_identite}
            if any(value in (None, "") for value in required.values()):
                raise ValueError("Les informations du client individuel sont obligatoires")
            birth_date = date.fromisoformat(data.date_naissance)
        else:
            required = {"nom_entreprise": data.nom_entreprise, "numero_registre_commerce": data.numero_registre_commerce, "nom_representant_legal": data.nom_representant_legal}
            if any(value in (None, "") for value in required.values()):
                raise ValueError("Les informations du client institutionnel sont obligatoires")
            birth_date = None

        client = Client(client_type=client_type, risk_profile=data.profil_risque or "MODERE", status="ACTIF")
        client.auth = ClientAuthentication(email=email, password_hash=hash_password(data.password), is_active=True)
        if client_type == "INDIVIDUEL":
            client.individual_profile = IndividualProfile(
                first_name=data.prenom, last_name=data.nom, birth_date=birth_date,
                nationality=data.nationalite, identity_type=data.type_piece_identite,
                identity_number=data.numero_piece_identite, profession=data.profession,
                income_source=data.source_revenus, estimated_annual_income=data.revenu_annuel_estime,
            )
        else:
            client.institutional_profile = InstitutionalProfile(
                company_name=data.nom_entreprise, registration_number=data.numero_registre_commerce,
                legal_form=data.forme_juridique, sector=data.secteur,
                annual_revenue=data.chiffre_affaires_annuel, legal_representative=data.nom_representant_legal,
            )

        if data.adresse_ligne1:
            client.addresses.append(ClientAddress(line1=data.adresse_ligne1, city=data.ville or "Port-au-Prince", postal_code=data.code_postal, country=data.pays or "Haïti", is_primary=True))
        if data.telephone:
            client.contacts.append(ClientContact(contact_type="TELEPHONE", value=data.telephone, is_primary=True, is_verified=False))

        db.add(client)
        db.flush()
        account = Account(account_number=f"INV-{datetime.now().year}-{client.id:05d}", account_type="INVESTISSEMENT", currency=data.devise or "USD", balance=0, available_balance=0, status="ACTIF")
        account.roles.append(AccountRole(client=client, role="TITULAIRE_PRINCIPAL", is_active=True))
        db.add(account)
        db.commit()
        db.refresh(client)
        return client

    @staticmethod
    def issue_tokens(db: Session, client: Client, ip_address: str | None = None) -> dict[str, str | int]:
        access_token = create_access_token(client.id)
        raw_refresh = create_refresh_token()
        db.add(RefreshToken(
            client_id=client.id,
            token_hash=hash_refresh_token(raw_refresh),
            expires_at=datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
            ip_address=ip_address,
        ))
        return {"access_token": access_token, "refresh_token": raw_refresh, "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60}

    @staticmethod
    def login(db: Session, email: str, password: str, ip_address: str | None = None) -> dict[str, Any]:
        auth = db.scalar(select(ClientAuthentication).where(ClientAuthentication.email == str(email).lower()).options(joinedload(ClientAuthentication.client)))
        if not auth or not auth.is_active or not verify_password(password, auth.password_hash):
            raise ValueError("Email ou mot de passe incorrect")
        if auth.client.status != "ACTIF":
            raise ValueError("Le client n'est pas actif")
        auth.last_login_at = datetime.now(timezone.utc)
        tokens = AuthService.issue_tokens(db, auth.client, ip_address)
        db.commit()
        return {"client": auth.client, **tokens}

    @staticmethod
    def refresh(db: Session, raw_token: str, ip_address: str | None = None) -> dict[str, Any]:
        stored = db.scalar(select(RefreshToken).where(RefreshToken.token_hash == hash_refresh_token(raw_token)).options(joinedload(RefreshToken.client)))
        now = datetime.now(timezone.utc)
        expires_at = stored.expires_at.replace(tzinfo=timezone.utc) if stored and stored.expires_at.tzinfo is None else stored.expires_at if stored else None
        if not stored or stored.revoked_at or expires_at <= now or stored.client.status != "ACTIF":
            raise ValueError("Refresh token invalide ou expiré")
        stored.revoked_at = now
        tokens = AuthService.issue_tokens(db, stored.client, ip_address)
        db.commit()
        return {"client": stored.client, **tokens}

    @staticmethod
    def logout(db: Session, raw_token: str) -> None:
        stored = db.scalar(select(RefreshToken).where(RefreshToken.token_hash == hash_refresh_token(raw_token)))
        if stored and not stored.revoked_at:
            stored.revoked_at = datetime.now(timezone.utc)
            db.commit()

    @staticmethod
    def get_client_from_access_token(db: Session, token: str) -> Client | None:
        payload = decode_access_token(token)
        if not payload:
            return None
        try:
            client_id = int(payload["sub"])
        except (KeyError, TypeError, ValueError):
            return None
        return db.scalar(select(Client).where(Client.id == client_id).options(joinedload(Client.auth), joinedload(Client.individual_profile), joinedload(Client.institutional_profile)))
