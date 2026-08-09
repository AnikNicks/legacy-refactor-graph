# Modernization roadmap — legacy-app

**Summary**: 5 of 5 planned stages ran, all approved, none rejected or needing a modification
round. 30 characterization tests pass (up from the 21 test-writer produced against the unmodified
target). Every module in the target (`auth`, `notes`, `billing`, `shared`) was touched by at least
one stage, but that does not mean the target is "done" — see the backlog below. **Highest-priority
remaining item**: `shared`'s structural centrality (all three domain modules depend on it for
database access and app wiring) was flagged by risk-assessor as an architectural risk but was
deliberately left out of this plan because it had no single actionable bug attached to it — it's
the natural next thing to scope once there's a concrete reason to touch `shared` again.

## What changed

| Stage | Module | Commit | What it did | Acceptance criteria |
|---|---|---|---|---|
| 1 | `notes` | `8620dc6` | Parameterized the 3 string-formatted SQL queries (create/list/update); `delete_note` was already safe. | All 3 met — existing tests pass, the apostrophe-crash test flipped from raising to succeeding, `grep` confirmed no `%`-formatted SQL remains. |
| 2 | `auth` | `692e074` | Introduced `auth/directory.py` (`is_known_user`/`verify`/`remember`); `auth/routes.py`'s register/login/profile migrated onto it, with `_user_cache` kept alive in parallel. | All 3 met — `test_auth.py` unchanged and passing, 5 new contract tests prove the two caches agree, `notes` had exactly one thing to import once stage 3 ran. |
| 3 | `notes` | `efbd1db` | `notes/routes.py` now imports only `auth.directory`, nothing from `auth.routes`. | All 3 met — existing tests pass including the 403-for-unknown-user case, no `auth.routes` import remains, new test covers the cache-cold acceptance path. |
| 4 | `billing` | `34af72e` | `pay_invoice`'s bare `except` narrowed to `sqlite3.DatabaseError`; cache only updates to `paid` after a confirmed-successful write. `create_invoice`'s except narrowed to `(KeyError, ValueError, TypeError)`. | All 3 met — existing tests pass, new test forces a DB failure and confirms the cache stays `pending`, no bare `except:` remains in the file. |
| 5 | `shared` | `1b5f347` | `SECRET_KEY` now read from the `SECRET_KEY` environment variable, falling back to an obviously-fake dev value when unset. | All 3 met — existing tests pass unmodified via the fallback, old hardcoded value confirmed absent via `grep`, new test proves the env var takes effect. |

## What's proven equivalent — and what isn't

- **Stage 2 (branch-by-abstraction)**: the contract tests in
  `tests/test_auth_directory_contract.py` prove `auth.directory`'s cache and the legacy
  `_user_cache` dict agree across register, login-cache-hit, login-cache-cold, profile-lookup, and
  unknown-user scenarios. This is equivalence **for those five scenarios**, not a formal proof —
  it doesn't cover concurrent access to either cache (neither the old nor the new code is
  thread-safe, and this run didn't change that).
- **Stage 3 (branch-by-abstraction, depends on stage 2)**: this stage has one deliberate,
  documented behavior change, not pure equivalence — a user who registers but never logs in can
  now create notes, where before they were incorrectly rejected. This was called out explicitly at
  the human checkpoint and approved as-is; it is not a regression, it's the fix for the coupling
  bug archaeology/risk-assessor both flagged, but it is real, user-visible behavior change and
  should be read as such, not filed under "internal refactor, no behavior change."
- **Stages 1, 4, 5** are behavior-preserving for all valid input by construction (stage 1's only
  behavior change — the apostrophe case — was a bug being fixed, characterized by a test that
  flipped from "raises" to "succeeds" as the explicit proof).

## Rejected or deferred stages

None. All 5 stages from `refactor_plan.json` were approved as presented or with the one flagged
judgment call in stage 2 (accepted as-is). No stage blocked a later one.

## Remaining risk-ranked backlog

Modules were all *touched*, but none were fully hardened. In risk-assessor's original order, what's
still outstanding:

1. **`notes`** (was highest risk) — SQL is now safe and the coupling is fixed, but there's still
   no authorization check on `update_note`/`delete_note`: any caller who knows a `note_id` can
   modify or delete it regardless of who owns it. Not part of any stage in this run.
2. **`auth`** — the underlying problem (two caches that could in principle drift) is now covered
   by contract tests, but the dual-cache design itself (`_user_cache` in `routes.py` plus
   `directory._directory_cache`) is still there; a future stage could collapse them into one now
   that `notes` no longer depends on `_user_cache` directly. `logout` is still a no-op with no
   real session model behind it.
3. **`shared`** — the structural-centrality risk risk-assessor flagged (every domain module
   depends on it) was explicitly not staged in this run because it had no single actionable bug
   attached — see the summary above. Worth a dedicated future run once there's a concrete reason
   (e.g. adding a second datastore, or splitting `get_db` per module).
4. **`billing`** — the specific cache/DB drift bug is fixed, but `INVOICE_CACHE` itself is still
   unbounded and never expires; under long-running production use it would grow without limit.
   Not part of any stage in this run.

No module was left completely untouched, but "touched" here means "the specific finding from
Phase 1/2 was addressed," not "hardened end-to-end." A second pipeline run against this same
target, informed by this backlog, would be the natural next step.
