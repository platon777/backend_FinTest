from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.ai.client import AIProviderError, AIUnavailableError
from app.core.dependencies import get_current_active_client
from app.db.database import get_db
from app.models.models import Client
from app.schemas.api import AssistantChatRequest, AssistantChatResponse
from app.services.assistant_service import AssistantService, DISCLAIMER

router = APIRouter()


@router.post("/chat", response_model=AssistantChatResponse)
def chat(payload: AssistantChatRequest, client: Client = Depends(get_current_active_client), db: Session = Depends(get_db)):
    try:
        completion, context_used = AssistantService.chat(
            db,
            client.id,
            payload.message,
            [item.model_dump() for item in payload.history],
        )
    except AIUnavailableError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail={"code": "AI_UNAVAILABLE", "message": str(exc)}) from exc
    except AIProviderError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail={"code": "AI_PROVIDER_ERROR", "message": str(exc)}) from exc

    return AssistantChatResponse(answer=completion.content, disclaimer=DISCLAIMER, context_used=context_used)
