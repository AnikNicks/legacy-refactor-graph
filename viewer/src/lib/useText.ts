import { useEffect, useState } from "react";

export function useText(path: string, pollMs = 5000): string | null {
  const [text, setText] = useState<string | null>(null);

  // Same reset-on-path-change fix as useJson — otherwise switching targets
  // leaves the previous target's synthesis report on screen indefinitely
  // once its own path 404s (e.g. an analysis-only target with no Phase 6).
  useEffect(() => {
    setText(null);
  }, [path]);

  useEffect(() => {
    let cancelled = false;

    const load = async () => {
      try {
        const res = await fetch(`data/${path}?t=${Date.now()}`);
        if (res.ok) {
          const t = await res.text();
          if (!cancelled) setText(t);
        } else if (!cancelled) {
          setText(null);
        }
      } catch {
        if (!cancelled) setText(null);
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
