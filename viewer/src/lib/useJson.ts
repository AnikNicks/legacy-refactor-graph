import { useEffect, useState } from "react";

export function useJson<T>(path: string, pollMs = 3000): { data: T | null; error: string | null } {
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Clear stale data the instant `path` changes (e.g. switching example
  // targets) rather than leaving the previous target's data on screen until
  // the next fetch resolves — otherwise a 404 for the new path (a target
  // that legitimately hasn't reached this phase yet) would leave the old
  // target's data displayed indefinitely instead of showing this panel's
  // empty state.
  useEffect(() => {
    setData(null);
    setError(null);
  }, [path]);

  useEffect(() => {
    let cancelled = false;

    const load = async () => {
      try {
        const res = await fetch(`/data/${path}?t=${Date.now()}`);
        if (!res.ok) {
          if (!cancelled) {
            setData(null);
            setError(`${path}: HTTP ${res.status}`);
          }
          return;
        }
        const json = (await res.json()) as T;
        if (!cancelled) {
          setData(json);
          setError(null);
        }
      } catch (e) {
        if (!cancelled) setError(String(e));
      }
    };

    load();
    const id = setInterval(load, pollMs);
    return () => {
      cancelled = true;
      clearInterval(id);
    };
  }, [path, pollMs]);

  return { data, error };
}
