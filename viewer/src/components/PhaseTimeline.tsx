import type { ProgressState } from "../types";

const STATUS_COLOR: Record<string, string> = {
  not_started: "var(--muted)",
  in_progress: "var(--amber)",
  awaiting_approval: "var(--violet)",
  complete: "var(--green)",
  blocked: "var(--red)",
};

export function PhaseTimeline({ progress }: { progress: ProgressState | null }) {
  if (!progress) {
    return <div className="panel">Waiting for output/progress_state.json…</div>;
  }

  return (
    <div className="panel">
      <h2>
        Phase timeline — {progress.target}
        {progress.branch && <span className="branch-tag">{progress.branch}</span>}
      </h2>
      <div className="phase-row">
        {progress.phases.map((p) => (
          <div key={p.phase} className="phase-chip" style={{ borderColor: STATUS_COLOR[p.status] }}>
            <div className="phase-chip-title">
              Phase {p.phase}: {p.name}
            </div>
            <div className="phase-chip-status" style={{ color: STATUS_COLOR[p.status] }}>
              {p.status.replace("_", " ")}
            </div>
            {p.summary && <div className="phase-chip-summary">{p.summary}</div>}
          </div>
        ))}
      </div>
      {progress.blockers.length > 0 && (
        <div className="blockers">
          <strong>Blockers</strong>
          <ul>
            {progress.blockers.map((b, i) => (
              <li key={i}>{b}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
