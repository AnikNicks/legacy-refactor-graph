# Pipeline progress

**Pipeline**: legacy-refactor-agent
**Targets**: `legacy-app/`, `ecommerce-app/`, `healthcare-app/`, `fintech-app/` — all four complete, all 6 phases
**Branch**: `refactor/legacy-app` (all four targets' work merged here — see note below)
**Status**: complete. 86/86 tests passing across all four targets (30 + 20 + 20 + 16).

This file is the human-readable run state. Each target's `output/<slug>/progress_state.json`
mirrors its own state exactly, kept in sync after every update, for `viewer/` to read. See
`GRAPH.md` for what each phase does and `.claude/commands/refactor-legacy-app.md` for how it's
executed.

## legacy-app — 5 stages, `refactor/legacy-app`

Ranked `notes` > `auth` > `shared` > `billing`. Flagship: `notes` reaching directly into `auth`'s
internals plus injection-prone SQL. Stage 1 `8620dc6` (notes SQL parameterization), stage 2
`692e074` (auth.directory interface), stage 3 `efbd1db` (notes migrated onto auth.directory — the
one deliberate behavior change: registered-but-never-logged-in users can now create notes), stage
4 `34af72e` (billing cache/DB drift fixed), stage 5 `1b5f347` (SECRET_KEY to env var). All 5
approved, none rejected. `output/legacy-app/synthesis_report.md`.

## ecommerce-app — 4 stages, originally on `refactor/ecommerce-app`

Ranked `cart` > `shared` > `catalog` > `inventory`. Flagship: inventory decrement duplicated
non-atomically in two places. Stage 1 `fb6e26d` (atomic guarded decrement — caught the negative-
result bug), stage 2 `26085d8` (cart routed through inventory.service — a real transactional-safety
bug was found and fixed *during* implementation, not just planned around: the interface needed an
optional shared connection so a checkout's decrement rolls back correctly on a later item's
failure), stage 3 `df1b697` (checkout idempotency key), stage 4 `e2a7b52` (N+1 fix). All 4
approved, none rejected. `output/ecommerce-app/synthesis_report.md`.

## healthcare-app — 5 stages, originally on `refactor/healthcare-app`

Ranked `records` > `patients` > `shared` > `appointments`. Flagship: SQL injection in a
PHI-handling module with no audit trail. Stage 1 `2c1afe3` (records SQL parameterized), stage 2
`dfc5e6c` (audit trail, failure-injection tested so a broken audit path can't break the primary
write), stage 3 `18a81e6` (SSN/DOB hidden by default — breaking response-shape change, flagged),
stage 4 `5ff420a` (PII removed from logs), stage 5 `8593136` (double-booking rejected via a unique
index). All 5 approved, none rejected. `output/healthcare-app/synthesis_report.md`. Top backlog
item: real access control tied to provider identity — bigger than any single stage.

## fintech-app — 4 stages, originally on `refactor/fintech-app`

Ranked `transactions` > `ledger` > `accounts` > `shared`. Flagship — the single most severe finding
across all four targets: a non-atomic balance transfer (real double-spend). Stage 1 `155b332`
(atomic guarded debit), stage 2 `623f719` (transfer idempotency key), stage 3 `0cc99fe` (currency
migrated float → integer cents, a deliberate breaking API rename to `*_cents` throughout), stage 4
`0295b05` (ledger query parameterized + `<int:account_id>` guard). All 4 approved, none rejected.
`output/fintech-app/synthesis_report.md`.

## Note on branch discipline for this multi-target session

`GRAPH.md`/`SECURITY.md` specify one dedicated branch per target. Each of the three newer targets
did get its own branch (`refactor/ecommerce-app`, `refactor/healthcare-app`, `refactor/fintech-app`,
each correctly forked from `refactor/legacy-app` — not `main`, after an earlier mistake this
session where branching off `main` reverted the whole working tree, caught immediately with no work
lost) for their Phase 5/6 work. Once all three were individually complete, all three branches were
merged back into `refactor/legacy-app` — conflict-free, since no two targets ever touch the same
file — specifically so the viewer (which reads live from whichever branch is checked out) can show
all four targets' complete final state in one working tree, rather than requiring a branch switch
per target to see its data. Each target's individual commit history remains intact and inspectable
on its own original branch if needed; the merge only changes what `refactor/legacy-app`'s working
tree contains.

## Note on subagent dispatch

The `Agent` tool in this session can't discover this project's `.claude/agents/*.md` subagents
(cwd-discovery issue tied to the session's original working directory, not this repo). Per the
user's direction, this entire run was done directly rather than via subagent dispatch, but still
strictly following each phase's own `.claude/agents/*.md` instructions and producing the same
validated output contracts. `/refactor-legacy-app` itself is unaffected — this only matters for
how *this run* was carried out inside this session.

## Blockers

None.
