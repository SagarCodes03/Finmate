export function JourneyProgress() {
  return (
    <section className="progress-card" aria-live="polite">
      <span className="eyebrow">JOURNEY ANALYSIS</span>
      <h1>Preparing your journey</h1>
      <p>FinMate is coordinating the governed journey. These are general processing stages, not live backend telemetry.</p>
      <ol className="progress-steps">
        <li className="complete">Preparing your journey</li>
        <li className="active">Gathering available context</li>
        <li>Evaluating the journey</li>
        <li>Preparing the next step</li>
      </ol>
      <div className="progress-line"><span /></div>
    </section>
  );
}
