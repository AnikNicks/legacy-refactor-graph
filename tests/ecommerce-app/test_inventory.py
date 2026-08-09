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


def test_adjust_stock_allows_negative_result(client):
    # Characterizes current (arguably buggy) behavior: adjust_stock has no
    # floor check, so a delta larger than the current stock produces a
    # negative stock_qty instead of being rejected or clamped at zero.
    product_id = _create_product(client, stock=5)
    resp = client.post(f"/inventory/{product_id}/adjust", json={"delta": -10})
    assert resp.status_code == 200
    assert resp.get_json()["stock_qty"] == -5
