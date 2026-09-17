"""Governed ML risk-signal utilities for FinMate.

This package deliberately produces risk signals only. It does not make lending
approvals, rejections, or policy decisions.
"""

from app.ml.inference import predict_risk

__all__ = ["predict_risk"]
