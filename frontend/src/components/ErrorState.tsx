export function ErrorState({ title = "We could not complete this journey", message, onRetry }: { title?: string; message: string; onRetry?: () => void }) {
  return (
    <section className="error-state" role="alert">
      <span className="error-icon">!</span>
      <div><h1>{title}</h1><p>{message}</p><p className="muted">Make sure FastAPI and n8n are running.</p></div>
      {onRetry && <button className="button button-primary" onClick={onRetry}>Retry</button>}
    </section>
  );
}
