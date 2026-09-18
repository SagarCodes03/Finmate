import type { JourneyResponse } from "../types/journey";
import { formatCurrency } from "../utils/format";
import { StatusBadge } from "./StatusBadge";

export function DecisionSummary({ journey }: { journey: JourneyResponse }) {
  const policy = journey.policy_decision;
  return (
    <section className="decision-summary card">
      <div>
        <span className="eyebrow">GOVERNED POLICY DECISION</span>
        <h2>{policy.reason}</h2>
        <p>{journey.customer_goal} · {formatCurrency(journey.requested_amount)}</p>
      </div>
      <div className="decision-status"><StatusBadge decision={policy.decision} /><span>{policy.reason_code}</span></div>
      <div className="journey-actions" aria-label="Journey details">
        <Link to="/intelligence">Decision intelligence</Link>
        {journey.goal_recovery && <Link to="/recovery">Explore recovery paths</Link>}
        {policy.human_review_required && <Link to="/human-review">Human review</Link>}
        <Link to="/audit">Audit</Link>
      </div>
    </section>
  );
}
import { Link } from "react-router-dom";
