import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import App from "../App";
import type { GovernedDecision, JourneyResponse } from "../types/journey";

function responseFor(decision: GovernedDecision): JourneyResponse {
  return {
    journey_id: "test-journey-1",
    customer_goal: "Purchase inventory",
    requested_amount: 200000,
    risk_signal: { risk_probability: 0.6, predicted_risk_class: 1, model_version: "finmate-default-risk-xgb-v2", top_risk_factors: [{ feature: "numeric__dti_n", shap_value: 0.2 }], top_protective_factors: [], prototype_only: true, is_simulated_journey: true },
    policy_decision: { decision, reason_code: "PROTOTYPE_RESULT", reason: "A deterministic prototype policy result.", risk_signal: { risk_probability: 0.6, predicted_risk_class: 1, model_version: "finmate-default-risk-xgb-v2" }, required_actions: ["Provide or verify: required_documents_complete"], human_review_required: decision === "COMPLEX_REVIEW", human_review_reason: decision === "COMPLEX_REVIEW" ? "A human review is required." : null, policy_version: "prototype-v1", triggered_rule_ids: ["P004_RISK_OR_AMOUNT_REVIEW"], audit_context: { journey_id: "test-journey-1" } },
    goal_recovery: decision === "NOT_SUITABLE" ? { recovery_status: "AVAILABLE", original_goal: "Purchase inventory", original_requested_amount: 200000, original_policy_decision: "NOT_SUITABLE", recovery_reason_code: "HIGH_RISK_PROTOTYPE_RECOVERY", recovery_reason: "Controlled alternatives are available.", available_paths: [{ path: "RIGHT_SIZED_FINANCING", title: "Right-sized prototype financing path", description: "Consider a smaller request.", reason: "A lower amount is a future path.", requested_amount: 200000, alternative_amount: 100000, next_actions: ["Review the smaller amount."], prototype_only: true }], policy_version: "prototype-v1", recovery_version: "prototype-recovery-v1", human_review_required: false, human_review_reason: null, triggered_rule_ids: ["R004_HIGH_RISK_RECOVERY"], audit_context: { journey_id: "test-journey-1" } } : null,
    next_action: "Continue to the next governed journey step.",
    audit: { policy_version: "prototype-v1", simulated: true }
  };
}

async function submitDecision(decision: GovernedDecision) {
  vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response(JSON.stringify(responseFor(decision)), { status: 200, headers: { "Content-Type": "application/json" } })));
  render(<App />);
  await userEvent.click(screen.getByRole("button", { name: /analyze my journey/i }));
  await waitFor(() => expect(window.location.pathname).toBe("/journey"));
}

beforeEach(() => { window.history.pushState({}, "", "/"); vi.unstubAllGlobals(); });
afterEach(() => cleanup());

describe("FinMate journey UI", () => {
  it("constructs a governed journey request from the form", async () => {
    const fetchMock = vi.fn().mockResolvedValue(new Response(JSON.stringify(responseFor("NOT_SUITABLE")), { status: 200, headers: { "Content-Type": "application/json" } }));
    vi.stubGlobal("fetch", fetchMock);
    render(<App />);
    fireEvent.change(screen.getByLabelText(/financial goal/i), { target: { value: "Purchase inventory" } });
    await userEvent.click(screen.getByRole("button", { name: /analyze my journey/i }));
    await waitFor(() => expect(fetchMock).toHaveBeenCalled());
    const [, options] = fetchMock.mock.calls[0] as [string, RequestInit];
    expect(JSON.parse(String(options.body))).toMatchObject({ customer_id: "recovery-demo", customer_goal: "Purchase inventory", requested_amount: 200000 });
  });

  it("renders an eligible governed next step without approval language", async () => { await submitDecision("ELIGIBLE"); expect(await screen.findByText(/your journey can move forward/i)).toBeInTheDocument(); expect(screen.getByText(/eligible for the next governed journey step/i)).toBeInTheDocument(); });
  it("renders returned required actions for missing information", async () => { await submitDecision("MISSING_INFORMATION"); expect(await screen.findByText(/we need a little more information/i)).toBeInTheDocument(); expect(screen.getByRole("button", { name: /confirm documents/i })).toBeInTheDocument(); });
  it("confirms simulated missing fields and renders the returned reassessment", async () => {
    const missing = responseFor("MISSING_INFORMATION");
    missing.policy_decision.required_actions = ["Provide or verify: customer_identity_verified", "Provide or verify: required_documents_complete"];
    const reassessed = responseFor("COMPLEX_REVIEW"); reassessed.journey_id = "test-journey-1-reassessment";
    const fetchMock = vi.fn()
      .mockResolvedValueOnce(new Response(JSON.stringify(missing), { status: 200, headers: { "Content-Type": "application/json" } }))
      .mockResolvedValueOnce(new Response("", { status: 200 }))
      .mockResolvedValueOnce(new Response("", { status: 200 }))
      .mockResolvedValueOnce(new Response(JSON.stringify({ original_journey_id: "test-journey-1", reassessment: reassessed, is_simulated: true }), { status: 200, headers: { "Content-Type": "application/json" } }));
    vi.stubGlobal("fetch", fetchMock);
    render(<App />);
    await userEvent.click(screen.getByRole("button", { name: /analyze my journey/i }));
    await screen.findByRole("button", { name: /verify identity/i });
    const rerun = screen.getByRole("button", { name: /re-run journey assessment/i });
    expect(rerun).toBeDisabled();
    await userEvent.click(screen.getByRole("button", { name: /verify identity/i }));
    await userEvent.click(screen.getByRole("button", { name: /confirm documents/i }));
    await waitFor(() => expect(rerun).toBeEnabled());
    await userEvent.click(rerun);
    expect(await screen.findByText(/simulated reassessment/i)).toBeInTheDocument();
    expect(screen.getByText(/your journey needs human review/i)).toBeInTheDocument();
    expect(fetchMock.mock.calls[3]?.[0]).toContain("/api/v1/journeys/reassess");
  });
  it("prepares a local human-review package from governed evidence", async () => {
    await submitDecision("COMPLEX_REVIEW");
    expect(await screen.findByText(/your journey needs human review/i)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /prepare human review/i })).toBeInTheDocument();
    expect(screen.queryByText(/next governed actions/i)).not.toBeInTheDocument();
    await userEvent.click(screen.getByRole("button", { name: /prepare human review/i }));
    expect(screen.getByText(/human review package prepared/i)).toBeInTheDocument();
    expect(screen.getByText(/no reviewer has been assigned/i)).toBeInTheDocument();
    expect(screen.getByText("COMPLEX_REVIEW")).toBeInTheDocument();
    expect(screen.getByText(/SHAP explanation/i)).toBeInTheDocument();
    expect(screen.getByText(/dti n/i)).toBeInTheDocument();
  });
  it("opens actual returned recovery paths", async () => {
    await submitDecision("NOT_SUITABLE");
    await userEvent.click(screen.getAllByRole("link", { name: /explore recovery paths/i })[0]);
    expect(await screen.findByText(/goal recovery pathways/i)).toBeInTheDocument();
    expect(screen.getByText(/right-sized prototype financing path/i)).toBeInTheDocument();
    await userEvent.click(screen.getByRole("button", { name: /explore this pathway/i }));
    expect(screen.getByText(/a lower amount is a future path/i)).toBeInTheDocument();
  });
  it("navigates to returned decision intelligence and audit metadata", async () => {
    await submitDecision("NOT_SUITABLE");
    const intelligenceLinks = screen.getAllByRole("link", { name: /^decision intelligence$/i });
    await userEvent.click(intelligenceLinks[intelligenceLinks.length - 1]);
    expect(await screen.findByText(/SHAP EXPLAINABILITY/i)).toBeInTheDocument();
    const auditLinks = screen.getAllByRole("link", { name: /^audit$/i });
    await userEvent.click(auditLinks[auditLinks.length - 1]);
    expect(await screen.findByText(/policy audit metadata returned by backend/i)).toBeInTheDocument();
  });
  it("navigates to actual human-review information", async () => {
    await submitDecision("COMPLEX_REVIEW");
    await userEvent.click(screen.getByRole("link", { name: /^human review$/i }));
    expect(await screen.findByText(/your journey needs human review/i)).toBeInTheDocument();
  });
  it("uses the active journey context without a customer switcher", async () => {
    await submitDecision("NOT_SUITABLE");
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response(JSON.stringify({ response: "The policy returned a governed result.", tools_used: ["evaluate_policy"], journey_status: "NOT_SUITABLE", context_used: ["current_governed_journey"], governance_note: "Governed prototype." }), { status: 200, headers: { "Content-Type": "application/json" } })));
    await userEvent.click(screen.getByRole("link", { name: /finmate ai/i }));
    expect(screen.getByRole("heading", { name: /ask about your journey context/i })).toBeInTheDocument();
    expect(screen.queryByLabelText(/chat demo customer/i)).not.toBeInTheDocument();
    expect(screen.getByText("Meera")).toBeInTheDocument();
    await userEvent.click(screen.getByRole("button", { name: /explain my risk assessment/i }));
    expect(await screen.findByText(/The policy returned a governed result/i)).toBeInTheDocument();
    expect(screen.getByText("evaluate_policy")).toBeInTheDocument();
    const [, request] = (vi.mocked(fetch).mock.calls[0] ?? []) as [string, RequestInit];
    expect(JSON.parse(String(request.body))).toMatchObject({ customer_id: "recovery-demo", message: "Explain my risk assessment", current_journey: { journey_id: "test-journey-1" } });
  });

  it("shows the safe backend assistant error detail", async () => {
    await submitDecision("NOT_SUITABLE");
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response(JSON.stringify({ detail: "The Gemini service could not complete this request." }), { status: 502, headers: { "Content-Type": "application/json" } })));
    await userEvent.click(screen.getByRole("link", { name: /finmate ai/i }));
    await userEvent.click(screen.getByRole("button", { name: /explain my risk assessment/i }));
    expect(await screen.findByRole("alert")).toHaveTextContent(/Gemini service could not complete this request/i);
  });
  it("shows the unavailable backend state instead of a result", async () => {
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new TypeError("network down")));
    render(<App />);
    await userEvent.click(screen.getByRole("button", { name: /analyze my journey/i }));
    expect(await screen.findByText(/FinMate backend is unavailable/i)).toBeInTheDocument();
  });
  it("shows a safe invalid response state", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response(JSON.stringify({ invalid: true }), { status: 200 })));
    render(<App />);
    await userEvent.click(screen.getByRole("button", { name: /analyze my journey/i }));
    expect(await screen.findByText(/invalid journey response/i)).toBeInTheDocument();
  });
});
