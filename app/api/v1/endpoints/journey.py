"""Frontend-facing proxy for the existing n8n-governed FinMate journey."""

import httpx
from fastapi import APIRouter, HTTPException, status
from pydantic import ValidationError

from app.config import get_settings
from app.schemas.orchestration import JourneyRequest, JourneyResponse

router = APIRouter()


def run_journey(payload: JourneyRequest) -> JourneyResponse:
    """Forward a frontend request to n8n; no risk, policy, or recovery logic runs here."""
    settings = get_settings()
    try:
        response = httpx.post(
            settings.n8n_journey_webhook_url,
            json=payload.model_dump(),
            timeout=settings.n8n_request_timeout_seconds,
        )
        response.raise_for_status()
        return JourneyResponse.model_validate(response.json())
    except httpx.HTTPError as error:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="The local journey orchestrator is unavailable.",
        ) from error
    except (ValidationError, ValueError) as error:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="The journey orchestrator returned an invalid response.",
        ) from error


@router.post("", response_model=JourneyResponse)
def start_journey(payload: JourneyRequest) -> JourneyResponse:
    return run_journey(payload)
