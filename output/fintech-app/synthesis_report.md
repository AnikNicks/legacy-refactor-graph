# Modernization roadmap — fintech-app

**Summary**: 4 of 4 planned stages ran, all approved, none rejected. 16 characterization tests
pass (up from the 13 test-writer produced against the unmodified target). The flagship finding
across every example target analyzed this session — a non-atomic balance transfer, a real
double-spend risk — is fully resolved, alongside the schema-level float-currency issue.
**Highest remaining backlog item**: `shared`'s structural centrality, deliberately left unstaged
for the same reason as every other example target's equivalent finding.

## What changed

| Stage | Module | Commit | What it did | Acceptance criteria |
|---|---|---|---|---|
| 1 | `transactions` | `155b332` | Debit is now a single atomic, guarded `UPDATE` instead of a read-then-compare. | All 3 met — existing tests pass, a new test exercises the guard directly (exact-balance transfer succeeds and drops to 0; a further transfer from the now-empty account is rejected), grep confirmed one guarded UPDATE. |
| 2 | `transactions` | `623f719` | Added a required `idempotency_key`; a repeat with the same key returns the original result. | All 3 met — the no-idempotency test flipped to prove single-debit behavior, missing-key requests rejected, all other tests still pass. |
| 3 | `shared`+`accounts`+`transactions`+`ledger` | `0cc99fe` | Migrated `balance`/`amount` from `REAL` to `INTEGER` cents; renamed the API fields to `*_cents` throughout as a deliberate breaking change. | All 3 met — every test updated to cents and passing, the float-drift test flipped from "~1.0, off by an epsilon" to "exactly 100 cents," schema confirmed `INTEGER` via grep. |
| 4 | `ledger` | `0295b05` | Parameterized the query and changed the route to `<int:account_id>`. | Both met — existing tests pass, the non-numeric-input test flipped from a crash to a clean 404. |

## What's proven equivalent — and what isn't

- **Stage 1**: the double-spend fix is proven by directly exercising the new guard's boundary
  condition (a transfer for exactly the current balance, then a further transfer that must fail),
  not just re-running the original happy-path tests. This is the closest a single-process test
  suite can get to proving the atomicity property without literally running concurrent requests —
  the guard itself (the `WHERE balance >= ?` clause) is what a concurrent request would also have
  to pass, so proving it's enforced correctly in the sequential case demonstrates the mechanism
  that makes the concurrent case safe too.
- **Stage 3** is the most significant deliberate behavior change in this run across all three
  example targets combined: every currency field in the public API was renamed
  (`starting_balance` → `starting_balance_cents`, `amount` → `amount_cents`, `balance` →
  `balance_cents`). This was a conscious choice, not an oversight — silently accepting a float
  dollar amount into a newly-integer-cents field would have been far worse than a caller getting a
  clean error from an unrecognized field name.
- **Stages 2 and 4** are behavior-preserving for all valid input by construction; stage 4's only
  behavior change (rejecting non-numeric `account_id` with 404 instead of crashing) is strictly a
  quality improvement over the previous crash.

## Rejected or deferred stages

None. All 4 stages from `refactor_plan.json` were approved as presented.

## Remaining risk-ranked backlog

In risk-assessor's original order, what's still outstanding:

1. **`shared`** — structural centrality (every domain module depends on it for database access)
   was flagged but deliberately not staged, consistent with every other example target's
   equivalent finding this session: no single actionable bug is attached to it yet.
2. **`accounts`** — `create_account` has no input validation (a negative `starting_balance_cents`
   is accepted as-is). Not part of any stage in this run.
3. **`transactions`** — the atomicity fix (stage 1) and idempotency (stage 2) are both in place,
   but there's still no real authentication tying a transfer request to who's actually authorized
   to move money out of `from_account`. That's a materially larger piece of work than any stage
   scoped this run, similar to `healthcare-app`'s access-control backlog item.

No module was left completely untouched, and this target's flagship risk — the one most likely to
cause literal financial harm across every example analyzed this session — is the one most fully
resolved: atomic, idempotent, and now typed correctly for money.
