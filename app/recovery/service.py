"""Ordered deterministic Goal Recovery rules; never an approval mechanism."""

from app.recovery.config import DEFAULT_RECOVERY_CONFIG, RECOVERY_VERSION, RecoveryConfig
from app.schemas.policy import PolicyDecision
from app.schemas.recovery import RecoveryEvaluationRequest, RecoveryEvaluationResponse, RecoveryOption, RecoveryPath, RecoveryStatus


def _response(request: RecoveryEvaluationRequest, status: RecoveryStatus, code: str, reason: str, paths: list[RecoveryOption], rules: list[str], human_reason: str | None = None) -> RecoveryEvaluationResponse:
    return RecoveryEvaluationResponse(
        recovery_status=status,
        original_goal=request.customer_goal,
        original_requested_amount=request.requested_amount,
        original_policy_decision=request.original_policy_decision,
        recovery_reason_code=code,
        recovery_reason=reason,
        available_paths=paths,
        policy_version=request.policy_version,
        recovery_version=RECOVERY_VERSION,
        human_review_required=human_reason is not None,
        human_review_reason=human_reason,
        triggered_rule_ids=rules,
        audit_context={"journey_id": request.journey_id, "policy_reason_code": request.policy_reason_code, "risk_probability": request.risk_signal.risk_probability},
    )


def _risk_factor_summary(request: RecoveryEvaluationRequest) -> str:
    if not request.top_risk_factors:
        return "the governed prototype risk signal"
    return "the explained risk factors: " + ", ".join(factor.feature for factor in request.top_risk_factors[:3])


def evaluate_recovery(request: RecoveryEvaluationRequest, config: RecoveryConfig = DEFAULT_RECOVERY_CONFIG) -> RecoveryEvaluationResponse:
    """Offer governed prototype paths only after an existing NOT_SUITABLE decision."""
    if request.original_policy_decision is PolicyDecision.COMPLEX_REVIEW or request.human_review_required:
        return _response(request, RecoveryStatus.HUMAN_REVIEW_REQUIRED, "HUMAN_REVIEW_REMAINS_PATHWAY", "The existing governed pathway requires human review; automated recovery is not generated.", [], ["R001_HUMAN_REVIEW_PRECEDENCE"], request.human_review_reason or "Existing policy evaluation requires human review.")
    if request.original_policy_decision is not PolicyDecision.NOT_SUITABLE:
        code = "GATHER_INFORMATION_FIRST" if request.original_policy_decision is PolicyDecision.MISSING_INFORMATION else "RECOVERY_NOT_REQUIRED"
        reason = "Complete the required information before considering any future path." if request.original_policy_decision is PolicyDecision.MISSING_INFORMATION else "The original governed pathway is not NOT_SUITABLE; Goal Recovery is not required."
        return _response(request, RecoveryStatus.NOT_APPLICABLE, code, reason, [], ["R002_RECOVERY_ONLY_AFTER_NOT_SUITABLE"])
    if request.customer_context.get("recovery_allowed") is False or request.policy_reason_code not in config.supported_not_suitable_reason_codes:
        return _response(request, RecoveryStatus.NO_APPLICABLE_PATH, "NO_GOVERNED_RECOVERY_PATH", "No configured prototype recovery path applies to this governed outcome.", [], ["R003_NO_CONFIGURED_PATH"])

    factor_summary = _risk_factor_summary(request)
    options: list[RecoveryOption] = []
    alternative = int(request.requested_amount * config.right_sized_ratio)
    if alternative >= config.minimum_right_sized_amount and alternative < request.requested_amount:
        options.append(RecoveryOption(
            path=RecoveryPath.RIGHT_SIZED_FINANCING, title="Right-sized prototype financing path",
            description="Consider a smaller prototype financing request while preserving the same customer goal.",
            reason="A lower requested amount may be a more proportionate future path given " + factor_summary + ".",
            requested_amount=request.requested_amount, alternative_amount=alternative,
            next_actions=["Review the smaller amount against the governed policy.", "Do not treat this as an approval or offer."],
        ))
    if request.requested_amount >= config.phased_financing_minimum_amount:
        options.append(RecoveryOption(
            path=RecoveryPath.PHASED_FINANCING, title="Phased prototype financing path",
            description="Break the goal into a smaller initial stage and reassess a later stage separately.",
            reason="Staging the request can reduce the immediate amount while retaining the original goal.",
            requested_amount=request.requested_amount, alternative_amount=alternative if alternative >= config.minimum_right_sized_amount else None,
            next_actions=["Define a smaller first stage for the same goal.", "Reassess any later stage through a new governed evaluation."],
        ))
    options.append(RecoveryOption(
        path=RecoveryPath.IMPROVE_ELIGIBILITY, title="Improve eligibility and reapply",
        description="Address relevant explained risk factors before a future prototype reapplication.",
        reason="The original path was unsuitable because of " + factor_summary + ".",
        requested_amount=request.requested_amount, alternative_amount=None,
        next_actions=["Review the explained risk factors.", f"Consider reapplication after at least {config.reapplication_waiting_period_days} days in this prototype.", "A later evaluation remains governed and is not guaranteed."],
    ))
    return _response(request, RecoveryStatus.AVAILABLE, "HIGH_RISK_PROTOTYPE_RECOVERY", "The original path was not suitable under the prototype risk rule; controlled alternatives are available for the same goal.", options, ["R004_HIGH_RISK_RECOVERY"])
