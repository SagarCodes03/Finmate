"""Versioned, explicit configuration for the Phase 1 risk model."""

from pathlib import Path

RANDOM_SEED = 42
TARGET_COLUMN = "Default"
NUMERIC_FEATURES = ("revenue", "dti_n", "loan_amnt", "fico_n")
CATEGORICAL_FEATURES = ("emp_length", "purpose", "home_ownership_n")
FEATURES = NUMERIC_FEATURES + CATEGORICAL_FEATURES

DATASET_PATH = Path("data/LC_loans_granting_model_dataset.csv")
ARTIFACT_DIR = Path("artifacts/ml")
MODEL_VERSION = "finmate-default-risk-xgb-v2"
PREPROCESSING_VERSION = "finmate-preprocessing-v1"

# This value is intentionally fitted from training rows only.
REVENUE_UPPER_QUANTILE = 0.995
# A positive class is a risk-review signal, never an approval/rejection decision.
# The final operating threshold is chosen on validation data only.
THRESHOLD_GRID = tuple(round(value / 100, 2) for value in range(5, 96, 5))
DEFAULT_CLASSIFICATION_THRESHOLD = 0.5
THRESHOLD_SELECTION_OBJECTIVE = "maximize_validation_f1"
SHAP_GLOBAL_SAMPLE_SIZE = 2_000
