import { Link, useNavigate } from "react-router-dom";
import { StatusBadge } from "../components/StatusBadge";
import { useJourneyStore } from "../hooks/useJourneyStore";
import { formatCurrency } from "../utils/format";

export function HistoryPage() {
  const { history, openJourney } = useJourneyStore();
  const navigate = useNavigate();
  return <div><section className="page-heading"><span className="eyebrow">DEMO HISTORY</span><h1>Journeys from this browser session</h1><p>FinMate’s current backend does not persist journeys. This is not a backend history.</p></section>{history.length === 0 ? <section className="empty-state"><p>No journeys have been analyzed in this session.</p><Link className="button button-primary" to="/">Start a new journey</Link></section> : <div className="history-list">{history.map((journey) => <button className="history-card" key={journey.journey_id} type="button" onClick={() => { openJourney(journey); navigate("/journey"); }}><div><strong>{journey.customer_goal}</strong><small>{journey.journey_id}</small></div><span>{formatCurrency(journey.requested_amount)}</span><StatusBadge decision={journey.policy_decision.decision} /></button>)}</div>}</div>;
}
