import type { JourneyResponse } from "../types/journey";
import type { CSSProperties } from "react";
import { formatProbability } from "../utils/format";

const outcomeLabels = {
  ELIGIBLE: "Policy path clear",
  MISSING_INFORMATION: "Information needed",
  NOT_SUITABLE: "Path constrained",
  COMPLEX_REVIEW: "Human oversight"
} as const;

export function GovernedJourney({ journey }: { journey: JourneyResponse }) {
  const decision = journey.policy_decision.decision;
  const stages = [
    { label: "Goal", detail: journey.customer_goal, state: "complete" },
    { label: "Context", detail: "Simulated context assembled", state: "complete" },
    { label: "Risk signal", detail: formatProbability(journey.risk_signal.risk_probability), state: "complete" },
    { label: "SHAP", detail: `${journey.risk_signal.top_risk_factors.length + journey.risk_signal.top_protective_factors.length} factors returned`, state: "complete" },
    { label: "Policy", detail: journey.policy_decision.policy_version, state: "complete" },
    { label: "Outcome", detail: outcomeLabels[decision], state: "current" }
  ];

  return <section className="governed-journey" aria-labelledby="governed-journey-title">
    <div className="journey-visual-heading">
      <div><span className="eyebrow">THE LIVING GOVERNED JOURNEY</span><h2 id="governed-journey-title">Evidence moves forward. Authority stays separated.</h2></div>
      <p>AI orchestrates <b>·</b> ML + rules govern <b>·</b> humans oversee</p>
    </div>
    <ol className="journey-stages">
      {stages.map((stage, index) => <li className={`journey-stage ${stage.state}`} style={{ "--stage": index } as CSSProperties} key={stage.label}>
        <span className="stage-index">0{index + 1}</span><strong>{stage.label}</strong><small>{stage.detail}</small>
      </li>)}
    </ol>
    <div className="journey-evidence-strip">
      <span>Model-derived signal <b>{formatProbability(journey.risk_signal.risk_probability)}</b></span>
      <span>SHAP evidence <b>{journey.risk_signal.top_risk_factors.length + journey.risk_signal.top_protective_factors.length} factors available</b></span>
      <span>Policy outcome <b>{decision.replace(/_/g, " ")}</b></span>
    </div>
  </section>;
}
