import { useState } from "react";
import { useJourneyStore } from "../hooks/useJourneyStore";
import type { JourneyResponse, ShapFactor } from "../types/journey";
import { formatCurrency, formatProbability, readableFeature } from "../utils/format";

function ShapFactors({ title, factors }: { title: string; factors: ShapFactor[] }) {
  return <div className="review-factors"><strong>{title}</strong>{factors.length ? <ul>{factors.map((factor) => <li key={`${factor.feature}-${factor.shap_value}`}><span>{readableFeature(factor.feature)}</span><b>{factor.shap_value > 0 ? "+" : ""}{factor.shap_value.toFixed(3)}</b></li>)}</ul> : <p>No factors were returned for this journey.</p>}</div>;
}

export function HumanReviewCard({ journey }: { journey: JourneyResponse }) {
  const { currentCustomerId } = useJourneyStore();
  const [prepared, setPrepared] = useState(false);
  const policy = journey.policy_decision;

  return <section className="result-card review-card"><span className="eyebrow">HUMAN OVERSIGHT REQUIRED</span><h1>Your journey needs human review</h1><p>{policy.human_review_reason ?? policy.reason}</p>{!prepared ? <section className="review-action-card"><span className="eyebrow">PROTOTYPE REVIEW PACKAGE</span><h2>Prepare the governed evidence for review</h2><p>This action prepares the evidence already returned by the governed journey. It does not contact or assign a reviewer.</p><button className="button button-primary" type="button" onClick={() => setPrepared(true)}>Prepare Human Review</button></section> : <section className="prepared-review" aria-live="polite"><span className="eyebrow">PROTOTYPE REVIEW PACKAGE</span><h2>Human review package prepared</h2><p className="notice">No reviewer has been assigned. Reviewer assignment is not implemented in this prototype.</p><div className="review-package"><span>Customer</span><strong>{currentCustomerId ?? "Simulated customer context unavailable"}</strong><span>Goal</span><strong>{journey.customer_goal}</strong><span>Requested amount</span><strong>{formatCurrency(journey.requested_amount)}</strong><span>Risk signal</span><strong>{formatProbability(journey.risk_signal.risk_probability)} · class {journey.risk_signal.predicted_risk_class} · {journey.risk_signal.model_version}</strong><span>Policy decision</span><strong>{policy.decision}</strong><span>Governed reason</span><strong>{policy.reason_code} · {policy.reason}</strong><span>Triggered rules</span><strong>{policy.triggered_rule_ids.join(", ") || "None returned"}</strong><span>Policy version</span><strong>{policy.policy_version}</strong></div><div className="review-shap"><h3>SHAP explanation</h3><p>These factors explain the model risk signal; they do not make the review decision.</p><div className="review-factor-grid"><ShapFactors title="Risk factors" factors={journey.risk_signal.top_risk_factors} /><ShapFactors title="Protective factors" factors={journey.risk_signal.top_protective_factors} /></div></div></section>}</section>;
}
