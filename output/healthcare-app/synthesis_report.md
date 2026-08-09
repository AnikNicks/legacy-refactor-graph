# Modernization roadmap — healthcare-app

**Summary**: 5 of 5 planned stages ran, all approved, none rejected. 20 characterization tests
pass (up from the 13 test-writer produced against the unmodified target). The flagship finding —
SQL injection in a PHI-handling module with no audit trail — is fully resolved: `records`' queries
are parameterized and every access now logs an audit entry. **Highest remaining backlog item**:
real access control tied to requesting-provider identity. Stage 2 (audit trail) and stage 3
(hide PII by default) both make PHI exposure *observable* and *reduced by default*, but neither
adds actual authorization — there's no auth model in this target to hook into yet, and inventing
one wasn't in scope for a stage meant to fix one specific, already-scoped finding.

## What changed

| Stage | Module | Commit | What it did | Acceptance criteria |
|---|---|---|---|---|
| 1 | `records` | `2c1afe3` | Parameterized both `add_note`'s INSERT and `search_notes`' LIKE query. | All 3 met — existing tests pass, both apostrophe-crash tests flipped to succeed/find literally, grep confirmed no `%`-formatted SQL remains. |
| 2 | `records` | `dfc5e6c` | New `audit_log` table; every `add_note`/`search_notes` call writes a best-effort entry after its primary operation succeeds. | All 3 met — existing tests pass, new tests confirm audit rows are written correctly, and a failure-injection test proves a broken audit path can't turn a successful note-add into an error. |
| 3 | `patients` | `18a81e6` | `get_patient`/`list_patients` exclude SSN/DOB by default; `?include_sensitive=true` still returns them. | All 3 met — the old all-fields test split into a default-excludes test and an explicit-includes test; list count assertion untouched. |
| 4 | `patients` | `5ff420a` | Registration log no longer includes the request payload, only the resulting id. | All 3 met — grep confirms the only remaining `print()` logs an id, and a new test captures stdout to prove the SSN value never appears. |
| 5 | `appointments` | `8593136` | Unique index on `(provider, scheduled_at)` makes double-booking rejection atomic. | All 3 met — the double-booking test flipped to expect 409, and two new tests confirm a different provider or different time still succeeds. |

## What's proven equivalent — and what isn't

- **Stage 2**: the audit trail's non-blocking guarantee is proven by an actual failure-injection
  test (`test_audit_log_failure_does_not_break_add_note`), not just asserted — the audit function
  was monkeypatched to raise outright, and `add_note` still returned 201. This is a stronger check
  than "existing tests still pass."
- **Stage 3 (branch-by-abstraction)**: this is a deliberate, documented response-shape change, not
  pure equivalence — the default `GET /patients/<id>` response now has fewer fields than before.
  Any caller depending on the old always-present `ssn`/`dob` fields needs to add
  `?include_sensitive=true`. This was flagged explicitly at the human checkpoint and approved
  as-is; it is the correct fix for the over-exposure finding, not a regression, but it is a real
  breaking change to the API surface.
- **Stage 5**: uses a database-level unique index rather than an application-level
  check-then-insert, deliberately following the same atomicity lesson learned in `ecommerce-app`
  and `fintech-app` this session — a separate SELECT-then-INSERT would have reintroduced the exact
  race-condition class those other targets' stages were fixing.
- **Stages 1 and 4** are behavior-preserving for all valid input by construction.

## Rejected or deferred stages

None. All 5 stages from `refactor_plan.json` were approved as presented.

## Remaining risk-ranked backlog

In risk-assessor's original order, what's still outstanding:

1. **`records`** — no real access control exists tied to requesting-provider identity; anyone
   who can reach `search_notes` can search every patient's clinical notes. Stage 2's audit trail
   makes this *observable* after the fact; it does not prevent it. This needs an actual auth/session
   model as a prerequisite, which is a larger piece of work than any single stage in this run.
2. **`patients`** — `list_patients` still has no pagination and returns every patient to any
   caller (just without SSN/DOB by default now). Same underlying access-control gap as `records`.
3. **`shared`** — structural centrality (every domain module depends on it for database access)
   was flagged but deliberately not staged, for the same reason as the other example targets'
   equivalent finding: no single actionable bug is attached to it yet.

No module was left completely untouched, but real authorization — the thing that would actually
close the "any caller sees any patient's PHI" risk — is bigger than any one stage and belongs in
its own future run once there's an auth model to build on.
