import type { RiskAssessment } from "../types";

export function RiskPanel({ data }: { data: RiskAssessment | null }) {
  if (!data) {
    return (
      <div className="panel">
        <h2>Risk ranking</h2>
        <p className="empty">No risk_assessment.json yet — Phase 2 hasn't run.</p>
      </div>
    );
  }

  const maxScore = Math.max(...data.ranked_modules.map((m) => m.total_score), 1);

  return (
    <div className="panel">
      <h2>Risk ranking</h2>
      <ol className="risk-list">
        {data.ranked_modules.map((m, i) => (
          <li key={m.module} className="risk-row">
            <div className="risk-row-head">
              <span className="risk-rank">#{i + 1}</span>
              <span className="risk-module">{m.module}</span>
              <span className="risk-total">{m.total_score.toFixed(1)}</span>
            </div>
            <div className="risk-meter-track">
              <div
                className="risk-meter-fill"
                style={{ width: `${(m.total_score / maxScore) * 100}%` }}
              />
            </div>
            <div className="risk-breakdown">
              churn <b>{m.churn_score.toFixed(1)}</b> · complexity{" "}
              <b>{m.complexity_score.toFixed(1)}</b> · coupling <b>{m.coupling_score.toFixed(1)}</b>{" "}
              · security <b>{m.security_score.toFixed(1)}</b>
            </div>
            <p className="risk-rationale">{m.rationale}</p>
          </li>
        ))}
      </ol>

      {data.findings.length > 0 && (
        <>
          <h3>Findings</h3>
          <ul className="findings-list">
            {data.findings.map((f, i) => (
              <li key={i}>{f}</li>
            ))}
          </ul>
        </>
      )}
    </div>
  );
}
