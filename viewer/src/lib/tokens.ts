// Status and categorical color assignment, following the reference palette:
// status colors are a fixed, reserved four-role set (never themed, never
// reused for a category), categorical hues are assigned in a fixed order
// and never cycled. See CSS custom properties in index.css for the actual
// hex values per mode — this file only maps *meaning* to *role name*.

export type StatusRole = "good" | "warning" | "serious" | "critical" | "muted";

const PHASE_STATUS_ROLE: Record<string, StatusRole> = {
  complete: "good",
  approved: "good",
  in_progress: "warning",
  awaiting_approval: "warning",
  pending: "muted",
  not_started: "muted",
  modified: "warning",
  blocked: "critical",
  rejected: "critical",
  failed: "critical",
};

export function statusRole(status: string): StatusRole {
  return PHASE_STATUS_ROLE[status] ?? "muted";
}

const RISK_LEVEL_ROLE: Record<string, StatusRole> = {
  low: "good",
  medium: "warning",
  high: "critical",
};

export function riskLevelRole(level: string): StatusRole {
  return RISK_LEVEL_ROLE[level] ?? "muted";
}

// Fixed categorical order — slot 1..4, never reassigned or cycled past 4.
const CATEGORY_SLOT: Record<string, 1 | 2 | 3 | 4> = {
  "General SaaS": 1,
  "E-Commerce": 2,
  Healthcare: 3,
  Fintech: 4,
};

export function categorySlot(category: string): 1 | 2 | 3 | 4 {
  return CATEGORY_SLOT[category] ?? 1;
}

export function statusLabel(status: string): string {
  return status.replace(/_/g, " ");
}
