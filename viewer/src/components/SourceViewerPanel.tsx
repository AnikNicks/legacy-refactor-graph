import { useEffect, useState } from "react";

export function SourceViewerPanel({ target }: { target: string }) {
  const [files, setFiles] = useState<string[]>([]);
  const [selected, setSelected] = useState<string | null>(null);
  const [content, setContent] = useState<string>("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    let cancelled = false;
    setFiles([]);
    setSelected(null);
    setContent("");

    fetch(`source-data/${target}/__index__.json?t=${Date.now()}`)
      .then((r) => r.json())
      .then((list: string[]) => {
        if (cancelled) return;
        setFiles(list);
        const entry = list.find((f) => f.endsWith("app.py")) ?? list[0] ?? null;
        setSelected(entry);
      })
      .catch(() => {
        if (!cancelled) setFiles([]);
      });

    return () => {
      cancelled = true;
    };
  }, [target]);

  useEffect(() => {
    if (!selected) return;
    let cancelled = false;
    setLoading(true);
    fetch(`source-data/${target}/${selected}?t=${Date.now()}`)
      .then((r) => r.text())
      .then((text) => {
        if (!cancelled) setContent(text);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [target, selected]);

  return (
    <div className="panel">
      <h2>Source — {target}</h2>
      {files.length === 0 ? (
        <p className="empty">No source files found for this target.</p>
      ) : (
        <div className="source-viewer">
          <div className="source-file-list">
            {files.map((f) => (
              <button
                key={f}
                type="button"
                className={`source-file-item${f === selected ? " active" : ""}`}
                onClick={() => setSelected(f)}
              >
                {f}
              </button>
            ))}
          </div>
          <pre className="source-code">{loading ? "Loading…" : content}</pre>
        </div>
      )}
    </div>
  );
}
