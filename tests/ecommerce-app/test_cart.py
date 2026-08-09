def _create_product(client, price_cents=1999, stock=50):
    return client.post(
        "/products", json={"name": "Widget", "price_cents": price_cents, "category": "gadgets", "initial_stock": stock}
    ).get_json()["id"]


def test_checkout_creates_order_with_tax_applied(client):
    product_id = _create_product(client, price_cents=1999, stock=50)

    resp = client.post(
        "/cart/checkout", json={"items": [{"product_id": product_id, "qty": 2}], "idempotency_key": "k1"}
    )
    assert resp.status_code == 201
    # subtotal 3998 * 1.08 tax = 4317.84, rounded to 4318 - pins down the
    # exact hardcoded 8% rate and Python's round() behavior together.
    assert resp.get_json()["total_cents"] == 4318


def test_checkout_decrements_stock(client):
    product_id = _create_product(client, stock=50)
    client.post("/cart/checkout", json={"items": [{"product_id": product_id, "qty": 3}], "idempotency_key": "k1"})

    resp = client.get(f"/inventory/{product_id}")
    assert resp.get_json()["stock_qty"] == 47


def test_checkout_unknown_product(client):
    resp = client.post(
        "/cart/checkout", json={"items": [{"product_id": 999999, "qty": 1}], "idempotency_key": "k1"}
    )
    assert resp.status_code == 400


def test_checkout_requires_idempotency_key(client):
    product_id = _create_product(client, stock=10)
    resp = client.post("/cart/checkout", json={"items": [{"product_id": product_id, "qty": 1}]})
    assert resp.status_code == 400


def test_get_order_returns_line_items(client):
    product_id = _create_product(client, price_cents=500, stock=10)
    order_id = client.post(
        "/cart/checkout", json={"items": [{"product_id": product_id, "qty": 2}], "idempotency_key": "k1"}
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


def test_checkout_rejects_insufficient_stock(client):
    # Stage 2: checkout now goes through inventory's guarded decrement
    # instead of blindly applying it, so an over-large order is rejected
    # rather than driving stock negative.
    product_id = _create_product(client, stock=5)

    resp = client.post(
        "/cart/checkout", json={"items": [{"product_id": product_id, "qty": 10}], "idempotency_key": "k1"}
    )
    assert resp.status_code == 400

    stock = client.get(f"/inventory/{product_id}").get_json()["stock_qty"]
    assert stock == 5


def test_checkout_rolls_back_earlier_items_when_a_later_item_fails(client):
    # Proves stage 2's decrement_stock(conn=db) actually participates in
    # checkout's own transaction: the first item's decrement must not stick
    # around uncommitted-but-applied when a later item in the same request
    # fails and the whole checkout is abandoned.
    product_a = _create_product(client, stock=10)

    resp = client.post(
        "/cart/checkout",
        json={
            "items": [{"product_id": product_a, "qty": 3}, {"product_id": 999999, "qty": 1}],
            "idempotency_key": "k1",
        },
    )
    assert resp.status_code == 400

    stock = client.get(f"/inventory/{product_a}").get_json()["stock_qty"]
    assert stock == 10  # product_a's decrement must have rolled back, not stuck at 7


def test_checkout_is_idempotent_with_same_key(client):
    # Stage 3 fixed this: retrying the identical checkout request with the
    # same idempotency_key returns the original order instead of creating a
    # second one and decrementing stock a second time.
    product_id = _create_product(client, stock=50)
    payload = {"items": [{"product_id": product_id, "qty": 5}], "idempotency_key": "same-key"}

    first = client.post("/cart/checkout", json=payload)
    second = client.post("/cart/checkout", json=payload)

    assert first.get_json()["order_id"] == second.get_json()["order_id"]
    stock = client.get(f"/inventory/{product_id}").get_json()["stock_qty"]
    assert stock == 45  # decremented once, not twice, for one logical purchase


def test_checkout_with_different_keys_creates_separate_orders(client):
    product_id = _create_product(client, stock=50)

    first = client.post(
        "/cart/checkout", json={"items": [{"product_id": product_id, "qty": 5}], "idempotency_key": "key-a"}
    )
    second = client.post(
        "/cart/checkout", json={"items": [{"product_id": product_id, "qty": 5}], "idempotency_key": "key-b"}
    )

    assert first.get_json()["order_id"] != second.get_json()["order_id"]
    stock = client.get(f"/inventory/{product_id}").get_json()["stock_qty"]
    assert stock == 40
