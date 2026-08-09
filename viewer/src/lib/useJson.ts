import { useEffect, useState } from "react";

export function useJson<T>(path: string, pollMs = 3000): { data: T | null; error: string | null } {
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    const load = async () => {
      try {
        const res = await fetch(`/data/${path}?t=${Date.now()}`);
        if (!res.ok) {
          if (!cancelled) setError(`${path}: HTTP ${res.status}`);
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
