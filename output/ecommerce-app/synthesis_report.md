# Modernization roadmap — ecommerce-app

**Summary**: 4 of 4 planned stages ran, all approved, none rejected. 20 characterization tests
pass (up from the 16 test-writer produced against the unmodified target). The flagship risk —
inventory decrement duplicated non-atomically in two places — is fully resolved: both `inventory`
and `cart` now share one atomic, guarded implementation. **Highest remaining backlog item**:
`shared`'s structural centrality (all three domain modules depend on it for database access) was
flagged by risk-assessor but deliberately left unstaged — no single actionable bug was attached to
it, same reasoning as `legacy-app`'s equivalent finding.

## What changed

| Stage | Module | Commit | What it did | Acceptance criteria |
|---|---|---|---|---|
| 1 | `inventory` | `fb6e26d` | Replaced the read-then-write stock decrement with a single atomic, guarded `UPDATE`. | All 3 met — existing tests pass, the negative-result test flipped from "accepts, returns -5" to "rejected, unchanged," grep confirmed one write statement. |
| 2 | `cart` | `26085d8` | `checkout` now calls `inventory.service.decrement_stock` instead of reimplementing it. | All 3 met — existing tests pass, a new test proves insufficient stock is now rejected, `cart/routes.py` no longer queries the inventory table directly. |
| 3 | `cart` | `df1b697` | Added a required `idempotency_key` to `checkout`; a repeat with the same key returns the original order. | All 3 met — the no-idempotency test flipped to prove single-decrement behavior, missing-key requests are rejected, all other cart tests still pass. |
| 4 | `catalog` | `e2a7b52` | Replaced `list_products`' N+1 query with a single `LEFT JOIN`. | Both met — existing tests pass unchanged, grep confirmed exactly one query. |

## What's proven equivalent — and what isn't

- **Stage 2 (branch-by-abstraction)**: a real transactional-safety bug was found and fixed
  *during* implementation, not just planned around — `decrement_stock` originally opened its own
  DB connection and committed independently, which would have broken checkout's all-or-nothing
  transaction (an earlier item's decrement would survive even if a later item failed). The fix
  (an optional `conn` parameter, letting `decrement_stock` participate in the caller's own
  transaction) is proven by a dedicated test
  (`test_checkout_rolls_back_earlier_items_when_a_later_item_fails`), not just asserted.
- **Stage 2** also has a deliberate, documented behavior change: checkout now rejects orders that
  exceed available stock, where before it silently drove `stock_qty` negative. This is the
  correct fix for the flagged finding, not a regression, but it is real behavior change and was
  called out explicitly rather than folded silently into "internal refactor, no behavior change."
- **Stages 1, 3, 4** are behavior-preserving for all valid input by construction; stage 1's only
  behavior change (rejecting an over-large single-item decrement) was itself the fix being tested,
  proven by the flipped test.

## Rejected or deferred stages

None. All 4 stages from `refactor_plan.json` were approved as presented.

## Remaining risk-ranked backlog

In risk-assessor's original order, what's still outstanding:

1. **`shared`** — structural centrality (every domain module depends on it for database access)
   was flagged but deliberately not staged this run, for the same reason as `legacy-app`'s
   equivalent finding: no single actionable bug is attached to it yet.
2. **`catalog`** — `create_product` has no input validation (a missing `price_cents` or negative
   value is accepted as-is). Not part of any stage in this run.
3. **`cart`** — the 8% tax rate is still a hardcoded constant local to this module; a real rate
   change would still require someone to know to look here specifically.

No module was left completely untouched — every stage addressed a specific finding from Phase 1/2
— but "touched" means "the flagged finding was fixed," not "hardened end-to-end."
