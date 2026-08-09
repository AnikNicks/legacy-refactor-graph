def _create_product(client, stock=20):
    return client.post(
        "/products", json={"name": "Widget", "price_cents": 500, "category": "misc", "initial_stock": stock}
    ).get_json()["id"]


def test_get_stock(client):
    product_id = _create_product(client, stock=20)
    resp = client.get(f"/inventory/{product_id}")
    assert resp.status_code == 200
    assert resp.get_json()["stock_qty"] == 20


def test_get_stock_unknown_product(client):
    resp = client.get("/inventory/999999")
    assert resp.status_code == 404


def test_adjust_stock_increases(client):
    product_id = _create_product(client, stock=20)
    resp = client.post(f"/inventory/{product_id}/adjust", json={"delta": 5})
    assert resp.status_code == 200
    assert resp.get_json()["stock_qty"] == 25


def test_adjust_stock_decreases(client):
    product_id = _create_product(client, stock=20)
    resp = client.post(f"/inventory/{product_id}/adjust", json={"delta": -8})
    assert resp.status_code == 200
    assert resp.get_json()["stock_qty"] == 12


def test_adjust_stock_unknown_product(client):
    resp = client.post("/inventory/999999/adjust", json={"delta": 1})
    assert resp.status_code == 404


def test_adjust_stock_rejects_delta_that_would_go_negative(client):
    # Stage 1 fixed this: adjust_stock now rejects a delta that would take
    # stock_qty below zero (400, unchanged) instead of applying it and
    # returning a negative quantity. The flip from "accepts and returns -5"
    # to "rejected, stock unchanged at 5" is the proof the atomic guarded
    # UPDATE is doing its job.
    product_id = _create_product(client, stock=5)
    resp = client.post(f"/inventory/{product_id}/adjust", json={"delta": -10})
    assert resp.status_code == 400

    stock = client.get(f"/inventory/{product_id}").get_json()["stock_qty"]
    assert stock == 5
