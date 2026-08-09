import type { RefactorPlan, StageState } from "../types";

const RISK_COLOR: Record<string, string> = {
  low: "var(--green)",
  medium: "var(--amber)",
  high: "var(--red)",
};

export function RefactorPlanPanel({
  plan,
  stageStates,
}: {
  plan: RefactorPlan | null;
  stageStates: StageState[];
}) {
  if (!plan) {
    return (
      <div className="panel">
        <h2>Refactor plan</h2>
        <p className="empty">No output/refactor_plan.json yet — Phase 3 hasn't run.</p>
      </div>
    );
  }

  const stateFor = (id: number) => stageStates.find((s) => s.id === id);

  return (
    <div className="panel">
      <h2>Refactor plan — {plan.stages.length} stages</h2>
      {plan.stages.map((s) => {
        const state = stateFor(s.id);
        return (
          <div key={s.id} className="stage-card" style={{ borderLeftColor: RISK_COLOR[s.risk_level] }}>
            <div className="stage-card-header">
              <strong>
                Stage {s.id}: {s.module}
              </strong>
              <span className="tag pattern-tag">{s.pattern}</span>
              <span className="tag" style={{ color: RISK_COLOR[s.risk_level] }}>
                {s.risk_level} risk
              </span>
              {state && <span className="tag status-tag">{state.status}</span>}
              {s.depends_on.length > 0 && (
                <span className="tag depends-tag">depends on {s.depends_on.join(", ")}</span>
              )}
            </div>
            <p>{s.description}</p>
            <div className="stage-files">{s.target_files.join(", ")}</div>
            <ul>
              {s.acceptance_criteria.map((c, i) => (
                <li key={i}>{c}</li>
              ))}
            </ul>
            {state?.summary && <div className="stage-result-summary">{state.summary}</div>}
          </div>
        );
      })}
    </div>
  );
}
