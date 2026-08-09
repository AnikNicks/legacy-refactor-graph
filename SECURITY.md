# Security guardrails

Stated honestly: what's actually enforced by code, versus what's a convention stated in an agent's
prompt that relies on the agent following it. Don't treat the second category as a real boundary.

## Enforced (via `scripts/validate_state.py`)

- **Schema validation between every phase.** Each `output/*.json` a phase writes is
  pydantic-validated against `scripts/schemas.py` before the next phase is allowed to start
  (`validate --schema <Name> --file <path>`). On failure the run gets exactly one retry with the
  validation error appended to the agent's prompt; a second failure stops the run entirely.
- **Path-scoped diffs in Phase 5.** `stage-diff-check --stage <n> --target <path>` inspects the
  git diff for that stage's commit and fails the check if it touches anything outside
  `<target>/` and `tests/` — regardless of what the target is. This matters more once the target
  is a real, arbitrary codebase rather than the `legacy-app/` fixture.
- **Preflight branch check.** `preflight --target <path>` refuses to proceed if the current branch
  is `main` — a run can't accidentally start doing phase work there.
- **Human approval gate on every Phase-5 commit.** The orchestrator does not run a commit command
  until an explicit approval has been given for that stage. Passing tests is necessary but never
  sufficient on its own.

## Convention-level (stated in agent prompts, not sandboxed)

- **Least-privilege tool grants.** `archaeologist` and `risk-assessor` have no `Edit` and no
  write-capable `Bash` — they can only read and produce their one JSON output. This is enforced by
  what tools their `.claude/agents/*.md` frontmatter grants, which Claude Code does honor, but
  nothing stops a future edit to that frontmatter from loosening it — there's no separate runtime
  sandbox re-checking it.
- **Context/output discipline.** `archaeologist`'s tier-1 inventory pass is instructed to
  summarize rather than dump full file contents into its own context or `output/archaeology.json`
  — this keeps a large target from blowing the context budget and keeps `output/*.json` from
  leaking more of the codebase than a downstream phase needs. This is a prompt instruction, not a
  hard limit.
- **SQLite MCP is read-only by convention, not by server configuration.** `.mcp.json` registers
  `mcp-server-sqlite` against `legacy-app/shared/data.db`; the server itself supports write
  queries. `archaeologist` and `risk-assessor` are instructed to only use its read tools
  (`list_tables`, `describe_table`, `read_query`) and never `write_query`. Nothing at the MCP
  config level currently prevents a write call if an agent were instructed otherwise.
- **Secret handling.** Any secret-like string the pipeline encounters in the target (e.g. the
  fixture's hardcoded `SECRET_KEY`, or plaintext-stored passwords) is flagged as a finding in the
  relevant `output/*.json`, never echoed verbatim into a commit message, a log line intended for
  external systems, or (once any of the not-wired-in MCPs in `CLAUDE.md` are added) an external
  call.

## Branch discipline

All pipeline work happens on a dedicated branch created in Phase 0 (`refactor/<target-slug>`).
`main` is only ever touched by the one-time bootstrap commit that creates this scaffold — no
pipeline phase commits there, ever.

## What this does not cover

There is no sandboxing of `stage-executor`'s `Bash` access beyond the path-scoped diff check that
runs *after* it finishes — it can run arbitrary commands during a stage, and the diff check only
catches unwanted *file changes*, not other side effects (network calls, package installs, etc.).
If a target ever warrants stronger isolation than that, run the pipeline inside a disposable
container or VM rather than assuming this repo's own guardrails are sufficient on their own.
