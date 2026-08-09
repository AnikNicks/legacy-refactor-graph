import type { ArchaeologyReport } from "../types";

export function ArchaeologyPanel({ data }: { data: ArchaeologyReport | null }) {
  if (!data) {
    return (
      <div className="panel">
        <h2>Archaeology</h2>
        <p className="empty">No output/archaeology.json yet — Phase 1 hasn't run.</p>
      </div>
    );
  }

  return (
    <div className="panel">
      <h2>Archaeology</h2>
      <h3>Modules</h3>
      <table>
        <thead>
          <tr>
            <th>Module</th>
            <th>Path</th>
            <th>LOC</th>
            <th>Churn</th>
            <th>Description</th>
          </tr>
        </thead>
        <tbody>
          {data.modules.map((m) => (
            <tr key={m.name}>
              <td>{m.name}</td>
              <td>
                <code>{m.path}</code>
              </td>
              <td>{m.loc}</td>
              <td>{m.churn_commits}</td>
              <td>{m.description}</td>
            </tr>
          ))}
        </tbody>
      </table>

      <h3>Entry points</h3>
      <ul>
        {data.entry_points.map((e, i) => (
          <li key={i}>
            <code>{e.path}</code> ({e.kind}) — {e.description}
          </li>
        ))}
      </ul>

      {data.coupling_notes.length > 0 && (
        <>
          <h3>Cross-module coupling</h3>
          <ul>
            {data.coupling_notes.map((c, i) => (
              <li key={i}>
                <strong>
                  {c.from_module} → {c.to_module}
                </strong>
                : {c.description}
              </li>
            ))}
          </ul>
        </>
      )}
    </div>
  );
}
