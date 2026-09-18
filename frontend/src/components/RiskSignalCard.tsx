import type { JourneyRiskSignal } from "../types/journey";
import { formatProbability } from "../utils/format";

export function RiskSignalCard({ risk }: { risk: JourneyRiskSignal }) {
  return (
    <section className="card risk-card">
      <span className="eyebrow">RISK SIGNAL</span>
      <div className="metric">{formatProbability(risk.risk_probability)}</div>
      <p>Predicted risk class: <strong>{risk.predicted_risk_class}</strong></p>
      <small>Model: {risk.model_version}</small>
      <div className="notice">Risk signal — not an approval decision</div>
    </section>
  );
}
