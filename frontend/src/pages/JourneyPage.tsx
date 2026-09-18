import { Link } from "react-router-dom";
import { DecisionSummary } from "../components/DecisionSummary";
import { GovernedJourney } from "../components/GovernedJourney";
import { HumanReviewCard } from "../components/HumanReviewCard";
import { MissingInformationCard } from "../components/MissingInformationCard";
import { RecoveryPathCard } from "../components/RecoveryPathCard";
import { RiskSignalCard } from "../components/RiskSignalCard";
import { demoCustomers } from "../data/demos";
import { useJourneyStore } from "../hooks/useJourneyStore";
import { formatCurrency } from "../utils/format";

export function JourneyPage() {
  const { result, previousAssessment, currentCustomerId, customerSummary } = useJourneyStore();
  if (!result) return <EmptyJourney />;
  const decision = result.policy_decision.decision;
  const previous = previousAssessment && <section className="notice"><strong>Simulated reassessment</strong> of previous journey {previousAssessment.journey_id} ({previousAssessment.policy_decision.decision}). The result below is a new governed assessment.</section>;
  if (!['ELIGIBLE', 'MISSING_INFORMATION', 'COMPLEX_REVIEW', 'NOT_SUITABLE'].includes(decision)) return <section className="safe-state"><h1>We could not safely display this journey</h1><p>The backend returned an unexpected governed decision.</p><Link className="button button-primary" to="/">Start a new journey</Link></section>;
  const customerName = customerSummary?.name ?? demoCustomers.find((customer) => customer.id === currentCustomerId)?.name ?? "Simulated customer";
  const businessType = customerSummary?.businessType;
  const context = <><section className="journey-context"><div><span>Customer</span><strong>{customerName}</strong>{businessType && <small>{businessType}</small>}</div><div><span>Goal / requested</span><strong>{result.customer_goal} · {formatCurrency(result.requested_amount)}</strong></div><div><span>Governed status</span><strong>{decision.replace(/_/g, " ")}</strong></div></section><GovernedJourney journey={result} /></>;
  if (decision === 'MISSING_INFORMATION') return <>{previous}{context}<div className="result-layout"><MissingInformationCard actions={result.policy_decision.required_actions} /><aside><RiskSignalCard risk={result.risk_signal} /><DecisionSummary journey={result} /></aside></div></>;
  if (decision === 'COMPLEX_REVIEW') return <>{previous}{context}<div className="result-layout"><HumanReviewCard journey={result} /><aside><RiskSignalCard risk={result.risk_signal} /><DecisionSummary journey={result} /></aside></div></>;
  if (decision === 'NOT_SUITABLE') return <>{previous}{context}<NotSuitableSummary /></>;
  return <>{previous}{context}<div className="result-layout"><section className="result-card eligible-card"><span className="eyebrow">GOVERNED NEXT STEP</span><h1>Your journey can move forward</h1><p>Your goal: <strong>{result.customer_goal}</strong></p><div className="path-amount">{formatCurrency(result.requested_amount)}</div><p>{result.next_action}</p><div className="notice">Eligible for the next governed journey step. This is not a loan approval or guarantee.</div></section><aside><RiskSignalCard risk={result.risk_signal} /><DecisionSummary journey={result} /></aside></div></>;
}

function NotSuitableSummary() {
  const { result } = useJourneyStore();
  if (!result?.goal_recovery) return <section className="safe-state"><h1>Recovery details are unavailable</h1><p>The governed result did not include recovery options.</p><Link className="button button-primary" to="/">Start a new journey</Link></section>;
  const recovery = result.goal_recovery;
  return <div className="result-layout"><section className="result-card missing-card"><span className="eyebrow">GOVERNED RESULT</span><h1>This original path is not suitable.</h1><p>{result.policy_decision.reason}</p><p>{recovery.recovery_reason}</p><Link className="button button-primary" to="/recovery">Explore Recovery Paths</Link><p className="notice">Recovery paths are illustrative prototype paths. Any amount shown is not an offer, approval, or guarantee.</p></section><aside><RiskSignalCard risk={result.risk_signal} /><DecisionSummary journey={result} /></aside></div>;
}

export function RecoveryPage() {
  const { result } = useJourneyStore();
  if (!result?.goal_recovery) return <section className="empty-state"><h1>No Goal Recovery data is available yet.</h1><p>Recovery information appears only when the backend returns it for the current journey.</p><Link className="button button-primary" to="/journey">Back to journey</Link></section>;
  const recovery = result.goal_recovery;
  return <div className="recovery-page"><section className="recovery-hero"><span className="eyebrow">GOAL RECOVERY / PROTOTYPE</span><h1>Your original path isn’t suitable.<br /><span>Your goal may still have illustrative paths.</span></h1><p>{recovery.recovery_reason}</p><div><span>Original goal</span><strong>{recovery.original_goal}</strong><span>Requested amount</span><strong>{formatCurrency(recovery.original_requested_amount)}</strong><span>Recovery status</span><strong>{recovery.recovery_status}</strong></div></section><section><div className="section-heading"><div><span className="eyebrow">AVAILABLE PATHWAYS</span><h2>Goal Recovery pathways</h2></div><p>Illustrative prototype paths; not offers, approvals, or guarantees.</p></div>{recovery.available_paths.length > 0 ? <div className="recovery-grid">{recovery.available_paths.map((path) => <RecoveryPathCard key={path.path} path={path} />)}</div> : <section className="card empty-recovery"><p>No recovery paths were returned for this journey.</p><p>{recovery.recovery_reason}</p></section>}</section><p className="notice">Customer data is simulated. Goal Recovery does not alter the XGBoost risk signal or deterministic policy decision.</p><Link className="button button-secondary" to="/journey">Back to journey</Link></div>;
}

function EmptyJourney() { return <section className="empty-state"><h1>No journey has been analyzed yet.</h1><p>Start a governed demo journey to see the response-driven experience.</p><Link className="button button-primary" to="/">Start a new journey</Link></section>; }
