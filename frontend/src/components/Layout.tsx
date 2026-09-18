import { NavLink, useLocation } from "react-router-dom";
import type { ReactNode } from "react";

const navItems = [
  ["/", "New journey"],
  ["/journey", "Journey"],
  ["/assistant", "FinMate AI"],
  ["/intelligence", "Decision intelligence"],
  ["/audit", "Audit & transparency"],
  ["/history", "Demo history"]
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
          {navItems.map(([to, label]) => (
            <NavLink key={to} to={to} end={to === "/"} className={({ isActive }) => `nav-link ${isActive ? "active" : ""}`}>
              {label}
            </NavLink>
          ))}
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
