import { useState } from "react";
import type { RecoveryPath, RecoveryPlanPeriod } from "../types/journey";
import { formatCurrency } from "../utils/format";

export function RecoveryPathCard({ path, explanation, personalizedPlan, onReassess, isReassessing, canReassess }: { path: RecoveryPath; explanation?: string; personalizedPlan?: RecoveryPlanPeriod[]; onReassess: (amount: number) => Promise<void>; isReassessing: boolean; canReassess: boolean }) {
  const [planStarted, setPlanStarted] = useState(false);
  const isFinancingPath = path.path === "RIGHT_SIZED_FINANCING" || path.path === "PHASED_FINANCING";
  const title = path.path === "RIGHT_SIZED_FINANCING" ? "Smaller amount" : path.path === "PHASED_FINANCING" ? "Fund in stages" : "Improve eligibility";
  const amount = path.alternative_amount ?? path.requested_amount;
  const actionLabel = path.path === "RIGHT_SIZED_FINANCING" ? `Re-evaluate ${formatCurrency(amount)} →` : "Evaluate Phase 1 →";
  return <article className="recovery-path" id={path.path}>
    <span className="path-label">RECOVERY PATH</span><h2>{title}</h2><p>{explanation ?? path.description}</p>
    {path.alternative_amount != null && <div className="path-amount">{formatCurrency(path.alternative_amount)}</div>}
    {isFinancingPath ? <><p className="path-reason">{path.reason}</p>{path.path === "PHASED_FINANCING" && <p>Phase 1: {formatCurrency(amount)}</p>}<button className="button button-primary" type="button" onClick={() => void onReassess(amount)} disabled={isReassessing || !canReassess}>{isReassessing ? "Re-evaluating your request…" : !canReassess ? "Recovery reassessment already completed" : actionLabel}</button></> : <div className="recovery-plan"><p className="path-timeline"><strong>Personalized 90-day plan</strong></p>{(personalizedPlan ?? []).map((period) => <section key={period.period}><h3>{period.period}</h3><ul>{period.actions.map((action) => <li key={action}>{action}</li>)}</ul></section>)}{!personalizedPlan && <section><ul>{path.next_actions.map((action) => <li key={action}>{action}</li>)}</ul></section>}<section><h3>Reassessment</h3>{!planStarted ? <button className="button button-primary" type="button" onClick={() => setPlanStarted(true)}>Start 90-day plan →</button> : <button className="button button-primary" type="button" onClick={() => void onReassess(amount)} disabled={isReassessing || !canReassess}>{isReassessing ? "Re-evaluating your request…" : !canReassess ? "Recovery reassessment already completed" : "Reassess after 90 days →"}</button>}</section></div>}
  </article>;
}
