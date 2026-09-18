import { Link } from "react-router-dom";
import { DecisionSummary } from "../components/DecisionSummary";
import { PolicyDecisionCard } from "../components/PolicyDecisionCard";
import { RiskSignalCard } from "../components/RiskSignalCard";
import { SHAPExplanation } from "../components/SHAPExplanation";
import { useJourneyStore } from "../hooks/useJourneyStore";

export function IntelligencePage() {
  const { result } = useJourneyStore();
  if (!result) return <Empty />;
  return <div className="intelligence-page"><section className="page-heading"><span className="eyebrow">DECISION INTELLIGENCE</span><h1>Clear evidence, separated by responsibility.</h1><p>Risk signal — not an approval decision.</p></section><div className="architecture-flow"><span>Journey</span><b>→</b><span>Context</span><b>→</b><span>XGBoost risk signal</span><b>→</b><span>SHAP explanation</span><b>→</b><strong>Policy decision</strong></div><div className="intelligence-grid"><RiskSignalCard risk={result.risk_signal} /><PolicyDecisionCard policy={result.policy_decision} /><DecisionSummary journey={result} /></div><SHAPExplanation riskFactors={result.risk_signal.top_risk_factors} protectiveFactors={result.risk_signal.top_protective_factors} />{result.goal_recovery && <section className="card recovery-evidence"><span className="eyebrow">GOAL RECOVERY INFORMATION</span><h2>{result.goal_recovery.recovery_status}</h2><p>{result.goal_recovery.recovery_reason}</p><p className="muted">Recovery version: {result.goal_recovery.recovery_version}</p><div className="rule-list">{result.goal_recovery.available_paths.map((path) => <span key={path.path}>{path.path}</span>)}</div></section>}</div>;
}
function Empty() { return <section className="empty-state"><h1>No decision intelligence yet.</h1><p>Analyze a journey first to see its actual returned evidence.</p><Link className="button button-primary" to="/">Start a new journey</Link></section>; }
