import { useState, type FormEvent } from "react";
import { useNavigate } from "react-router-dom";
import { createCustomCustomer } from "../api/journeys";
import { CustomCustomerForm } from "../components/CustomCustomerForm";
import { DemoSelector } from "../components/DemoSelector";
import { ErrorState } from "../components/ErrorState";
import { JourneyProgress } from "../components/JourneyProgress";
import { demoCustomers, type DemoCustomer } from "../data/demos";
import { useJourneyStore } from "../hooks/useJourneyStore";
import type { CustomCustomerRequest } from "../types/journey";
import { formatCurrency, newJourneyId } from "../utils/format";

export function NewJourneyPage() {
  const defaultDemo = demoCustomers[3];
  const [customer, setCustomer] = useState<DemoCustomer>(defaultDemo);
  const [goal, setGoal] = useState(defaultDemo.goal);
  const [amount, setAmount] = useState(String(defaultDemo.amount));
  const [customMode, setCustomMode] = useState(false);
  const [customError, setCustomError] = useState<string | null>(null);
  const { status, errorMessage, submit, setCustomerSummary } = useJourneyStore();
  const navigate = useNavigate();
  const selectDemo = (demo: DemoCustomer) => { setCustomer(demo); setGoal(demo.goal); setAmount(String(demo.amount)); };
  const send = async () => { const requestedAmount = Number(amount.replace(/[^0-9]/g, "")); if (!goal.trim() || !Number.isSafeInteger(requestedAmount) || requestedAmount <= 0) return; const result = await submit({ journey_id: newJourneyId(), customer_id: customer.id, customer_goal: goal.trim(), requested_amount: requestedAmount }); if (result) navigate("/journey"); };
  const submitCustom = async (payload: CustomCustomerRequest) => { setCustomError(null); try { const created = await createCustomCustomer(payload); setCustomerSummary({ name: created.name, businessType: created.business_type }); const result = await submit({ journey_id: newJourneyId(), customer_id: created.customer_id, customer_goal: created.customer_goal, requested_amount: created.requested_amount }); if (result) navigate("/journey"); } catch (error) { setCustomError(error instanceof Error ? error.message : "FinMate could not create the custom customer."); } };
  if (status === "SUBMITTING") return <JourneyProgress />;
  if (!customMode && ["API_UNAVAILABLE", "INVALID_RESPONSE", "ERROR"].includes(status) && errorMessage) return <ErrorState message={errorMessage} onRetry={() => void send()} />;
  return <div className="new-journey-page"><section className="hero-card"><div><span className="eyebrow">GOVERNED FINANCIAL JOURNEYS</span><h1>{customMode ? "Bring a new journey into view." : "What are you trying to achieve?"}</h1><p>Start with a goal. FinMate coordinates the journey and presents the backend’s governed result.</p></div><div className="hero-rule">AI orchestrates.<br />ML + Rules govern.<br />Humans oversee.</div></section>{customMode ? <CustomCustomerForm onSubmit={submitCustom} onBack={() => { setCustomMode(false); setCustomError(null); }} error={customError ?? errorMessage} submitting={false} /> : <div className="journey-form-layout"><form className="goal-form card" onSubmit={(event: FormEvent) => { event.preventDefault(); void send(); }}><span className="eyebrow">NEW JOURNEY</span><h2>Define your journey</h2><label>Demo customer<select value={customer.id} onChange={(event) => selectDemo(demoCustomers.find((demo) => demo.id === event.target.value) ?? defaultDemo)}>{demoCustomers.map((demo) => <option key={demo.id} value={demo.id}>{demo.name} · {demo.outcomeHint}</option>)}</select></label><label>Financial goal<textarea value={goal} maxLength={500} onChange={(event) => setGoal(event.target.value)} required /></label><label>Requested amount<span className="amount-input"><span>₹</span><input value={amount} inputMode="numeric" onChange={(event) => setAmount(event.target.value.replace(/[^0-9]/g, ""))} required /></span><small>{Number(amount) > 0 ? formatCurrency(Number(amount)) : "Enter a whole amount"}</small></label><button className="button button-primary button-large" type="submit">Analyze my journey <span>→</span></button></form><div><button type="button" className="button button-secondary new-customer-trigger" onClick={() => setCustomMode(true)}>+ New Customer</button><DemoSelector selectedId={customer.id} onSelect={selectDemo} /></div></div>}</div>;
}
