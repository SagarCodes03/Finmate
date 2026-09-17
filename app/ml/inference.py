"""Single-record inference for the saved FinMate risk-signal artifact."""

from __future__ import annotations

from collections.abc import Mapping
import json
from pathlib import Path
from typing import Any

import joblib
import pandas as pd

from app.ml.config import ARTIFACT_DIR, FEATURES
from app.ml.explainability import customer_factor_explanations


def predict_risk(customer: Mapping[str, Any], artifact_dir: Path | str = ARTIFACT_DIR) -> dict[str, Any]:
    """Return a Default-risk signal, never a financing approval/rejection.

    Missing supported fields are passed to the train-fitted imputers. Extra
    fields are ignored so callers cannot silently affect the model schema.
    """
    directory = Path(artifact_dir)
    preprocessor = joblib.load(directory / "preprocessing.joblib")
    model = joblib.load(directory / "model.joblib")
    metadata = json.loads((directory / "feature_metadata.json").read_text(encoding="utf-8"))
    record = pd.DataFrame([{name: customer.get(name) for name in FEATURES}])
    transformed = preprocessor.transform(record)
    probability = float(model.predict_proba(transformed)[0, 1])
    top_risk_factors, top_protective_factors = customer_factor_explanations(
        model, transformed, metadata["transformed_feature_names"]
    )
    return {
        "risk_probability": probability,
        "predicted_risk_class": int(probability >= metadata["selected_threshold"]),
        "top_risk_factors": top_risk_factors,
        "top_protective_factors": top_protective_factors,
    }
