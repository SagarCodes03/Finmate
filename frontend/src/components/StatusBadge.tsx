import type { GovernedDecision } from "../types/journey";

const labels: Record<GovernedDecision, string> = {
  ELIGIBLE: "Eligible",
  MISSING_INFORMATION: "Information needed",
  COMPLEX_REVIEW: "Human review",
  NOT_SUITABLE: "Goal recovery"
};

export function StatusBadge({ decision }: { decision: GovernedDecision }) {
  return <span className={`status-badge status-${decision.toLowerCase()}`}>{labels[decision]}</span>;
}
