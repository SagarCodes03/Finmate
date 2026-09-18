import type { PolicyDecision } from "../types/journey";
import { StatusBadge } from "./StatusBadge";

export function PolicyDecisionCard({ policy }: { policy: PolicyDecision }) {
  return (
    <section className="card policy-card">
      <span className="eyebrow">GOVERNED POLICY DECISION</span>
      <div className="policy-title"><h2>{policy.decision.replace(/_/g, " ")}</h2><StatusBadge decision={policy.decision} /></div>
      <p>{policy.reason}</p>
      <dl className="metadata"><div><dt>Policy version</dt><dd>{policy.policy_version}</dd></div><div><dt>Triggered rules</dt><dd>{policy.triggered_rule_ids.length ? policy.triggered_rule_ids.join(", ") : "None returned"}</dd></div></dl>
      {policy.human_review_required && <p className="notice">Human oversight required: {policy.human_review_reason ?? "See the governed next actions."}</p>}
      {policy.required_actions.length > 0 && <div className="inline-actions"><strong>Required actions</strong><ul>{policy.required_actions.map((action) => <li key={action}>{action}</li>)}</ul></div>}
    </section>
  );
}
