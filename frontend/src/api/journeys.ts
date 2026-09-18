import type { JourneyReassessmentResponse, JourneyRequest, JourneyResponse, SimulatedVerificationField } from "../types/journey";

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

export async function reassessJourney(request: JourneyRequest, originalJourneyId: string): Promise<JourneyReassessmentResponse> {
  const response = await fetch(`${apiBaseUrl}/api/v1/journeys/reassess`, {
    method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ ...request, original_journey_id: originalJourneyId })
  });
  if (!response.ok) throw new JourneyApiError("FinMate could not re-run the governed journey assessment.", "error");
  return await response.json() as JourneyReassessmentResponse;
}

export { apiBaseUrl };
