import { useState } from "react";
import type { RecoveryPath } from "../types/journey";
import { formatCurrency } from "../utils/format";

export function RecoveryPathCard({ path }: { path: RecoveryPath }) {
  const [expanded, setExpanded] = useState(false);
  return <article className="recovery-path" id={path.path}>
    <span className="path-label">Illustrative prototype pathway · {path.path.replace(/_/g, " ")}</span>
    <h2>{path.title}</h2><p>{path.description}</p>
    {path.timeline_days != null && <p className="path-timeline"><strong>Preparation timeline:</strong> {path.timeline_days} days</p>}
    {path.alternative_amount != null && <div className="path-amount">{formatCurrency(path.alternative_amount)} <small>illustrative amount — not an offer, approval, or guarantee</small></div>}
    {expanded && <div className="path-details"><p className="path-reason">{path.reason}</p><ul>{path.next_actions.map((action) => <li key={action}>{action}</li>)}</ul></div>}
    <button className="button button-secondary" type="button" aria-expanded={expanded} onClick={() => setExpanded((value) => !value)}>{expanded ? "Hide pathway details" : "Explore this pathway"}</button>
  </article>;
}
