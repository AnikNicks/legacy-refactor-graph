export function SynthesisPanel({ text }: { text: string | null }) {
  if (!text) {
    return (
      <div className="panel">
        <h2>Synthesis / roadmap</h2>
        <p className="empty">No output/synthesis_report.md yet — Phase 6 hasn't run.</p>
      </div>
    );
  }

  return (
    <div className="panel">
      <h2>Synthesis / roadmap</h2>
      <pre className="markdown-raw">{text}</pre>
    </div>
  );
}
