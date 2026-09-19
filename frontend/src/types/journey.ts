export type GovernedDecision =
  | "ELIGIBLE"
  | "MISSING_INFORMATION"
  | "NOT_SUITABLE"
  | "COMPLEX_REVIEW";

export interface JourneyRequest {
  journey_id: string;
  customer_id: string;
  customer_goal: string;
  requested_amount: number;
}

export interface ShapFactor {
  feature: string;
  shap_value: number;
}

export interface RiskSignal {
  risk_probability: number;
  predicted_risk_class: number;
  model_version: string;
}

export interface JourneyRiskSignal extends RiskSignal {
  top_risk_factors: ShapFactor[];
  top_protective_factors: ShapFactor[];
  prototype_only: boolean;
  shap_source?: string | null;
  is_simulated_journey: boolean;
}

export interface PolicyDecision {
  decision: GovernedDecision;
  reason_code: string;
  reason: string;
  risk_signal: RiskSignal;
  required_actions: string[];
  human_review_required: boolean;
  human_review_reason?: string | null;
  policy_version: string;
  triggered_rule_ids: string[];
  audit_context: AuditMetadata;
}

export type RecoveryStatus =
  | "AVAILABLE"
  | "NOT_APPLICABLE"
  | "HUMAN_REVIEW_REQUIRED"
  | "NO_APPLICABLE_PATH";

export interface RecoveryPath {
  path: "RIGHT_SIZED_FINANCING" | "PHASED_FINANCING" | "IMPROVE_ELIGIBILITY";
  title: string;
  description: string;
  reason: string;
  requested_amount: number;
  alternative_amount?: number | null;
  next_actions: string[];
  timeline_days?: number | null;
  prototype_only: boolean;
}

export interface GoalRecovery {
  recovery_status: RecoveryStatus;
  original_goal: string;
  original_requested_amount: number;
  original_policy_decision: GovernedDecision;
  recovery_reason_code: string;
  recovery_reason: string;
  available_paths: RecoveryPath[];
  policy_version: string;
  recovery_version: string;
  human_review_required: boolean;
  human_review_reason?: string | null;
  triggered_rule_ids: string[];
  audit_context: AuditMetadata;
}

export type AuditValue = string | number | boolean | null;
export type AuditMetadata = Record<string, AuditValue>;

export interface JourneyResponse {
  journey_id: string;
  customer_goal: string;
  requested_amount: number;
  risk_signal: JourneyRiskSignal;
  policy_decision: PolicyDecision;
  goal_recovery?: GoalRecovery | null;
  next_action: string;
  audit: AuditMetadata;
}

export type SimulatedVerificationField = "customer_identity_verified" | "required_documents_complete";

export interface JourneyReassessmentResponse {
  original_journey_id: string;
  reassessment: JourneyResponse;
  is_simulated: boolean;
}

export interface RecoveryCustomerContext {
  annualRevenue?: number;
  monthlyObligations?: number;
  creditScore?: number;
}

export interface CustomCustomerRequest {
  name: string; business_type: string; customer_goal: string; requested_amount: number;
  monthly_revenue: number; monthly_obligations: number; fico_n: number; emp_length: string;
  home_ownership_n: "RENT" | "OWN" | "MORTGAGE" | "OTHER"; business_tenure_years: number; purpose: string;
  customer_identity_verified: boolean; required_documents_complete: boolean;
  existing_customer_relationship: boolean; recovery_allowed: boolean;
}

export interface CustomCustomerResponse {
  customer_id: string; name: string; business_type: string; customer_goal: string;
  requested_amount: number; dti_n: number; is_simulated: boolean;
}
