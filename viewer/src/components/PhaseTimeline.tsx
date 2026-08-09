import type { ProgressState } from "../types";
import { StatusBadge } from "./StatusBadge";

const PHASE_LABEL: Record<string, string> = {
  preflight: "Preflight",
  archaeologist: "Archaeologist",
  risk_assessor: "Risk assessor",
  fan_out: "Test writer + refactor planner",
  human_gate: "Human gate",
  stage_execution: "Stage execution",
  synthesis: "Synthesis",
};

export function PhaseTimeline({ progress }: { progress: ProgressState | null }) {
  if (!progress) {
    return <div className="panel">Waiting for progress_state.json…</div>;
  }

  return (
    <div className="panel">
      <div className="panel-header-row">
        <h2>
          Phase timeline <span className="panel-subtitle">{progress.target}</span>
        </h2>
        {progress.branch && <span className="branch-tag">{progress.branch}</span>}
      </div>
      <div className="phase-row">
        {progress.phases.map((p) => (
          <div key={p.phase} className="phase-chip">
            <div className="phase-chip-title">
              Phase {p.phase} · {PHASE_LABEL[p.name] ?? p.name}
            </div>
            <StatusBadge status={p.status} />
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
