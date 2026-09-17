"""Leakage-safe preprocessing for FinMate's structured risk signal."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import FunctionTransformer, OneHotEncoder

from app.ml.config import CATEGORICAL_FEATURES, FEATURES, NUMERIC_FEATURES, REVENUE_UPPER_QUANTILE, TARGET_COLUMN


class FinancialDataCleaner(BaseEstimator, TransformerMixin):
    """Apply train-fitted revenue treatment and deterministic input cleaning.

    `dti_n == 999` is treated as a sentinel for an unavailable/suspicious DTI
    value and converted to ``NaN``. The downstream median imputer is fitted on
    training data only. Revenue is capped at a training-set quantile, then
    log-transformed after imputation to reduce the influence of extreme values.
    """

    def __init__(self, revenue_upper_quantile: float = REVENUE_UPPER_QUANTILE) -> None:
        self.revenue_upper_quantile = revenue_upper_quantile

    def fit(self, X: pd.DataFrame, y: Any = None) -> "FinancialDataCleaner":
        frame = self._validate_and_copy(X)
        revenue = pd.to_numeric(frame["revenue"], errors="coerce")
        self.revenue_cap_ = float(revenue.quantile(self.revenue_upper_quantile))
        return self

    def transform(self, X: pd.DataFrame) -> pd.DataFrame:
        frame = self._validate_and_copy(X)
        for column in NUMERIC_FEATURES:
            frame[column] = pd.to_numeric(frame[column], errors="coerce")
        frame["dti_n"] = frame["dti_n"].replace(999, np.nan)
        frame["revenue"] = frame["revenue"].clip(upper=self.revenue_cap_)
        for column in CATEGORICAL_FEATURES:
            frame[column] = frame[column].replace("", np.nan).astype("object")
        return frame.loc[:, FEATURES]

    @staticmethod
    def _validate_and_copy(X: pd.DataFrame) -> pd.DataFrame:
        if not isinstance(X, pd.DataFrame):
            raise TypeError("Expected a pandas DataFrame with FinMate feature columns")
        missing = set(FEATURES).difference(X.columns)
        if missing:
            raise ValueError(f"Missing required feature columns: {sorted(missing)}")
        return X.copy()


def _make_one_hot_encoder() -> OneHotEncoder:
    # sparse_output was introduced in scikit-learn 1.2; support older local environments.
    try:
        return OneHotEncoder(handle_unknown="ignore", sparse_output=True)
    except TypeError:
        return OneHotEncoder(handle_unknown="ignore", sparse=True)


def build_preprocessor() -> Pipeline:
    """Return an unfitted pipeline. Call ``fit`` only on the training split."""
    revenue_pipeline = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median")),
            ("log_revenue", FunctionTransformer(np.log1p, feature_names_out="one-to-one")),
        ]
    )
    other_numeric_pipeline = Pipeline(steps=[("imputer", SimpleImputer(strategy="median"))])
    categorical_pipeline = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("one_hot", _make_one_hot_encoder()),
        ]
    )
    columns = ColumnTransformer(
        transformers=[
            ("revenue", revenue_pipeline, ["revenue"]),
            ("numeric", other_numeric_pipeline, ["dti_n", "loan_amnt", "fico_n"]),
            ("categorical", categorical_pipeline, list(CATEGORICAL_FEATURES)),
        ],
        remainder="drop",
    )
    return Pipeline(steps=[("cleaner", FinancialDataCleaner()), ("columns", columns)])


def prepare_target(values: pd.Series) -> pd.Series:
    """Validate and return the binary Default target as integer labels."""
    target = pd.to_numeric(values, errors="raise")
    if target.isna().any() or not target.isin([0, 1]).all():
        raise ValueError(f"{TARGET_COLUMN} must contain only binary values 0 and 1")
    return target.astype("int8")
