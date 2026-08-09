# Pipeline architecture

This is the architecture spec for the legacy-refactor-agent pipeline: the phase DAG, each node's
input/output contract, and the strategy that lets the same six agents work against anything from
a small fixture to a real, large SaaS monorepo. This document doesn't change between runs — for
the state of any specific run, see `PROGRESS.md` (human-readable) and `output/progress_state.json`
(machine-readable).

## Why a graph, not a linear script

Some phases genuinely depend on their predecessor's output (archaeologist before risk-assessor —
you can't score risk on modules you haven't inventoried yet). Others don't (test-writer and
refactor-planner both only need archaeology + risk data, not each other), so they run in parallel.
Modeling this explicitly as a DAG is what makes the "read only what this phase needs" discipline
well-defined, and what makes the fan-out in Phase 3 correct instead of accidental.

**Note on what "graph" means here**: this file is a spec, not a graph-execution engine. There's no
state-machine library walking nodes and edges at runtime — `.claude/commands/refactor-legacy-app.md`
follows this DAG as hand-written numbered steps. The graph is a real design; it just isn't a data
structure any code traverses.

## The DAG

```
Phase 0  preflight(target)
              │
Phase 1  archaeologist   → output/archaeology.json
              │
Phase 2  risk-assessor   → output/risk_assessment.json
              │
Phase 3  fan-out (parallel)
    ┌─────────────┴─────────────┐
    test-writer         refactor-planner
    → tests/            → output/refactor_plan.json
    └─────────────┬─────────────┘
              │
Phase 4  HUMAN GATE (no agent)
              │
Phase 5  stage-executor × N (sequential, one dispatch per stage)
         → output/stage_N_result.json (+ commit, only after per-stage approval)
              │
Phase 6  synthesizer     → output/synthesis_report.md
```

## Node contracts

### Phase 0 — preflight
- **Input**: target path (`$ARGUMENTS` to `/refactor-legacy-app`, defaults to `legacy-app/`).
- **Action**: `scripts/validate_state.py preflight --target <path>` — confirms the target exists,
  a git repo is present, the current branch is not `main`, `output/` is writable.
- **Output**: none (a gate, not a producer). Creates branch `refactor/<target-slug>` if it doesn't
  already exist.

### Phase 1 — archaeologist
- **Input**: target path only.
- **Tools**: Read, Grep, Glob, Write, SQLite MCP (read-only queries against
  `legacy-app/shared/data.db`).
- **Strategy — two-tier, this is the part that scales**:
  1. **Tier 1 (repo-wide inventory)**: walk the directory tree, get per-module LOC and git-churn
     stats (`git log --stat`), read manifest/dependency files, identify entry points — without
     reading every file's full contents. Produces a module map.
  2. **Tier 2 (targeted deep-read)**: read in full only the entry points and whatever tier 1
     flags as high-signal (unusually large, unusually churned, or named like an integration
     point). Schema-level facts (tables, columns, foreign keys) come from the SQLite MCP, not from
     grepping SQL strings out of source.
  This is what lets the same agent design work whether the target is a 400-line fixture or a real
  monorepo — tier 1 never blows its context budget because it summarizes, and `output/*.json`
  never contains more raw source than a downstream phase actually needs.
- **Output**: `output/archaeology.json` — module inventory, entry points, schema summary,
  cross-module coupling notes, deep-dive findings. Validated against `ArchaeologyReport` in
  `scripts/schemas.py`.

### Phase 2 — risk-assessor
- **Input**: `output/archaeology.json` + targeted source reads.
- **Tools**: Read, Grep, Write, SQLite MCP (read-only).
- **Strategy**: score each module on four axes — churn (from archaeology's git stats),
  complexity (rough heuristic: branching/nesting density), coupling (cross-module references,
  foreign keys via the MCP), security-surface (injection-prone SQL, plaintext secrets, unvalidated
  input). Produces a ranked priority list, not a flat report — this ranking is what makes the rest
  of the run's ordering defensible.
- **Output**: `output/risk_assessment.json` — validated against `RiskAssessment`.

### Phase 3 — fan-out: test-writer + refactor-planner (parallel)
Both read `archaeology.json` + `risk_assessment.json` and nothing else from earlier phases;
neither reads the other's output — that's what makes running them concurrently correct.

- **test-writer** (Read, Write, Bash): writes black-box characterization tests per prioritized
  module — HTTP request/response pairs against the target's actual routes, not unit tests of
  internals the refactor is about to change. Runs pytest to confirm they pass against the
  unmodified target before Phase 5 touches anything. → `tests/`.
- **refactor-planner** (Read, Write): produces an ordered stage plan, sequenced by
  risk-assessor's ranking, using standard incremental-modernization patterns per stage:
  - **strangler-fig** — build the new implementation alongside the old, routed behind a seam,
    cut over once proven equivalent.
  - **branch-by-abstraction** — introduce the seam/interface before extracting anything, so the
    codebase is never in a half-migrated state with no clean rollback.
  - **contract tests** — before cutover, a stage's acceptance criteria include proving old and
    new paths produce equivalent output, not just "new code passes its own tests."
  → `output/refactor_plan.json` — `RefactorPlan` with ordered `stages: list[Stage]`, each carrying
  module, target files, pattern used, risk level, acceptance criteria.

### Phase 4 — human gate
No agent runs. I present the full `refactor_plan.json` (every stage, files touched, pattern,
risk level, acceptance criteria) plus the written test files. **No Phase 5 dispatch happens
without explicit approval.**

### Phase 5 — stage-executor × N
One dispatch per stage in `refactor_plan.json`, strictly sequential (a later stage may depend on
an earlier one's seam existing). Per stage:
1. Dispatch `stage-executor` (Read, Edit, Write, Bash) for that one stage only. It implements the
   change and runs the characterization tests. **It does not commit.**
2. Tests fail → one guarded retry with the failure appended to its prompt. Fails again → stop the
   whole run, report which stage/test failed.
3. Tests pass → **stop for a human checkpoint.** Show the diff (uncommitted), test results, and
   the stage's acceptance criteria. Approve as-is, request a specific change (re-dispatch with
   feedback, re-test, re-present), or reject (skip, log why, continue to the next stage unless a
   later stage depends on this one).
4. Only after approval: commit on the refactor branch, run
   `validate_state.py stage-diff-check --stage <n> --target <path>` (confirms the diff touched
   only `<target>/` and `tests/`), write `output/stage_N_result.json`, update PROGRESS.md's
   sub-entry for that stage.

A stage too large for one dispatch to handle cleanly gets **split in `refactor_plan.json`** rather
than forced through a single oversized dispatch — that's a refactor-planner correction, not a
stage-executor workaround.

### Phase 6 — synthesizer
- **Input**: every `output/*.json` produced so far + `git log` on the refactor branch.
- **Tools**: Read, Bash (`git log` only), Write.
- **Output**: `output/synthesis_report.md` — a modernization **roadmap**, not a completion claim:
  what changed, what's proven equivalent via contract tests, and the remaining risk-ranked
  backlog. One run through a large codebase finishes a handful of stages, never the whole app —
  the report has to say so honestly.

## MCP extensions

Only the **SQLite MCP** is wired in today (`archaeologist`, `risk-assessor` — read-only against
`legacy-app/shared/data.db`, configured in `.mcp.json`). A longer menu of MCPs that would extend
specific nodes without changing this graph's shape is documented in `CLAUDE.md` — none of them are
live.
