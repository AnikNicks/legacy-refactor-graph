import type { ArchaeologyReport } from "../types";

export function ArchaeologyPanel({ data }: { data: ArchaeologyReport | null }) {
  if (!data) {
    return (
      <div className="panel">
        <h2>Archaeology</h2>
        <p className="empty">No archaeology.json yet — Phase 1 hasn't run.</p>
      </div>
    );
  }

  const entryPointsByModule = new Map<string, typeof data.entry_points>();
  for (const ep of data.entry_points) {
    const list = entryPointsByModule.get(ep.module) ?? [];
    list.push(ep);
    entryPointsByModule.set(ep.module, list);
  }

  return (
    <div className="panel">
      <h2>Archaeology</h2>

      <h3>Modules</h3>
      <table className="data-table">
        <thead>
          <tr>
            <th>Module</th>
            <th className="num">LOC</th>
            <th className="num">Churn</th>
            <th>What it does</th>
          </tr>
        </thead>
        <tbody>
          {data.modules.map((m) => (
            <tr key={m.name}>
              <td>
                <code>{m.name}</code>
              </td>
              <td className="num">{m.loc}</td>
              <td className="num">{m.churn_commits}</td>
              <td className="description-cell">{m.description}</td>
            </tr>
          ))}
        </tbody>
      </table>

      <h3>Entry points</h3>
      <div className="entry-point-groups">
        {data.modules.map((m) => {
          const eps = entryPointsByModule.get(m.name);
          if (!eps || eps.length === 0) return null;
          return (
            <div key={m.name} className="entry-point-group">
              <div className="entry-point-group-title">{m.name}</div>
              <ul>
                {eps.map((e, i) => (
                  <li key={i}>{e.description}</li>
                ))}
              </ul>
            </div>
          );
        })}
      </div>

      {data.coupling_notes.length > 0 && (
        <>
          <h3>Cross-module coupling</h3>
          <ul className="coupling-list">
            {data.coupling_notes.map((c, i) => (
              <li key={i}>
                <span className="coupling-edge">
                  {c.from_module} → {c.to_module}
                </span>
                {c.description}
              </li>
            ))}
          </ul>
        </>
      )}
    </div>
  );
}
