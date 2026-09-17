"""Deterministic, auditable governance for FinMate prototype journeys."""

from app.policy.service import evaluate_policy

__all__ = ["evaluate_policy"]
