"""Server-side, governed Gemini assistant endpoint."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.orchestration import AssistantChatRequest, AssistantChatResponse, AssistantDiagnosticResponse
from app.services.assistant import AssistantConfigurationError, AssistantProviderError, FinMateAssistant

router = APIRouter()


@router.post("/diagnostic", response_model=AssistantDiagnosticResponse)
def diagnostic(db: Session = Depends(get_db)) -> AssistantDiagnosticResponse:
    """Run a minimal, secret-safe Gemini configuration and connectivity check."""
    return FinMateAssistant(db).diagnose_provider()


@router.post("/chat", response_model=AssistantChatResponse)
def chat(payload: AssistantChatRequest, db: Session = Depends(get_db)) -> AssistantChatResponse:
    try:
        return FinMateAssistant(db).chat(payload)
    except AssistantConfigurationError as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="The FinMate AI Assistant is not configured. Set GEMINI_API_KEY on the backend.",
        ) from error
    except AssistantProviderError as error:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(error),
        ) from error
