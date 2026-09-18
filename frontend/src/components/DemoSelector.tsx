import { demoCustomers, type DemoCustomer } from "../data/demos";
import { formatCurrency } from "../utils/format";

export function DemoSelector({ selectedId, onSelect }: { selectedId: string; onSelect: (demo: DemoCustomer) => void }) {
  return (
    <section className="demo-selector" aria-labelledby="demo-mode-heading">
      <div className="section-heading">
        <div>
          <span className="eyebrow">DEMO MODE</span>
          <h2 id="demo-mode-heading">Choose a verified journey</h2>
        </div>
        <p>Each route is governed by the backend.</p>
      </div>
      <div className="demo-grid">
        {demoCustomers.map((demo) => (
          <button key={demo.id} className={`demo-card ${selectedId === demo.id ? "selected" : ""}`} onClick={() => onSelect(demo)} type="button">
            <span className="avatar">{demo.name[0]}</span>
            <span><strong>{demo.name}</strong><small>{demo.outcomeHint}</small></span>
            <em>{formatCurrency(demo.amount)}</em>
          </button>
        ))}
      </div>
    </section>
  );
}
