import type { RefactorPlan, StageState } from "../types";
import { RiskBadge, StatusBadge } from "./StatusBadge";

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
        <p className="empty">No refactor_plan.json yet — Phase 3 hasn't run.</p>
      </div>
    );
  }

  const stateFor = (id: number) => stageStates.find((s) => s.id === id);

  return (
    <div className="panel">
      <h2>
        Refactor plan <span className="panel-subtitle">{plan.stages.length} stages</span>
      </h2>
      {plan.stages.map((s) => {
        const state = stateFor(s.id);
        return (
          <div key={s.id} className="stage-card">
            <div className="stage-card-header">
              <strong>
                Stage {s.id} · {s.module}
              </strong>
              <span className="tag pattern-tag">{s.pattern}</span>
              <RiskBadge level={s.risk_level} />
              {state && <StatusBadge status={state.status} />}
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
