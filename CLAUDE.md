# legacy-refactor-graph

A general-purpose pipeline for modernizing legacy codebases and large SaaS applications: survey a
codebase, rank what's actually risky, write characterization tests that pin down current behavior,
propose an incremental (strangler-fig / branch-by-abstraction) refactor plan, and execute it stage
by stage with a human approving every single commit. It is not specific to any one target — see
`output/examples.json` for the current set of example targets, none of which is "the" point of
the tool; each is a small fixture standing in for a real codebase.

## Where things live

| Path | What it is |
|---|---|
| `GRAPH.md` | The pipeline's architecture — the phase DAG, each node's input/output contract, the scale strategy. Read this to understand *how* the pipeline works. |
| `PROGRESS.md` | The current run's state, human-readable, compacted to one line per completed phase (for the target most recently worked on). Read this to understand *where a run currently stands*. |
| `output/<target>/progress_state.json` | The same state as `PROGRESS.md`, structured, per target, for `viewer/` to read without parsing markdown. |
| `output/examples.json` | The manifest of every example target the viewer's dropdown lists — slug, display name, category, description, run depth. Add an entry here when a new example target is added. |
| `SECURITY.md` | What's actually enforced (by `scripts/validate_state.py`) vs. what's convention-level (stated in agent prompts, not sandboxed). |
| `.claude/commands/refactor-legacy-app.md` | The orchestrator. Invoke with `/refactor-legacy-app [path]` — `path` defaults to `legacy-app/`. |
| `.claude/agents/` | The six subagents: `archaeologist`, `risk-assessor`, `test-writer`, `refactor-planner`, `stage-executor`, `synthesizer`. |
| `scripts/schemas.py`, `scripts/validate_state.py` | The pydantic contracts every phase's output must satisfy, and the CLI (`preflight` / `validate` / `stage-diff-check`) that enforces them between phases. |
| `output/<target>/*.json` | The audit trail per target — every phase's validated output. Tracked in git, not gitignored. |
| `legacy-app/`, `ecommerce-app/`, `healthcare-app/`, `fintech-app/` | The example targets — see `output/examples.json` for what each one is and how far its pipeline run went. `legacy-app/` has the only full 0–6 run; the other three have Phases 0–2 (archaeologist + risk-assessor) only. |
| `viewer/` | A read-only TypeScript/React/Vite dashboard over `output/<target>/*.json`, with a dropdown to switch targets and a source-viewer panel to browse each target's actual code. Optional — nothing about the pipeline depends on it running. |

## Conventions

- Every phase reads only the upstream `output/*.json` its `GRAPH.md` contract names — never the
  full history of earlier phases "just in case."
- Every write is validated by `scripts/validate_state.py` before the next phase may start. A
  validation failure stops the run and is logged in `PROGRESS.md`'s Blockers section — it is never
  silently retried more than once.
- All pipeline work happens on a dedicated branch (`refactor/<target-slug>`); `main` is only ever
  touched by the initial scaffold commit.
- Every Phase-5 stage commit requires explicit human approval — passing tests is necessary, never
  sufficient.

## MCP extension list (documented, not wired in)

Only the SQLite MCP is live today (`archaeologist` + `risk-assessor`, read-only, see `.mcp.json`
and `SECURITY.md`). These are named as the natural next additions, per agent, whenever a real
target makes them worth the setup — none of them are configured:

| MCP | Agent | What it would add |
|---|---|---|
| Git MCP | `archaeologist` | Structured churn/blame queries instead of parsing `git log --stat` text |
| Code-intelligence / tree-sitter MCP | `archaeologist` | Real import/call graphs for coupling analysis, instead of grep heuristics |
| GitHub MCP | `risk-assessor` | Bug-report/incident density per module as a risk signal |
| GitHub MCP | `stage-executor` | Land each stage as its own PR instead of a direct commit |
| Sentry/Datadog-style MCP | `risk-assessor` | Production error rates per module — a real runtime risk signal |
| Dependency/CVE-scanning MCP (e.g. Semgrep) | `risk-assessor` | Real security-surface findings instead of pattern-matching on source |
| OpenAPI/schema MCP | `test-writer` | Ground black-box tests in an actual published contract, when one exists |
| Network/HTTP capture MCP | `test-writer` | Golden-master tests from a running instance's real traffic |
| Jira/Linear MCP | `refactor-planner` | Cross-check planned stages against existing backlog |
| CI MCP | `stage-executor` | Gate a stage on a real CI run, not just local `pytest` |
| Notion/Confluence/Slack MCP | `synthesizer` | Publish the roadmap somewhere durable — a visible/shared-state action, would need explicit confirmation every time, never automatic |
