import { statusLabel, statusRole, type StatusRole } from "../lib/tokens";

// Icon + label always together — a status color never carries meaning alone
// (reference palette: warning/serious sit under 3:1 contrast on the light
// surface by design; the icon+label pairing is the documented mitigation).
const ROLE_GLYPH: Record<StatusRole, string> = {
  good: "✓", // check
  warning: "●", // filled circle — in progress / needs attention
  serious: "▲", // triangle
  critical: "✕", // cross
  muted: "○", // hollow circle — not started
};

export function StatusBadge({ status, label }: { status: string; label?: string }) {
  const role = statusRole(status);
  return (
    <span className={`status-badge status-${role}`}>
      <span className="status-badge-glyph" aria-hidden="true">
        {ROLE_GLYPH[role]}
      </span>
      {label ?? statusLabel(status)}
    </span>
  );
}

export function RiskBadge({ level }: { level: string }) {
  const role = level === "low" ? "good" : level === "high" ? "critical" : "warning";
  return (
    <span className={`status-badge status-${role}`}>
      <span className="status-badge-glyph" aria-hidden="true">
        {ROLE_GLYPH[role]}
      </span>
      {level} risk
    </span>
  );
}
