"""Ordered, deterministic FinMate prototype policy rules.

This module deliberately has no LLM, model-loading, database, or web concerns.
"""

from app.policy.config import DEFAULT_POLICY_CONFIG, POLICY_VERSION, PrototypePolicyConfig
from app.schemas.policy import PolicyDecision, PolicyEvaluationRequest, PolicyEvaluationResponse


def _missing_fields(request: PolicyEvaluationRequest, config: PrototypePolicyConfig) -> list[str]:
    status = request.required_information
    return [field for field in config.missing_information_fields if not getattr(status, field)]


def _response(
    request: PolicyEvaluationRequest,
    decision: PolicyDecision,
    reason_code: str,
    reason: str,
    actions: list[str],
    rule_ids: list[str],
    human_review_reason: str | None = None,
) -> PolicyEvaluationResponse:
    return PolicyEvaluationResponse(
        decision=decision,
        reason_code=reason_code,
        reason=reason,
        risk_signal=request.risk_signal,
        required_actions=actions,
        human_review_required=human_review_reason is not None,
        human_review_reason=human_review_reason,
        policy_version=POLICY_VERSION,
        triggered_rule_ids=rule_ids,
        audit_context={
            "journey_id": request.journey_id,
            "requested_loan_amount": request.requested_loan_amount,
            "goal": request.goal,
            "exceptional_case": request.exceptional_case,
        },
    )


def evaluate_policy(request: PolicyEvaluationRequest, config: PrototypePolicyConfig = DEFAULT_POLICY_CONFIG) -> PolicyEvaluationResponse:
    """Return exactly one governed prototype pathway using ordered rules.

    Rule precedence makes results stable and auditable: required information,
    explicit ambiguity, high risk, review band/amount, then eligible.
    """
    missing = _missing_fields(request, config)
    if missing:
        return _response(
            request, PolicyDecision.MISSING_INFORMATION, "REQUIRED_INFORMATION_MISSING",
            "Required prototype journey information is incomplete.",
            [f"Provide or verify: {field}" for field in missing], ["P001_REQUIRED_INFORMATION"],
        )
    if request.exceptional_case or request.ambiguity_reason:
        detail = request.ambiguity_reason or "An exceptional case was flagged in the supplied context."
        return _response(
            request, PolicyDecision.COMPLEX_REVIEW, "EXCEPTION_OR_AMBIGUITY_REVIEW",
            "This journey requires human review because its context is exceptional or ambiguous.",
            ["Route the journey to a human reviewer."], ["P002_EXCEPTION_OR_AMBIGUITY"], detail,
        )
    risk = request.risk_signal.risk_probability
    if risk >= config.not_suitable_risk_probability:
        return _response(
            request, PolicyDecision.NOT_SUITABLE, "RISK_SIGNAL_ABOVE_PROTOTYPE_LIMIT",
            "The prototype risk signal is above the configured suitability limit.",
            ["Do not treat this path as suitable without a separate governed recovery process."],
            ["P003_HIGH_RISK_SIGNAL"],
        )
    if risk >= config.complex_review_risk_probability or request.requested_loan_amount >= config.complex_review_requested_amount:
        review_reason = "Risk signal falls in the prototype review band." if risk >= config.complex_review_risk_probability else "Requested amount meets the prototype high-impact review threshold."
        return _response(
            request, PolicyDecision.COMPLEX_REVIEW, "RISK_OR_AMOUNT_REVIEW",
            "This journey requires human review under prototype risk/amount controls.",
            ["Route the journey to a human reviewer."], ["P004_RISK_OR_AMOUNT_REVIEW"], review_reason,
        )
    return _response(
        request, PolicyDecision.ELIGIBLE, "PROTOTYPE_POLICY_CRITERIA_MET",
        "The journey meets the configured prototype policy criteria for the next governed step.",
        ["Continue to the next governed journey step."], ["P005_PROTOTYPE_ELIGIBLE"],
    )
