from fastapi import APIRouter

from app.ml.config import MODEL_VERSION
from app.ml.inference import predict_risk
from app.schemas.orchestration import RiskInferenceRequest, RiskInferenceResponse

router = APIRouter()


@router.post("/infer", response_model=RiskInferenceResponse)
def infer(payload: RiskInferenceRequest) -> RiskInferenceResponse:
    """Delegate to the existing ML/SHAP inference service; never makes a lending decision."""
    result = predict_risk(payload.model_dump())
    return RiskInferenceResponse(model_version=MODEL_VERSION, **result)
