"""Explicit, auditable prototype-only Goal Recovery rules."""

from dataclasses import dataclass

RECOVERY_VERSION = "prototype-recovery-v1"


@dataclass(frozen=True)
class RecoveryConfig:
    right_sized_ratio: float = 0.50
    minimum_right_sized_amount: int = 50_000
    phased_financing_minimum_amount: int = 100_000
    reapplication_waiting_period_days: int = 90
    supported_not_suitable_reason_codes: tuple[str, ...] = (
        "RISK_SIGNAL_ABOVE_PROTOTYPE_LIMIT",
    )


DEFAULT_RECOVERY_CONFIG = RecoveryConfig()
