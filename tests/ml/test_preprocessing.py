import tempfile
import unittest
import json
from pathlib import Path

import joblib
import pandas as pd
from xgboost import XGBClassifier

from app.ml.config import FEATURES
from app.ml.inference import predict_risk
from app.ml.preprocessing import build_preprocessor, prepare_target
from app.ml.training import evaluate_thresholds, metrics_at_threshold, select_operating_threshold


def sample_features() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "revenue": [10000, 20000, 5000000, None],
            "dti_n": [10.0, 999.0, 25.0, None],
            "loan_amnt": [1000, 2000, 3000, 4000],
            "fico_n": [700, 680, 720, 650],
            "emp_length": ["1 year", "2 years", "10+ years", None],
            "purpose": ["car", "medical", "car", "other"],
            "home_ownership_n": ["RENT", "OWN", "MORTGAGE", "RENT"],
        }
    )


class PreprocessingTests(unittest.TestCase):
    def test_sentinel_becomes_missing_and_revenue_cap_is_training_fitted(self) -> None:
        preprocessor = build_preprocessor()
        transformed = preprocessor.fit_transform(sample_features())
        cleaner = preprocessor.named_steps["cleaner"]
        cleaned = cleaner.transform(sample_features())
        self.assertTrue(pd.isna(cleaned.loc[1, "dti_n"]))
        self.assertLess(cleaner.revenue_cap_, 5000000)
        self.assertEqual(transformed.shape[0], 4)

    def test_target_transformation_validates_binary_values(self) -> None:
        self.assertEqual(prepare_target(pd.Series(["0", "1"])).tolist(), [0, 1])
        with self.assertRaises(ValueError):
            prepare_target(pd.Series([0, 2]))

    def test_feature_names_are_stable_and_match_transformed_width(self) -> None:
        preprocessor = build_preprocessor()
        transformed = preprocessor.fit_transform(sample_features())
        names = preprocessor.named_steps["columns"].get_feature_names_out()
        self.assertEqual(len(names), transformed.shape[1])
        self.assertTrue(any("revenue__revenue" == name for name in names))

    def test_single_customer_inference_returns_risk_signal(self) -> None:
        X = sample_features()
        y = pd.Series([0, 1, 0, 1])
        preprocessor = build_preprocessor()
        transformed = preprocessor.fit_transform(X, y)
        model = XGBClassifier(n_estimators=2, max_depth=2, eval_metric="logloss", random_state=42, n_jobs=1)
        model.fit(transformed, y)
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            joblib.dump(preprocessor, output / "preprocessing.joblib")
            joblib.dump(model, output / "model.joblib")
            names = preprocessor.named_steps["columns"].get_feature_names_out().tolist()
            (output / "feature_metadata.json").write_text(
                json.dumps({"transformed_feature_names": names, "selected_threshold": 0.5}), encoding="utf-8"
            )
            result = predict_risk({name: X.iloc[0][name] for name in FEATURES}, output)
        self.assertIn("risk_probability", result)
        self.assertIn("predicted_risk_class", result)
        self.assertGreaterEqual(result["risk_probability"], 0.0)
        self.assertLessEqual(result["risk_probability"], 1.0)
        self.assertIn(result["predicted_risk_class"], [0, 1])
        self.assertIn("top_risk_factors", result)
        self.assertIn("top_protective_factors", result)

    def test_threshold_metrics_include_specificity_and_select_validation_f1(self) -> None:
        target = pd.Series([0, 0, 1, 1])
        probabilities = pd.Series([0.1, 0.4, 0.35, 0.9]).to_numpy()
        metrics = metrics_at_threshold(target, probabilities, 0.35)
        self.assertEqual(metrics["confusion_matrix"], [[1, 1], [0, 2]])
        self.assertAlmostEqual(metrics["specificity"], 0.5)
        rows = evaluate_thresholds(target, probabilities, (0.35, 0.5))
        self.assertEqual(select_operating_threshold(rows)["threshold"], 0.35)
