---
description: Run the legacy-refactor-agent pipeline against a target codebase
argument-hint: [target-path]
---

Run the full legacy-refactor-agent pipeline against target `$ARGUMENTS` (default `legacy-app` if
no argument is given). See `GRAPH.md` for the full architecture this command implements — this
file is the executable steps; `GRAPH.md` is the reference for *why* they're ordered this way.

**Always regenerate on an explicit re-run.** If you're asked to run this pipeline again for a
target that already has `output/$ARGUMENTS/*.json` from a previous run, that's a new run — dispatch every
phase fresh rather than treating existing output as already-done work, unless the user is
explicitly asking you to resume a specific stalled phase.

## Guardrails

Every guardrail below runs via `python scripts/validate_state.py` — real pydantic validation and
real git inspection, never an eyeballed substitute. On any `GUARDRAIL_FAIL`: stop, report exactly
what failed, and do not proceed to the next phase.

## Steps

### Phase 0 — preflight
Run `python scripts/validate_state.py preflight --target $ARGUMENTS`. If it prints
`GUARDRAIL_FAIL`, stop immediately and report the errors — do not create a branch or dispatch any
subagent on a bad target. If it passes: create (or switch to, if it already exists) branch
`refactor/<target-slug>` off `main` (slugify the target path — e.g. `legacy-app` →
`refactor/legacy-app`). All work from here on happens on that branch; `main` is never committed to
again this run. Create `output/$ARGUMENTS/` if it doesn't exist yet, and add an entry for this
target to `output/examples.json` if one isn't already there (slug, display name, category,
description, run depth) — that's what makes it show up in the viewer's dropdown. Update
`PROGRESS.md` and `output/$ARGUMENTS/progress_state.json` together.

### Phase 1 — archaeologist
Before dispatching, read the target yourself and post a prediction of what `archaeologist`'s
inventory should find (module boundaries, entry points, notable smells, cross-module coupling) —
this is for the user to compare against the real output, not a step to skip because you're
confident. Then dispatch the `archaeologist` subagent via the Task tool with the target path.
Once `output/$ARGUMENTS/archaeology.json` exists (confirm with Read, don't just trust the completion
notification), run
`python scripts/validate_state.py validate --schema ArchaeologyReport --file output/$ARGUMENTS/archaeology.json`.
On `GUARDRAIL_FAIL`: re-dispatch `archaeologist` once with the validation errors appended to its
prompt, then re-validate. Fails again → stop the whole run, report which field failed. Update
`PROGRESS.md`/`progress_state.json`.

### Phase 2 — risk-assessor
Same prediction-before-dispatch pattern: post what you expect `risk-assessor` to rank highest and
why, given what you already read in Phase 1, before dispatching. Dispatch `risk-assessor` with the
target path (it reads `output/$ARGUMENTS/archaeology.json` itself). Validate
`output/$ARGUMENTS/risk_assessment.json` against `RiskAssessment`, same retry-once-then-stop rule. Update
`PROGRESS.md`/`progress_state.json`.

### Phase 3 — fan-out: test-writer + refactor-planner
Dispatch both `test-writer` and `refactor-planner` via the Task tool **in one message, in
parallel** — they're both independent readers of `archaeology.json` + `risk_assessment.json`, not
of each other. **Wait for both completion notifications before doing anything else** — do not
validate one and move on while the other is still running, and do not guess at either's result.
Once both are done: run `pytest` (via Bash) against `test-writer`'s output to confirm the
characterization tests actually pass, and
`python scripts/validate_state.py validate --schema RefactorPlan --file output/$ARGUMENTS/refactor_plan.json`.
Either failing gets the same one-retry-then-stop treatment, applied to whichever subagent produced
the failing output — don't re-dispatch the one that already succeeded. Update
`PROGRESS.md`/`progress_state.json`.

### Phase 4 — human gate (hard stop)
Read `output/$ARGUMENTS/refactor_plan.json` and the test files under `tests/`. Present the **full** staged
plan to the user: every stage's module, description, pattern, risk level, target files, and
acceptance criteria. **Do not dispatch anything from Phase 5 in this same turn or without an
explicit approval message from the user.** Update `PROGRESS.md` to reflect "awaiting human
approval on the Phase 4 plan" and stop.

### Phase 5 — stage execution (only after Phase 4 approval)
For each stage in `refactor_plan.json`'s `stages`, **in order**:
1. Dispatch `stage-executor` via the Task tool with just that one stage's definition. It
   implements the change and runs tests; it does not commit.
2. Tests fail → re-dispatch `stage-executor` once with the failure details appended. Fails again
   → stop the entire run, report which stage/test failed, do not attempt the remaining stages.
3. Tests pass → **this is a human checkpoint, not an auto-commit.** Show the user: the diff
   (`git diff`, uncommitted), the test output, and this stage's `acceptance_criteria`. Wait for
   one of:
   - **Approve** → proceed to step 4 as-is.
   - **Request a change** → either make the edit directly or re-dispatch `stage-executor` with the
     feedback appended, re-run tests, and present again. Repeat until approved or rejected.
   - **Reject** → do not commit. Log the rejection and why in `PROGRESS.md`'s sub-entry for this
     stage, `git checkout` the stage's uncommitted changes to discard them, and move to the next
     stage — unless a later stage's `depends_on` includes this one, in which case stop and tell
     the user the plan needs re-sequencing.
4. On approval: commit on the refactor branch with a message describing the stage. Run
   `python scripts/validate_state.py stage-diff-check --stage <id> --target $ARGUMENTS`. On
   `GUARDRAIL_FAIL` here (the commit touched something outside the target/tests), do not proceed —
   this is a real containment breach, not a retry-once situation; stop and report it. On pass:
   write `output/$ARGUMENTS/stage_N_result.json` (matching `StageResult`), update `PROGRESS.md`'s sub-entry
   for this stage, move to the next stage.

If your turn would otherwise end while a stage is mid-checkpoint (tests passed, diff shown, no
user response yet), that's correct — stop and wait, don't guess at approval.

### Phase 6 — synthesis
Once every stage is resolved (approved+committed, rejected, or the run stopped on a failure):
dispatch `synthesizer` with the target path. Wait for its completion notification. Validate
`output/$ARGUMENTS/synthesis_report.md` exists and actually covers every stage (spot-check against
`refactor_plan.json`'s stage count — this file isn't pydantic-validated since it's markdown, so
this check is a manual read, not a `validate_state.py` call). Update `PROGRESS.md` to "complete"
and compact every phase's entry to one line each.

## Progress tracking

After **every** phase above: update `PROGRESS.md` (compact the phase just finished to one line,
clear and rewrite the "Active phase — details" section for whatever's next, update "Blockers" if
anything failed) and write the same state to `output/$ARGUMENTS/progress_state.json` in lockstep — the
`viewer/` app reads the JSON one and must never fall out of sync with the markdown one.
