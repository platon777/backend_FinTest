from dataclasses import dataclass
from typing import Any

import httpx

from app.core.config import Settings


class AIUnavailableError(RuntimeError):
    """The assistant cannot be used with the current configuration."""


class AIProviderError(RuntimeError):
    """The configured provider failed without exposing its response body."""


@dataclass(frozen=True)
class AICompletion:
    content: str
    model: str
    usage: dict[str, Any]


class OpenRouterClient:
    def __init__(self, settings: Settings):
        self.settings = settings

    def complete(self, messages: list[dict[str, str]]) -> AICompletion:
        if not self.settings.AI_ENABLED or not self.settings.OPENROUTER_API_KEY:
            raise AIUnavailableError("Le service IA n'est pas configuré.")

        headers = {
            "Authorization": f"Bearer {self.settings.OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
            "HTTP-Referer": "http://localhost:3000",
            "X-OpenRouter-Title": "ProFin Prototype",
        }
        payload = {
            "model": self.settings.OPENROUTER_MODEL,
            "messages": messages,
            "temperature": 0.2,
            "max_tokens": self.settings.OPENROUTER_MAX_TOKENS,
        }

        try:
            with httpx.Client(
                base_url=self.settings.OPENROUTER_BASE_URL.rstrip("/"),
                timeout=self.settings.OPENROUTER_TIMEOUT_SECONDS,
            ) as client:
                response = client.post("/chat/completions", headers=headers, json=payload)
        except httpx.RequestError as exc:
            raise AIProviderError("Le fournisseur IA est temporairement indisponible.") from exc

        if response.status_code >= 400:
            raise AIProviderError(f"Le fournisseur IA a retourné HTTP {response.status_code}.")

        try:
            body = response.json()
            content = body["choices"][0]["message"]["content"]
        except (ValueError, KeyError, IndexError, TypeError) as exc:
            raise AIProviderError("La réponse du fournisseur IA est inexploitable.") from exc

        if not isinstance(content, str) or not content.strip():
            raise AIProviderError("Le fournisseur IA a retourné une réponse vide.")

        return AICompletion(
            content=content.strip(),
            model=str(body.get("model", self.settings.OPENROUTER_MODEL)),
            usage=body.get("usage") if isinstance(body.get("usage"), dict) else {},
        )
