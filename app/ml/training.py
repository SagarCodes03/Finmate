"""Reproducible training, threshold selection, and evaluation for FinMate risk signals."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import average_precision_score, confusion_matrix, f1_score, precision_score, recall_score, roc_auc_score
from sklearn.model_selection import train_test_split
from xgboost import XGBClassifier

from app.ml.config import ARTIFACT_DIR, CATEGORICAL_FEATURES, DATASET_PATH, FEATURES, MODEL_VERSION, NUMERIC_FEATURES, PREPROCESSING_VERSION, RANDOM_SEED, SHAP_GLOBAL_SAMPLE_SIZE, TARGET_COLUMN, THRESHOLD_GRID, THRESHOLD_SELECTION_OBJECTIVE
from app.ml.explainability import global_feature_importance
from app.ml.preprocessing import build_preprocessor, prepare_target


def load_dataset(dataset_path: Path | str = DATASET_PATH) -> tuple[pd.DataFrame, pd.Series]:
    """Load approved features/target only; the source CSV is never altered."""
    frame = pd.read_csv(dataset_path, usecols=[*FEATURES, TARGET_COLUMN])
    return frame.loc[:, FEATURES], prepare_target(frame[TARGET_COLUMN])


def split_dataset(X: pd.DataFrame, y: pd.Series) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.Series, pd.Series, pd.Series]:
    """Create reproducible 70/15/15 stratified train/validation/test splits."""
    X_train, X_holdout, y_train, y_holdout = train_test_split(X, y, test_size=0.30, stratify=y, random_state=RANDOM_SEED)
    X_validation, X_test, y_validation, y_test = train_test_split(X_holdout, y_holdout, test_size=0.50, stratify=y_holdout, random_state=RANDOM_SEED)
    return X_train, X_validation, X_test, y_train, y_validation, y_test


def build_model(scale_pos_weight: float | None = None) -> XGBClassifier:
    options: dict[str, Any] = {} if scale_pos_weight is None else {"scale_pos_weight": scale_pos_weight}
    return XGBClassifier(
        objective="binary:logistic", eval_metric="logloss", n_estimators=300, learning_rate=0.05,
        max_depth=5, min_child_weight=5, subsample=0.8, colsample_bytree=0.9,
        random_state=RANDOM_SEED, n_jobs=4, tree_method="hist", **options,
    )


def probability_summary(probabilities: np.ndarray) -> dict[str, float]:
    """Persist a compact score distribution for threshold review."""
    quantiles = {"min": 0.0, "p01": 0.01, "p05": 0.05, "p10": 0.10, "p25": 0.25, "p50": 0.50, "p75": 0.75, "p90": 0.90, "p95": 0.95, "p99": 0.99, "max": 1.0}
    return {label: float(np.quantile(probabilities, quantile)) for label, quantile in quantiles.items()} | {"mean": float(np.mean(probabilities))}


def metrics_at_threshold(y: pd.Series, probabilities: np.ndarray, threshold: float) -> dict[str, Any]:
    predictions = (probabilities >= threshold).astype(int)
    matrix = confusion_matrix(y, predictions, labels=[0, 1])
    tn, fp, fn, tp = matrix.ravel()
    return {
        "threshold": threshold,
        "precision": float(precision_score(y, predictions, zero_division=0)),
        "recall": float(recall_score(y, predictions, zero_division=0)),
        "f1": float(f1_score(y, predictions, zero_division=0)),
        "specificity": float(tn / (tn + fp)) if tn + fp else 0.0,
        "roc_auc": float(roc_auc_score(y, probabilities)),
        "pr_auc": float(average_precision_score(y, probabilities)),
        "confusion_matrix": matrix.tolist(),
    }


def evaluate_thresholds(y: pd.Series, probabilities: np.ndarray, thresholds: tuple[float, ...] = THRESHOLD_GRID) -> list[dict[str, Any]]:
    return [metrics_at_threshold(y, probabilities, threshold) for threshold in thresholds]


def select_operating_threshold(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Choose validation-only maximum F1; ties prefer precision then higher threshold.

    F1 balances detection recall with the volume of cases flagged for risk review.
    It is an ML operating point, never a lending decision policy.
    """
    return max(rows, key=lambda row: (row["f1"], row["precision"], row["threshold"]))


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _fit_candidate(X_train: Any, y_train: pd.Series, X_validation: Any, y_validation: pd.Series, scale_pos_weight: float | None) -> tuple[XGBClassifier, np.ndarray]:
    model = build_model(scale_pos_weight)
    model.fit(X_train, y_train, eval_set=[(X_validation, y_validation)], verbose=False)
    return model, model.predict_proba(X_validation)[:, 1]


def train_and_evaluate(dataset_path: Path | str = DATASET_PATH, artifact_dir: Path | str = ARTIFACT_DIR) -> dict[str, Any]:
    """Select model/threshold on validation only, then evaluate held-out test once."""
    source_path, output_dir = Path(dataset_path), Path(artifact_dir)
    X, y = load_dataset(source_path)
    X_train, X_validation, X_test, y_train, y_validation, y_test = split_dataset(X, y)
    preprocessor = build_preprocessor()
    X_train_processed = preprocessor.fit_transform(X_train, y_train)
    X_validation_processed = preprocessor.transform(X_validation)
    X_test_processed = preprocessor.transform(X_test)

    baseline, baseline_probabilities = _fit_candidate(X_train_processed, y_train, X_validation_processed, y_validation, None)
    positive_weight = float((y_train == 0).sum() / (y_train == 1).sum())
    weighted, weighted_probabilities = _fit_candidate(X_train_processed, y_train, X_validation_processed, y_validation, positive_weight)

    candidates: list[dict[str, Any]] = []
    for name, model, probabilities, weight in [("baseline", baseline, baseline_probabilities, None), ("class_weighted", weighted, weighted_probabilities, positive_weight)]:
        threshold_rows = evaluate_thresholds(y_validation, probabilities)
        candidates.append({"name": name, "model": model, "probabilities": probabilities, "scale_pos_weight": weight, "threshold_rows": threshold_rows, "selected": select_operating_threshold(threshold_rows)})

    # Preserve the baseline unless weighting improves the documented validation objective.
    selected_candidate = max(candidates, key=lambda item: (item["selected"]["f1"], item["selected"]["precision"], item["selected"]["threshold"]))
    selected_threshold = selected_candidate["selected"]["threshold"]
    final_model = selected_candidate["model"]
    test_probabilities = final_model.predict_proba(X_test_processed)[:, 1]
    final_test_metrics = metrics_at_threshold(y_test, test_probabilities, selected_threshold)

    feature_names = preprocessor.named_steps["columns"].get_feature_names_out().tolist()
    shap_sample = X_validation_processed[:min(SHAP_GLOBAL_SAMPLE_SIZE, X_validation_processed.shape[0])]
    shap_importance = global_feature_importance(final_model, shap_sample, feature_names)
    metrics = {
        "model_version": MODEL_VERSION, "preprocessing_version": PREPROCESSING_VERSION,
        "dataset": {"path": str(source_path), "sha256": _sha256(source_path)}, "random_seed": RANDOM_SEED,
        "split_sizes": {"train": len(y_train), "validation": len(y_validation), "test": len(y_test)},
        "threshold_selection": {"objective": THRESHOLD_SELECTION_OBJECTIVE, "selection_data": "validation_only"},
        "validation_probability_distribution": {candidate["name"]: probability_summary(candidate["probabilities"]) for candidate in candidates},
        "validation_candidate_comparison": [{"name": candidate["name"], "scale_pos_weight": candidate["scale_pos_weight"], "selected": candidate["selected"]} for candidate in candidates],
        "validation_threshold_metrics": {candidate["name"]: candidate["threshold_rows"] for candidate in candidates},
        "selected_candidate": selected_candidate["name"], "selected_threshold": selected_threshold,
        "test_final_evaluation": final_test_metrics,
        "test_threshold_independent": {"roc_auc": final_test_metrics["roc_auc"], "pr_auc": final_test_metrics["pr_auc"]},
    }
    metadata = {
        "model_version": MODEL_VERSION, "preprocessing_version": PREPROCESSING_VERSION, "target": TARGET_COLUMN,
        "numeric_features": list(NUMERIC_FEATURES), "categorical_features": list(CATEGORICAL_FEATURES),
        "transformed_feature_names": feature_names, "selected_threshold": selected_threshold,
        "threshold_selection_objective": THRESHOLD_SELECTION_OBJECTIVE,
        "dti_sentinel": {"value": 999, "treatment": "convert_to_missing_then_training_median_imputation"},
        "revenue_treatment": {"upper_quantile": preprocessor.named_steps["cleaner"].revenue_upper_quantile, "training_fitted_cap": preprocessor.named_steps["cleaner"].revenue_cap_, "transform": "log1p_after_imputation"},
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    joblib.dump(final_model, output_dir / "model.joblib")
    joblib.dump(preprocessor, output_dir / "preprocessing.joblib")
    (output_dir / "feature_metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    (output_dir / "metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    (output_dir / "shap_global_importance.json").write_text(json.dumps(shap_importance, indent=2), encoding="utf-8")
    return metrics
