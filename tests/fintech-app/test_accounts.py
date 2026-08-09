def test_create_account(client):
    resp = client.post("/accounts", json={"owner": "Alice", "starting_balance": 100.0})
    assert resp.status_code == 201
    assert resp.get_json()["balance"] == 100.0


def test_get_account(client):
    account_id = client.post("/accounts", json={"owner": "Alice", "starting_balance": 50.0}).get_json()["id"]

    resp = client.get(f"/accounts/{account_id}")
    assert resp.status_code == 200
    assert resp.get_json()["owner"] == "Alice"
    assert resp.get_json()["balance"] == 50.0


def test_get_account_unknown(client):
    resp = client.get("/accounts/999999")
    assert resp.status_code == 404


def test_create_account_defaults_to_zero_balance(client):
    resp = client.post("/accounts", json={"owner": "Bob"})
    assert resp.status_code == 201
    assert resp.get_json()["balance"] == 0
