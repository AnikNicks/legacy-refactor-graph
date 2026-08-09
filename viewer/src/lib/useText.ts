import { useEffect, useState } from "react";

export function useText(path: string, pollMs = 5000): string | null {
  const [text, setText] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    const load = async () => {
      try {
        const res = await fetch(`/data/${path}?t=${Date.now()}`);
        if (res.ok) {
          const t = await res.text();
          if (!cancelled) setText(t);
        }
      } catch {
        // Not written yet (e.g. synthesis_report.md before Phase 6) — leave as null.
      }
    };

    load();
    const id = setInterval(load, pollMs);
    return () => {
      cancelled = true;
      clearInterval(id);
    };
  }, [path, pollMs]);

  return text;
}
