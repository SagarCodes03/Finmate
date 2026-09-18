import { useState, type FormEvent } from "react";
import { useNavigate } from "react-router-dom";
import { DemoSelector } from "../components/DemoSelector";
import { ErrorState } from "../components/ErrorState";
import { JourneyProgress } from "../components/JourneyProgress";
import { demoCustomers, type DemoCustomer } from "../data/demos";
import { useJourneyStore } from "../hooks/useJourneyStore";
import { newJourneyId, formatCurrency } from "../utils/format";

export function NewJourneyPage() {
  const defaultDemo = demoCustomers[3];
  const [customer, setCustomer] = useState<DemoCustomer>(defaultDemo);
  const [goal, setGoal] = useState(defaultDemo.goal);
  const [amount, setAmount] = useState(String(defaultDemo.amount));
  const { status, errorMessage, submit } = useJourneyStore();
  const navigate = useNavigate();

  const selectDemo = (demo: DemoCustomer) => { setCustomer(demo); setGoal(demo.goal); setAmount(String(demo.amount)); };
  const send = async () => {
    const requestedAmount = Number(amount.replace(/[^0-9]/g, ""));
    if (!goal.trim() || !Number.isSafeInteger(requestedAmount) || requestedAmount <= 0) return;
    const result = await submit({ journey_id: newJourneyId(), customer_id: customer.id, customer_goal: goal.trim(), requested_amount: requestedAmount });
    if (result) navigate("/journey");
  };
  const onSubmit = (event: FormEvent) => { event.preventDefault(); void send(); };

  if (status === "SUBMITTING") return <JourneyProgress />;
  if (["API_UNAVAILABLE", "INVALID_RESPONSE", "ERROR"].includes(status) && errorMessage) return <ErrorState message={errorMessage} onRetry={() => void send()} />;
  return <div className="new-journey-page"><section className="hero-card"><div><span className="eyebrow">GOVERNED FINANCIAL JOURNEYS</span><h1>What are you trying to achieve?</h1><p>Start with a goal. FinMate coordinates the journey and presents the backend’s governed result.</p></div><div className="hero-rule">AI orchestrates.<br />ML + Rules govern.<br />Humans oversee.</div></section><div className="journey-form-layout"><form className="goal-form card" onSubmit={onSubmit}><span className="eyebrow">NEW JOURNEY</span><h2>Define your journey</h2><label>Demo customer<select value={customer.id} onChange={(event) => selectDemo(demoCustomers.find((demo) => demo.id === event.target.value) ?? defaultDemo)}>{demoCustomers.map((demo) => <option key={demo.id} value={demo.id}>{demo.name} · {demo.outcomeHint}</option>)}</select></label><label>Financial goal<textarea value={goal} maxLength={500} onChange={(event) => setGoal(event.target.value)} placeholder="Describe the goal you want to pursue" required /></label><label>Requested amount<span className="amount-input"><span>₹</span><input value={amount} inputMode="numeric" onChange={(event) => setAmount(event.target.value.replace(/[^0-9]/g, ""))} required /></span><small>{Number(amount) > 0 ? formatCurrency(Number(amount)) : "Enter a whole amount"}</small></label><button className="button button-primary button-large" type="submit">Analyze my journey <span>→</span></button><p className="form-note">FinMate sends this journey to the governed backend. It does not make a decision in your browser.</p></form><DemoSelector selectedId={customer.id} onSelect={selectDemo} /></div></div>;
}
