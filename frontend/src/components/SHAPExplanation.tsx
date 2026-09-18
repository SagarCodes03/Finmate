import type { ShapFactor } from "../types/journey";
import { readableFeature } from "../utils/format";

function FactorList({ title, factors, kind }: { title: string; factors: ShapFactor[]; kind: "risk" | "protective" }) {
  return (
    <div className={`factor-list ${kind}`}>
      <h3>{title}</h3>
      {factors.length === 0 ? <p className="muted">No factors were returned for this journey.</p> : factors.map((factor) => (
        <div className="factor" key={`${factor.feature}-${factor.shap_value}`}>
          <span>{readableFeature(factor.feature)}</span><strong>{factor.shap_value > 0 ? "+" : ""}{factor.shap_value.toFixed(3)}</strong>
        </div>
      ))}
    </div>
  );
}

export function SHAPExplanation({ riskFactors, protectiveFactors }: { riskFactors: ShapFactor[]; protectiveFactors: ShapFactor[] }) {
  return <section className="card shap-card"><span className="eyebrow">SHAP EXPLAINABILITY</span><h2>Model-linked factors</h2><p className="muted">These values explain the model signal; they are not a governed decision.</p><div className="factor-columns"><FactorList title="Risk factors" factors={riskFactors} kind="risk" /><FactorList title="Protective factors" factors={protectiveFactors} kind="protective" /></div></section>;
}
