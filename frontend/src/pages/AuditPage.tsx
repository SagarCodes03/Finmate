import { Link } from "react-router-dom";
import { AuditPanel } from "../components/AuditPanel";
import { useJourneyStore } from "../hooks/useJourneyStore";
export function AuditPage() { const { result } = useJourneyStore(); return result ? <><AuditPanel journey={result} /><div className="page-back"><Link className="button button-secondary" to="/journey">Back to journey</Link></div></> : <section className="empty-state"><h1>No journey audit is available yet.</h1><p>This screen only displays fields returned with the current frontend session’s journey.</p><Link className="button button-primary" to="/">Start a new journey</Link></section>; }
