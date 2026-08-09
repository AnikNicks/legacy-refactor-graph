import type { RiskAssessment } from "../types";

export function RiskPanel({ data }: { data: RiskAssessment | null }) {
  if (!data) {
    return (
      <div className="panel">
        <h2>Risk ranking</h2>
        <p className="empty">No output/risk_assessment.json yet — Phase 2 hasn't run.</p>
      </div>
    );
  }

  return (
    <div className="panel">
      <h2>Risk ranking</h2>
      <table>
        <thead>
          <tr>
            <th>#</th>
            <th>Module</th>
            <th>Total</th>
            <th>Churn</th>
            <th>Complexity</th>
            <th>Coupling</th>
            <th>Security</th>
          </tr>
        </thead>
        <tbody>
          {data.ranked_modules.map((m, i) => (
            <tr key={m.module}>
              <td>{i + 1}</td>
              <td>{m.module}</td>
              <td>
                <strong>{m.total_score.toFixed(1)}</strong>
              </td>
              <td>{m.churn_score.toFixed(1)}</td>
              <td>{m.complexity_score.toFixed(1)}</td>
              <td>{m.coupling_score.toFixed(1)}</td>
              <td>{m.security_score.toFixed(1)}</td>
            </tr>
          ))}
        </tbody>
      </table>

      {data.findings.length > 0 && (
        <>
          <h3>Findings</h3>
          <ul>
            {data.findings.map((f, i) => (
              <li key={i}>{f}</li>
            ))}
          </ul>
        </>
      )}
    </div>
  );
}
