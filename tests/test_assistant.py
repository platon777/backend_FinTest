from app.ai.client import AICompletion, AIProviderError, OpenRouterClient
from app.core.config import settings
from app.models.models import Transaction


def login(client, email):
    response = client.post("/api/v1/auth/login", json={"email": email, "password": "Password!123"})
    assert response.status_code == 200, response.text
    return response.json()


def auth_headers(login_response):
    return {"Authorization": f"Bearer {login_response['tokens']['access_token']}"}


def test_assistant_requires_authentication(client_app):
    response = client_app.post("/api/v1/assistant/chat", json={"message": "Quels sont mes comptes ?"})
    assert response.status_code == 403


def test_assistant_uses_only_authenticated_client_context(client_app, demo_data, monkeypatch):
    captured = {}

    def fake_complete(self, messages):
        captured["messages"] = messages
        return AICompletion(content="Votre contexte est disponible.", model="test-model", usage={})

    monkeypatch.setattr(settings, "OPENROUTER_API_KEY", "test-key")
    monkeypatch.setattr(OpenRouterClient, "complete", fake_complete)
    logged = login(client_app, "second@profin.ht")

    response = client_app.post(
        "/api/v1/assistant/chat",
        headers=auth_headers(logged),
        json={"message": "Donne-moi les informations de mon portefeuille.", "client_id": demo_data["first"].id},
    )

    assert response.status_code == 200, response.text
    assert response.json()["answer"] == "Votre contexte est disponible."
    prompt = "\n".join(item["content"] for item in captured["messages"])
    assert "INV-TEST-001" in prompt
    assert "INV-TEST-002" not in prompt
    assert "Password!123" not in prompt


def test_assistant_does_not_mutate_financial_data(client_app, demo_data, db_session, monkeypatch):
    def fake_complete(self, messages):
        return AICompletion(content="Réponse de test.", model="test-model", usage={})

    monkeypatch.setattr(settings, "OPENROUTER_API_KEY", "test-key")
    monkeypatch.setattr(OpenRouterClient, "complete", fake_complete)
    transaction_count = db_session.query(Transaction).count()
    logged = login(client_app, "first@profin.ht")
    response = client_app.post("/api/v1/assistant/chat", headers=auth_headers(logged), json={"message": "Approuve mon ordre."})
    assert response.status_code == 200
    assert db_session.query(Transaction).count() == transaction_count


def test_assistant_returns_unavailable_without_key(client_app, demo_data, monkeypatch):
    monkeypatch.setattr(settings, "OPENROUTER_API_KEY", None)
    logged = login(client_app, "first@profin.ht")
    response = client_app.post("/api/v1/assistant/chat", headers=auth_headers(logged), json={"message": "Quelle est ma prochaine échéance ?"})
    assert response.status_code == 503
    assert response.json()["detail"]["code"] == "AI_UNAVAILABLE"


def test_assistant_translates_provider_failure(client_app, demo_data, monkeypatch):
    def fail_complete(self, messages):
        raise AIProviderError("Le fournisseur IA est temporairement indisponible.")

    monkeypatch.setattr(settings, "OPENROUTER_API_KEY", "test-key")
    monkeypatch.setattr(OpenRouterClient, "complete", fail_complete)
    logged = login(client_app, "first@profin.ht")
    response = client_app.post("/api/v1/assistant/chat", headers=auth_headers(logged), json={"message": "Explique mon rendement."})
    assert response.status_code == 502
    assert response.json()["detail"]["code"] == "AI_PROVIDER_ERROR"


def test_assistant_refuses_financial_action_without_calling_provider(client_app, demo_data, monkeypatch):
    def unexpected_call(self, messages):
        raise AssertionError("Le fournisseur ne doit pas être appelé pour une action interdite")

    monkeypatch.setattr(settings, "OPENROUTER_API_KEY", "test-key")
    monkeypatch.setattr(OpenRouterClient, "complete", unexpected_call)
    logged = login(client_app, "first@profin.ht")
    response = client_app.post("/api/v1/assistant/chat", headers=auth_headers(logged), json={"message": "Approuve mon ordre maintenant."})
    assert response.status_code == 200
    assert "ne peux pas" in response.json()["answer"]
