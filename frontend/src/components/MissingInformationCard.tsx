import { useState } from "react";
import { useJourneyStore } from "../hooks/useJourneyStore";
import type { SimulatedVerificationField } from "../types/journey";

export function MissingInformationCard({ actions }: { actions: string[] }) {
  const { confirmVerification, reassess } = useJourneyStore();
  const [confirmed, setConfirmed] = useState<SimulatedVerificationField[]>([]);
  const [loadingField, setLoadingField] = useState<SimulatedVerificationField | null>(null);
  const [isReassessing, setIsReassessing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const verificationFields: { key: SimulatedVerificationField; title: string; action: string }[] = [
    { key: "customer_identity_verified", title: "Identity Verification", action: "Verify Identity" },
    { key: "required_documents_complete", title: "Required Documents", action: "Confirm Documents" },
  ];
  const fields = verificationFields.filter((field) => actions.some((item) => item.includes(field.key)));
  const confirm = async (field: SimulatedVerificationField) => {
    setLoadingField(field); setError(null);
    if (await confirmVerification(field)) setConfirmed((current) => [...current, field]);
    else setError("The simulated verification could not be updated.");
    setLoadingField(null);
  };
  const rerun = async () => { setIsReassessing(true); setError(null); if (!await reassess()) setError("The governed reassessment could not be completed."); setIsReassessing(false); };
  return <section className="result-card missing-card"><span className="eyebrow">SIMULATED PROTOTYPE / INFORMATION CHECKLIST</span><h1>We need a little more information</h1><p>Confirm only the items identified by the governed policy, then re-run the governed journey.</p><p className="notice">No real identity or document verification occurs. This updates simulated prototype context only.</p><div className="checklist">{fields.map((field) => <div key={field.key}><strong>{field.title}</strong><button className="button button-secondary" type="button" onClick={() => void confirm(field.key)} disabled={Boolean(loadingField) || confirmed.includes(field.key)}>{confirmed.includes(field.key) ? "Simulated confirmation complete" : loadingField === field.key ? "Confirming…" : field.action}</button></div>)}</div>{error && <p className="form-note" role="alert">{error}</p>}<button className="button button-primary" type="button" onClick={() => void rerun()} disabled={confirmed.length !== fields.length || isReassessing}>{isReassessing ? "Re-running governed assessment…" : "Re-run Journey Assessment"}</button><small>The original result remains a previous assessment; the next screen shows the actual reassessment result.</small></section>;
}
