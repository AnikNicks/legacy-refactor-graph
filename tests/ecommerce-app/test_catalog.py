def test_create_product_seeds_inventory(client):
    resp = client.post(
        "/products", json={"name": "Widget", "price_cents": 1999, "category": "gadgets", "initial_stock": 50}
    )
    assert resp.status_code == 201
    product_id = resp.get_json()["id"]

    resp = client.get(f"/inventory/{product_id}")
    assert resp.get_json()["stock_qty"] == 50


def test_list_products_includes_stock(client):
    client.post("/products", json={"name": "Widget", "price_cents": 1999, "category": "gadgets", "initial_stock": 10})

    resp = client.get("/products")
    assert resp.status_code == 200
    products = resp.get_json()
    assert len(products) == 1
    assert products[0]["name"] == "Widget"
    assert products[0]["stock_qty"] == 10


def test_get_product(client):
    product_id = client.post(
        "/products", json={"name": "Widget", "price_cents": 1999, "category": "gadgets", "initial_stock": 5}
    ).get_json()["id"]

    resp = client.get(f"/products/{product_id}")
    assert resp.status_code == 200
    assert resp.get_json()["stock_qty"] == 5


def test_get_product_unknown(client):
    resp = client.get("/products/999999")
    assert resp.status_code == 404
