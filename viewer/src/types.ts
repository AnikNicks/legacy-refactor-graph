// Mirrors scripts/schemas.py and the progress_state.json shape the
// orchestrator writes in .claude/commands/refactor-legacy-app.md. Keep these
// in sync by hand — there's no codegen step tying the two together.

export interface StageState {
  id: number;
  module: string;
  status: "pending" | "in_progress" | "approved" | "modified" | "rejected" | "failed";
  summary: string;
}

export interface PhaseState {
  phase: string;
  name: string;
  status: "not_started" | "in_progress" | "awaiting_approval" | "complete" | "blocked";
  summary: string;
  timestamp: string | null;
  stages?: StageState[];
}

export interface ProgressState {
  target: string;
  branch: string | null;
  status: string;
  phases: PhaseState[];
  blockers: string[];
}

export interface ModuleInventoryEntry {
  name: string;
  path: string;
  loc: number;
  churn_commits: number;
  description: string;
}

export interface EntryPoint {
  module: string;
  path: string;
  kind: string;
  description: string;
}

export interface CouplingNote {
  from_module: string;
  to_module: string;
  description: string;
  evidence: string;
}

export interface SchemaTable {
  name: string;
  columns: string[];
  foreign_keys: string[];
}

export interface ArchaeologyReport {
  target: string;
  modules: ModuleInventoryEntry[];
  entry_points: EntryPoint[];
  schema_tables: SchemaTable[];
  coupling_notes: CouplingNote[];
  deep_dive_notes: string[];
}

export interface ModuleRiskScore {
  module: string;
  churn_score: number;
  complexity_score: number;
  coupling_score: number;
  security_score: number;
  total_score: number;
  rationale: string;
}

export interface RiskAssessment {
  target: string;
  ranked_modules: ModuleRiskScore[];
  findings: string[];
}

export type RefactorPattern =
  | "strangler-fig"
  | "branch-by-abstraction"
  | "direct"
  | "contract-test-only";

export interface Stage {
  id: number;
  module: string;
  description: string;
  target_files: string[];
  pattern: RefactorPattern;
  risk_level: "low" | "medium" | "high";
  acceptance_criteria: string[];
  depends_on: number[];
}

export interface RefactorPlan {
  target: string;
  stages: Stage[];
}
