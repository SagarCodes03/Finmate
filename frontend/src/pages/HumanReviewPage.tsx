import { Link } from "react-router-dom";
import { HumanReviewCard } from "../components/HumanReviewCard";
import { useJourneyStore } from "../hooks/useJourneyStore";

export function HumanReviewPage() {
  const { result } = useJourneyStore();
  if (!result) return <section className="empty-state"><h1>No human-review information is available yet.</h1><p>Analyze a journey first to view the backend’s current review information.</p><Link className="button button-primary" to="/">Start a new journey</Link></section>;
  if (!result.policy_decision.human_review_required && !result.goal_recovery?.human_review_required) return <section className="safe-state"><h1>Human review is not required for this journey.</h1><p>The current backend response did not flag human review.</p><Link className="button button-secondary" to="/journey">Back to journey</Link></section>;
  return <><HumanReviewCard journey={result} /><div className="page-back"><Link className="button button-secondary" to="/journey">Back to journey</Link></div></>;
}
