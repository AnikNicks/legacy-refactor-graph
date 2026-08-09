import type { ExampleManifestEntry } from "../types";
import { categorySlot } from "../lib/tokens";

export function ExampleSelector({
  examples,
  selected,
  onSelect,
}: {
  examples: ExampleManifestEntry[];
  selected: ExampleManifestEntry | null;
  onSelect: (slug: string) => void;
}) {
  if (examples.length === 0) {
    return <div className="example-selector empty">Loading examples…</div>;
  }

  return (
    <div className="example-selector">
      <label htmlFor="example-select" className="example-selector-label">
        Example target
      </label>
      <div className="example-selector-row">
        <span className={`category-dot category-slot-${categorySlot(selected?.category ?? "")}`} />
        <select
          id="example-select"
          value={selected?.slug ?? ""}
          onChange={(e) => onSelect(e.target.value)}
        >
          {examples.map((ex) => (
            <option key={ex.slug} value={ex.slug}>
              {ex.name} — {ex.category}
            </option>
          ))}
        </select>
      </div>
      {selected && (
        <div className="example-selector-detail">
          <p>{selected.description}</p>
          <div className="example-selector-meta">
            <span className="tag">
              {selected.runDepth === "full" ? "Full 6-phase run" : "Analysis only (Phases 0–2)"}
            </span>
            <span className="example-flagship">Flagship risk: {selected.flagshipRisk}</span>
          </div>
        </div>
      )}
    </div>
  );
}
