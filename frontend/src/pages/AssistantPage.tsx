import { useState, type FormEvent } from "react";
import { sendAssistantMessage } from "../api/assistant";
import { demoCustomers } from "../data/demos";
import { useJourneyStore } from "../hooks/useJourneyStore";
import type { ChatMessage } from "../types/chat";
import { formatCurrency } from "../utils/format";

const suggestedPrompts = ["Why was my journey not suitable?", "What can I do to reach my financial goal?", "Explain my risk assessment", "What documents are missing?"];
const welcomeMessage: ChatMessage = { id: "welcome", role: "assistant", content: "I’m the FinMate AI Assistant. I explain governed prototype evidence, but cannot make or change financial decisions." };

export function AssistantPage() {
  const { result, currentCustomerId } = useJourneyStore();
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState<ChatMessage[]>([welcomeMessage]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [toolsUsed, setToolsUsed] = useState<string[]>([]);
  const customer = demoCustomers.find((item) => item.id === currentCustomerId);
  const canChat = Boolean(currentCustomerId && result);

  const sendMessage = async (message = input) => {
    const trimmed = message.trim();
    if (!trimmed || isLoading || !currentCustomerId || !result) return;
    const history = messages.filter((item) => item.id !== welcomeMessage.id);
    setMessages((current) => [...current, { id: `${Date.now()}-user`, role: "user", content: trimmed }]);
    setInput(""); setError(null); setIsLoading(true);
    try {
      const reply = await sendAssistantMessage({ customer_id: currentCustomerId, message: trimmed, conversation_history: history, current_journey: result });
      setMessages((current) => [...current, { id: `${Date.now()}-assistant`, role: "assistant", content: reply.response }]);
      setToolsUsed(reply.tools_used);
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "FinMate AI Assistant is unavailable.");
    } finally { setIsLoading(false); }
  };
  const onSubmit = (event: FormEvent) => { event.preventDefault(); void sendMessage(); };

  return <div className="assistant-page"><section className="assistant-heading"><div><span className="eyebrow">FINMATE AI ASSISTANT</span><h1>Ask about your journey context.</h1><p>The assistant explains governed backend evidence; financial decisions remain outside the LLM.</p></div><span className="assistant-status">Governed LLM / tools connected</span></section><div className="assistant-layout"><aside className="assistant-context card"><span className="eyebrow">CURRENT JOURNEY CONTEXT</span><h2>Conversation context</h2>{customer && result ? <dl><div><dt>Customer</dt><dd>{customer.name}</dd></div><div><dt>Goal</dt><dd>{result.customer_goal}</dd></div><div><dt>Requested amount</dt><dd>{formatCurrency(result.requested_amount)}</dd></div><div><dt>Data source</dt><dd>Simulated demo data</dd></div></dl> : <p className="muted">Start a governed journey first. The Assistant will use that journey’s customer and evidence.</p>}{result && <div className="current-journey"><strong>Current returned journey</strong><span>{result.customer_goal} · {formatCurrency(result.requested_amount)}</span><span>Policy: {result.policy_decision.decision}</span></div>}<div className="tool-indicators" aria-label="Assistant tools used">{toolsUsed.length ? toolsUsed.map((tool) => <span key={tool}>{tool}</span>) : <span>No tools used yet</span>}</div></aside><section className="chat-panel card" aria-label="FinMate AI Assistant chat"><div className="chat-messages" aria-live="polite">{messages.map((item) => <article className={`chat-message ${item.role}`} key={item.id}><span>{item.role === "assistant" ? "FinMate AI" : "You"}</span><p>{item.content}</p></article>)}{isLoading && <article className="chat-message assistant loading"><span>FinMate AI</span><p>Retrieving governed context…</p></article>}</div>{error && <div className="chat-error" role="alert"><strong>Assistant unavailable</strong><span>{error}</span></div>}<div className="suggested-prompts"><span>Suggested prompts</span><div>{suggestedPrompts.map((prompt) => <button key={prompt} type="button" onClick={() => void sendMessage(prompt)} disabled={isLoading || !canChat}>{prompt}</button>)}</div></div><form className="chat-composer" onSubmit={onSubmit}><label htmlFor="assistant-message">Message FinMate AI</label><div><input id="assistant-message" value={input} onChange={(event) => { setInput(event.target.value); setError(null); }} placeholder={canChat ? "Ask about the current journey context" : "Start a journey to enable the Assistant"} disabled={isLoading || !canChat} /><button className="button button-primary" type="submit" disabled={!input.trim() || isLoading || !canChat}>{isLoading ? "Sending…" : "Send"}</button></div></form><p className="form-note">Messages stay in this browser session. Gemini receives only this conversation and governed prototype evidence; it cannot make financial decisions.</p></section></div></div>;
}
