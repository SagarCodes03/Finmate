import type { CustomCustomerRequest, CustomCustomerResponse, JourneyReassessmentResponse, JourneyRequest, JourneyResponse, RecoveryCustomerContext, RecoveryPersonalizationResponse, SimulatedVerificationField } from "../types/journey";

const apiBaseUrl = (import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000").replace(/\/$/, "");

export class JourneyApiError extends Error {
  constructor(
    message: string,
    public readonly kind: "unavailable" | "invalid_response" | "error"
  ) {
    super(message);
  }
}

function isJourneyResponse(value: unknown): value is JourneyResponse {
  if (!value || typeof value !== "object") return false;
  const response = value as Partial<JourneyResponse>;
  const decision = response.policy_decision?.decision;
  return (
    typeof response.journey_id === "string" &&
    typeof response.customer_goal === "string" &&
    typeof response.requested_amount === "number" &&
    typeof response.risk_signal?.risk_probability === "number" &&
    typeof response.risk_signal?.predicted_risk_class === "number" &&
    typeof response.risk_signal?.model_version === "string" &&
    Array.isArray(response.risk_signal?.top_risk_factors) &&
    Array.isArray(response.risk_signal?.top_protective_factors) &&
    ["ELIGIBLE", "MISSING_INFORMATION", "NOT_SUITABLE", "COMPLEX_REVIEW"].includes(decision ?? "") &&
    typeof response.policy_decision?.policy_version === "string" &&
    Array.isArray(response.policy_decision?.triggered_rule_ids) &&
    Array.isArray(response.policy_decision?.required_actions) &&
    typeof response.next_action === "string" &&
    !!response.audit
  );
}

export async function startJourney(request: JourneyRequest): Promise<JourneyResponse> {
  let response: Response;
  try {
    response = await fetch(`${apiBaseUrl}/api/v1/journeys`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(request)
    });
  } catch {
    throw new JourneyApiError("FinMate backend is unavailable.", "unavailable");
  }

  if (!response.ok) {
    if (response.status === 502 || response.status >= 500) {
      throw new JourneyApiError("FinMate backend is unavailable.", "unavailable");
    }
    throw new JourneyApiError("FinMate could not start this journey. Please check the information and retry.", "error");
  }

  let payload: unknown;
  try {
    payload = await response.json();
  } catch {
    throw new JourneyApiError("FinMate received an invalid journey response.", "invalid_response");
  }
  if (!isJourneyResponse(payload)) {
    throw new JourneyApiError("FinMate received an invalid journey response.", "invalid_response");
  }
  return payload;
}

export async function confirmSimulatedVerification(customerId: string, field: SimulatedVerificationField): Promise<void> {
  const response = await fetch(`${apiBaseUrl}/api/v1/journeys/simulated-verifications`, {
    method: "PATCH", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ customer_id: customerId, field })
  });
  if (!response.ok) throw new JourneyApiError("FinMate could not update the simulated verification.", "error");
}

export async function createCustomCustomer(payload: CustomCustomerRequest): Promise<CustomCustomerResponse> {
  let response: Response;
  try {
    response = await fetch(`${apiBaseUrl}/api/v1/custom-customers`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload) });
  } catch { throw new JourneyApiError("FinMate could not create the custom customer.", "unavailable"); }
  if (!response.ok) {
    let message = "FinMate could not create the custom customer. Please check the provided details.";
    try { const body = await response.json() as { detail?: string }; if (typeof body.detail === "string") message = body.detail; } catch { /* Safe default. */ }
    throw new JourneyApiError(message, "error");
  }
  return await response.json() as CustomCustomerResponse;
}

export async function reassessJourney(request: JourneyRequest, originalJourneyId: string): Promise<JourneyReassessmentResponse> {
  const response = await fetch(`${apiBaseUrl}/api/v1/journeys/reassess`, {
    method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ ...request, original_journey_id: originalJourneyId })
  });
  if (!response.ok) {
    let message = "FinMate could not re-run the governed journey assessment.";
    try { const body = await response.json() as { detail?: string }; if (typeof body.detail === "string") message = body.detail; } catch { /* Safe default. */ }
    throw new JourneyApiError(message, "error");
  }
  return await response.json() as JourneyReassessmentResponse;
}

async function getSimulatedContextSection(customerId: string, section: "financial" | "credit"): Promise<Record<string, unknown> | null> {
  try {
    const response = await fetch(`${apiBaseUrl}/api/v1/simulated-context/${encodeURIComponent(customerId)}/${section}`);
    if (!response.ok) return null;
    const value: unknown = await response.json();
    return value && typeof value === "object" ? value as Record<string, unknown> : null;
  } catch { return null; }
}

function numberValue(context: Record<string, unknown> | null, key: string): number | undefined {
  const value = context?.[key];
  return typeof value === "number" && Number.isFinite(value) ? value : undefined;
}

export async function getRecoveryCustomerContext(customerId: string): Promise<RecoveryCustomerContext> {
  const [financial, credit] = await Promise.all([getSimulatedContextSection(customerId, "financial"), getSimulatedContextSection(customerId, "credit")]);
  return { annualRevenue: numberValue(financial, "annual_revenue"), monthlyObligations: numberValue(financial, "existing_obligations"), creditScore: numberValue(credit, "fico_n") };
}

export async function getRecoveryPersonalization(customerId: string, journey: JourneyResponse): Promise<RecoveryPersonalizationResponse | null> {
  if (!journey.goal_recovery) return null;
  try {
    const response = await fetch(`${apiBaseUrl}/api/v1/recovery/personalize`, {
      method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({
        customer_id: customerId,
        policy_reason_code: journey.policy_decision.reason_code,
        risk_signal: journey.risk_signal,
        top_risk_factors: journey.risk_signal.top_risk_factors,
        recovery: journey.goal_recovery
      })
    });
    if (!response.ok) return null;
    const value: unknown = await response.json();
    return value && typeof value === "object" ? value as RecoveryPersonalizationResponse : null;
  } catch { return null; }
}

export { apiBaseUrl };
