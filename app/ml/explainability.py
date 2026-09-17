"""SHAP explanations tied to the exact saved XGBoost risk model and features."""

from __future__ import annotations

from typing import Any

import numpy as np
import shap


def _positive_class_values(explainer: shap.TreeExplainer, transformed_features: Any) -> np.ndarray:
    values = explainer.shap_values(transformed_features)
    if isinstance(values, list):
        values = values[1]
    values = np.asarray(values)
    if values.ndim == 3:
        values = values[:, :, 1]
    return values


def build_explainer(model: Any) -> shap.TreeExplainer:
    """Build a tree explainer from the actual saved XGBoost model."""
    return shap.TreeExplainer(model)


def global_feature_importance(model: Any, transformed_features: Any, feature_names: list[str]) -> list[dict[str, float | str]]:
    """Rank transformed features by mean absolute SHAP value."""
    values = _positive_class_values(build_explainer(model), transformed_features)
    importance = np.abs(values).mean(axis=0)
    ranked = sorted(zip(feature_names, importance, strict=True), key=lambda item: item[1], reverse=True)
    return [{"feature": name, "mean_abs_shap": float(value)} for name, value in ranked]


def customer_factor_explanations(model: Any, transformed_features: Any, feature_names: list[str], limit: int = 3) -> tuple[list[dict[str, float | str]], list[dict[str, float | str]]]:
    """Return strongest positive and negative SHAP contributions for one record.

    Positive SHAP values increase the model's Default-risk signal; negative
    values decrease it. They are model explanations, not lending decisions.
    """
    values = _positive_class_values(build_explainer(model), transformed_features)
    row = values[0]
    pairs = [(feature_names[index], float(value)) for index, value in enumerate(row)]
    risk = sorted((pair for pair in pairs if pair[1] > 0), key=lambda item: item[1], reverse=True)[:limit]
    protective = sorted((pair for pair in pairs if pair[1] < 0), key=lambda item: item[1])[:limit]
    return (
        [{"feature": name, "shap_value": value} for name, value in risk],
        [{"feature": name, "shap_value": value} for name, value in protective],
    )
