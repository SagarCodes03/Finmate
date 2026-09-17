"""Central, explicit prototype policy configuration.

These values are demo controls only. They are not production lending rules.
"""

from dataclasses import dataclass

POLICY_VERSION = "prototype-v1"


@dataclass(frozen=True)
class PrototypePolicyConfig:
    missing_information_fields: tuple[str, ...] = (
        "customer_identity_verified",
        "business_context_verified",
        "required_documents_complete",
    )
    # Risk-signal thresholds, not lending approval thresholds.
    not_suitable_risk_probability: float = 0.50
    complex_review_risk_probability: float = 0.35
    complex_review_requested_amount: int = 500_000


DEFAULT_POLICY_CONFIG = PrototypePolicyConfig()
