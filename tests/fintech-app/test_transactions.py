def _create_account(client, owner, balance):
    return client.post("/accounts", json={"owner": owner, "starting_balance": balance}).get_json()["id"]


def test_transfer_moves_balance(client):
    alice = _create_account(client, "Alice", 100.0)
    bob = _create_account(client, "Bob", 20.0)

    resp = client.post("/transactions/transfer", json={"from_account": alice, "to_account": bob, "amount": 30.0})
    assert resp.status_code == 201

    assert client.get(f"/accounts/{alice}").get_json()["balance"] == 70.0
    assert client.get(f"/accounts/{bob}").get_json()["balance"] == 50.0


def test_transfer_insufficient_funds_rejected(client):
    alice = _create_account(client, "Alice", 10.0)
    bob = _create_account(client, "Bob", 0.0)

    resp = client.post("/transactions/transfer", json={"from_account": alice, "to_account": bob, "amount": 9999.0})
    assert resp.status_code == 400

    assert client.get(f"/accounts/{alice}").get_json()["balance"] == 10.0
    assert client.get(f"/accounts/{bob}").get_json()["balance"] == 0.0


def test_transfer_unknown_from_account(client):
    bob = _create_account(client, "Bob", 0.0)
    resp = client.post("/transactions/transfer", json={"from_account": 999999, "to_account": bob, "amount": 5.0})
    assert resp.status_code == 400


def test_transfer_unknown_to_account(client):
    alice = _create_account(client, "Alice", 100.0)
    resp = client.post("/transactions/transfer", json={"from_account": alice, "to_account": 999999, "amount": 5.0})
    assert resp.status_code == 400


def test_transfer_of_exact_balance_then_rejects_further_transfer(client):
    # Stage 1: exercises the atomic guarded UPDATE's WHERE clause directly
    # rather than the old separate read-then-compare. A transfer for
    # exactly the current balance succeeds and drops it to 0; anything
    # further from that now-empty account is rejected.
    alice = _create_account(client, "Alice", 50.0)
    bob = _create_account(client, "Bob", 0.0)

    first = client.post("/transactions/transfer", json={"from_account": alice, "to_account": bob, "amount": 50.0})
    assert first.status_code == 201
    assert client.get(f"/accounts/{alice}").get_json()["balance"] == 0.0

    second = client.post("/transactions/transfer", json={"from_account": alice, "to_account": bob, "amount": 0.01})
    assert second.status_code == 400
    assert client.get(f"/accounts/{alice}").get_json()["balance"] == 0.0


def test_transfer_has_no_idempotency_protection(client):
    # Characterizes the flagship finding: retrying the identical transfer
    # request (e.g. a client retry after a timed-out response that actually
    # succeeded) moves the money a second time instead of being recognized
    # as a duplicate of the first.
    alice = _create_account(client, "Alice", 100.0)
    bob = _create_account(client, "Bob", 0.0)
    payload = {"from_account": alice, "to_account": bob, "amount": 30.0}

    client.post("/transactions/transfer", json=payload)
    client.post("/transactions/transfer", json=payload)

    assert client.get(f"/accounts/{alice}").get_json()["balance"] == 40.0  # 100 - 30 - 30
    assert client.get(f"/accounts/{bob}").get_json()["balance"] == 60.0  # 0 + 30 + 30


def test_repeated_small_transfers_accumulate_float_drift(client):
    # Characterizes the schema-level float-currency finding: 0.1 has no
    # exact binary floating-point representation, so ten transfers of 0.1
    # do not sum to exactly 1.0 the way integer cents would.
    alice = _create_account(client, "Alice", 10.0)
    bob = _create_account(client, "Bob", 0.0)

    for _ in range(10):
        client.post("/transactions/transfer", json={"from_account": alice, "to_account": bob, "amount": 0.1})

    bob_balance = client.get(f"/accounts/{bob}").get_json()["balance"]
    assert bob_balance != 1.0
    assert abs(bob_balance - 1.0) < 1e-9  # the drift is real but tiny at this scale
