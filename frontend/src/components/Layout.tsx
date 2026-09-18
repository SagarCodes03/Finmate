import { NavLink, useLocation } from "react-router-dom";
import type { ReactNode } from "react";

const navGroups = [
  { label: "Journey", items: [["/", "New journey"], ["/journey", "Journey"]] },
  { label: "Intelligence", items: [["/intelligence", "Decision intelligence"], ["/assistant", "FinMate AI"]] },
  { label: "Governance", items: [["/human-review", "Human review"], ["/audit", "Audit & transparency"]] },
  { label: "History", items: [["/history", "Demo history"]] }
] as const;

export function Layout({ children }: { children: ReactNode }) {
  const location = useLocation();
  return (
    <div className="app-shell">
      <aside className="sidebar">
        <NavLink to="/" className="brand" aria-label="FinMate home">
          <span className="brand-mark" aria-hidden="true"><i /><i /><i /></span>
          <span>Fin<span>Mate</span></span>
        </NavLink>
        <p className="brand-tagline">Your AI teammate for financial journeys.</p>
        <nav aria-label="Primary navigation">
          {navGroups.map((group) => <section className="nav-group" key={group.label}>
            <span>{group.label}</span>
            {group.items.map(([to, label]) => (
              <NavLink key={to} to={to} end={to === "/"} aria-label={label === "Human review" ? "Human review workspace" : undefined} className={({ isActive }) => `nav-link ${isActive ? "active" : ""}`}>
                {label}
              </NavLink>
            ))}
          </section>)}
        </nav>
        <div className="sidebar-note">
          <strong>Prototype mode</strong>
          <span>AI orchestrates. ML + Rules govern. Humans oversee.</span>
        </div>
      </aside>
      <main className="main-content">
        <header className="topbar">
          <span className="eyebrow">FINMATE / {location.pathname === "/" ? "NEW JOURNEY" : "GOVERNED JOURNEY"}</span>
          <span className="simulated-pill">Prototype / simulated data</span>
        </header>
        {children}
      </main>
    </div>
  );
}
