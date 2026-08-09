def _create_account(client, owner, balance_cents):
    return client.post(
        "/accounts", json={"owner": owner, "starting_balance_cents": balance_cents}
    ).get_json()["id"]


def test_ledger_lists_transfers_in_and_out(client):
    alice = _create_account(client, "Alice", 10000)
    bob = _create_account(client, "Bob", 0)
    carol = _create_account(client, "Carol", 5000)

    client.post(
        "/transactions/transfer",
        json={"from_account": alice, "to_account": bob, "amount_cents": 1000, "idempotency_key": "k1"},
    )
    client.post(
        "/transactions/transfer",
        json={"from_account": carol, "to_account": alice, "amount_cents": 500, "idempotency_key": "k2"},
    )

    resp = client.get(f"/ledger/{alice}")
    assert resp.status_code == 200
    rows = resp.get_json()
    assert len(rows) == 2
    assert "amount_cents" in rows[0]


def test_ledger_empty_for_account_with_no_transfers(client):
    alice = _create_account(client, "Alice", 10000)
    resp = client.get(f"/ledger/{alice}")
    assert resp.get_json() == []


def test_ledger_with_non_numeric_account_id_returns_clean_404(client):
    # Stage 4 fixed this: Flask's <int:account_id> converter now rejects a
    # non-numeric path segment before the route body (and its query) ever
    # runs, instead of the old string-formatted WHERE clause producing
    # invalid SQL. The flip from "raises sqlite3.OperationalError" to "404"
    # is the proof.
    resp = client.get("/ledger/not-a-number")
    assert resp.status_code == 404
