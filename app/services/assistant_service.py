import logging
from time import monotonic

from sqlalchemy.orm import Session

from app.ai.client import AICompletion, AIProviderError, AIUnavailableError, OpenRouterClient
from app.ai.context import build_client_context
from app.ai.prompt import CONTEXT_USED, DISCLAIMER, build_messages
from app.core.config import settings

logger = logging.getLogger(__name__)
POLICY_REFUSAL = "Je peux expliquer vos données et le parcours métier, mais je ne peux pas accéder à des secrets, produire du SQL ou approuver, rejeter ou exécuter une opération financière."


def _requires_policy_refusal(message: str) -> bool:
    normalized = " ".join(message.lower().split())
    return any(
        phrase in normalized
        for phrase in (
            "api key",
            "clé api",
            "mot de passe",
            "token",
            "sql",
            "select *",
            "drop table",
            "delete from",
            "approuve mon",
            "approuver mon",
            "valide mon",
            "valider mon",
            "rejette mon",
            "rejeter mon",
            "exécute mon",
            "exécuter mon",
        )
    )


class AssistantService:
    @staticmethod
    def chat(db: Session, client_id: int, message: str, history: list[dict[str, str]]) -> tuple[AICompletion, list[str]]:
        context = build_client_context(db, client_id)
        if _requires_policy_refusal(message):
            logger.info("assistant_policy_refusal client_id=%s", client_id)
            return AICompletion(content=POLICY_REFUSAL, model="policy", usage={}), CONTEXT_USED
        started = monotonic()
        try:
            completion = OpenRouterClient(settings).complete(build_messages(message, history, context))
        except (AIUnavailableError, AIProviderError):
            logger.info(
                "assistant_unavailable client_id=%s model=%s duration_ms=%s",
                client_id,
                settings.OPENROUTER_MODEL,
                round((monotonic() - started) * 1000),
            )
            raise

        logger.info(
            "assistant_completed client_id=%s model=%s duration_ms=%s prompt_tokens=%s completion_tokens=%s",
            client_id,
            completion.model,
            round((monotonic() - started) * 1000),
            completion.usage.get("prompt_tokens"),
            completion.usage.get("completion_tokens"),
        )
        return completion, CONTEXT_USED


__all__ = ["AssistantService", "DISCLAIMER"]
