def _create_account(client, owner, balance_cents):
    return client.post(
        "/accounts", json={"owner": owner, "starting_balance_cents": balance_cents}
    ).get_json()["id"]


def test_transfer_moves_balance(client):
    alice = _create_account(client, "Alice", 10000)
    bob = _create_account(client, "Bob", 2000)

    resp = client.post(
        "/transactions/transfer",
        json={"from_account": alice, "to_account": bob, "amount_cents": 3000, "idempotency_key": "k1"},
    )
    assert resp.status_code == 201

    assert client.get(f"/accounts/{alice}").get_json()["balance_cents"] == 7000
    assert client.get(f"/accounts/{bob}").get_json()["balance_cents"] == 5000


def test_transfer_insufficient_funds_rejected(client):
    alice = _create_account(client, "Alice", 1000)
    bob = _create_account(client, "Bob", 0)

    resp = client.post(
        "/transactions/transfer",
        json={"from_account": alice, "to_account": bob, "amount_cents": 999900, "idempotency_key": "k1"},
    )
    assert resp.status_code == 400

    assert client.get(f"/accounts/{alice}").get_json()["balance_cents"] == 1000
    assert client.get(f"/accounts/{bob}").get_json()["balance_cents"] == 0


def test_transfer_unknown_from_account(client):
    bob = _create_account(client, "Bob", 0)
    resp = client.post(
        "/transactions/transfer",
        json={"from_account": 999999, "to_account": bob, "amount_cents": 500, "idempotency_key": "k1"},
    )
    assert resp.status_code == 400


def test_transfer_unknown_to_account(client):
    alice = _create_account(client, "Alice", 10000)
    resp = client.post(
        "/transactions/transfer",
        json={"from_account": alice, "to_account": 999999, "amount_cents": 500, "idempotency_key": "k1"},
    )
    assert resp.status_code == 400


def test_transfer_requires_idempotency_key(client):
    alice = _create_account(client, "Alice", 10000)
    bob = _create_account(client, "Bob", 0)
    resp = client.post(
        "/transactions/transfer", json={"from_account": alice, "to_account": bob, "amount_cents": 500}
    )
    assert resp.status_code == 400


def test_transfer_of_exact_balance_then_rejects_further_transfer(client):
    # Stage 1: exercises the atomic guarded UPDATE's WHERE clause directly
    # rather than the old separate read-then-compare. A transfer for
    # exactly the current balance succeeds and drops it to 0; anything
    # further from that now-empty account is rejected.
    alice = _create_account(client, "Alice", 5000)
    bob = _create_account(client, "Bob", 0)

    first = client.post(
        "/transactions/transfer",
        json={"from_account": alice, "to_account": bob, "amount_cents": 5000, "idempotency_key": "k1"},
    )
    assert first.status_code == 201
    assert client.get(f"/accounts/{alice}").get_json()["balance_cents"] == 0

    second = client.post(
        "/transactions/transfer",
        json={"from_account": alice, "to_account": bob, "amount_cents": 1, "idempotency_key": "k2"},
    )
    assert second.status_code == 400
    assert client.get(f"/accounts/{alice}").get_json()["balance_cents"] == 0


def test_transfer_is_idempotent_with_same_key(client):
    # Stage 2 fixed this: retrying the identical transfer request with the
    # same idempotency_key returns the original result instead of moving
    # the money a second time.
    alice = _create_account(client, "Alice", 10000)
    bob = _create_account(client, "Bob", 0)
    payload = {"from_account": alice, "to_account": bob, "amount_cents": 3000, "idempotency_key": "same-key"}

    client.post("/transactions/transfer", json=payload)
    client.post("/transactions/transfer", json=payload)

    assert client.get(f"/accounts/{alice}").get_json()["balance_cents"] == 7000  # debited once, not twice
    assert client.get(f"/accounts/{bob}").get_json()["balance_cents"] == 3000


def test_transfer_with_different_keys_moves_money_twice(client):
    alice = _create_account(client, "Alice", 10000)
    bob = _create_account(client, "Bob", 0)

    client.post(
        "/transactions/transfer",
        json={"from_account": alice, "to_account": bob, "amount_cents": 3000, "idempotency_key": "key-a"},
    )
    client.post(
        "/transactions/transfer",
        json={"from_account": alice, "to_account": bob, "amount_cents": 3000, "idempotency_key": "key-b"},
    )

    assert client.get(f"/accounts/{alice}").get_json()["balance_cents"] == 4000
    assert client.get(f"/accounts/{bob}").get_json()["balance_cents"] == 6000


def test_repeated_small_transfers_sum_exactly_in_cents(client):
    # Stage 3 fixed the float-drift finding: ten transfers of 10 cents now
    # sum to exactly 100 cents. The flip from "approximately 1.0, off by a
    # float epsilon" to "exactly 100" is the proof the drift is gone, not
    # just made smaller.
    alice = _create_account(client, "Alice", 1000)
    bob = _create_account(client, "Bob", 0)

    for i in range(10):
        client.post(
            "/transactions/transfer",
            json={"from_account": alice, "to_account": bob, "amount_cents": 10, "idempotency_key": f"k{i}"},
        )

    assert client.get(f"/accounts/{bob}").get_json()["balance_cents"] == 100
