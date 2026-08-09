def _create_product(client, price_cents=1999, stock=50):
    return client.post(
        "/products", json={"name": "Widget", "price_cents": price_cents, "category": "gadgets", "initial_stock": stock}
    ).get_json()["id"]


def test_checkout_creates_order_with_tax_applied(client):
    product_id = _create_product(client, price_cents=1999, stock=50)

    resp = client.post("/cart/checkout", json={"items": [{"product_id": product_id, "qty": 2}]})
    assert resp.status_code == 201
    # subtotal 3998 * 1.08 tax = 4317.84, rounded to 4318 - pins down the
    # exact hardcoded 8% rate and Python's round() behavior together.
    assert resp.get_json()["total_cents"] == 4318


def test_checkout_decrements_stock(client):
    product_id = _create_product(client, stock=50)
    client.post("/cart/checkout", json={"items": [{"product_id": product_id, "qty": 3}]})

    resp = client.get(f"/inventory/{product_id}")
    assert resp.get_json()["stock_qty"] == 47


def test_checkout_unknown_product(client):
    resp = client.post("/cart/checkout", json={"items": [{"product_id": 999999, "qty": 1}]})
    assert resp.status_code == 400


def test_get_order_returns_line_items(client):
    product_id = _create_product(client, price_cents=500, stock=10)
    order_id = client.post(
        "/cart/checkout", json={"items": [{"product_id": product_id, "qty": 2}]}
    ).get_json()["order_id"]

    resp = client.get(f"/cart/orders/{order_id}")
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["status"] == "placed"
    assert len(body["items"]) == 1
    assert body["items"][0]["qty"] == 2


def test_get_order_unknown(client):
    resp = client.get("/cart/orders/999999")
    assert resp.status_code == 404


def test_checkout_has_no_idempotency_protection(client):
    # Characterizes the current (buggy) behavior explicitly named in
    # archaeology/risk-assessor: retrying the identical checkout request
    # creates a second order and decrements stock a second time, rather than
    # being recognized as a duplicate of the first.
    product_id = _create_product(client, stock=50)
    payload = {"items": [{"product_id": product_id, "qty": 5}]}

    first = client.post("/cart/checkout", json=payload)
    second = client.post("/cart/checkout", json=payload)

    assert first.get_json()["order_id"] != second.get_json()["order_id"]
    stock = client.get(f"/inventory/{product_id}").get_json()["stock_qty"]
    assert stock == 40  # 50 - 5 - 5, decremented twice for one logical purchase
