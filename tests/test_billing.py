def test_create_invoice(client):
    resp = client.post("/billing/invoices", json={"username": "alice", "amount_cents": 500})
    assert resp.status_code == 201
    assert "invoice_id" in resp.get_json()


def test_create_invoice_bad_payload(client):
    resp = client.post("/billing/invoices", json={"username": "alice"})
    assert resp.status_code == 400
    assert resp.get_json() == {"error": "bad payload"}


def test_get_invoice_from_cache(client):
    invoice_id = client.post(
        "/billing/invoices", json={"username": "alice", "amount_cents": 500}
    ).get_json()["invoice_id"]

    resp = client.get(f"/billing/invoices/{invoice_id}")
    assert resp.status_code == 200
    assert resp.get_json()["amount_cents"] == 500


def test_get_invoice_unknown(client):
    resp = client.get("/billing/invoices/999999")
    assert resp.status_code == 404


def test_list_invoices_by_username(client):
    client.post("/billing/invoices", json={"username": "alice", "amount_cents": 500})
    client.post("/billing/invoices", json={"username": "alice", "amount_cents": 700})

    resp = client.get("/billing/invoices", query_string={"username": "alice"})
    assert resp.status_code == 200
    assert len(resp.get_json()) == 2


def test_pay_invoice_updates_status(client):
    invoice_id = client.post(
        "/billing/invoices", json={"username": "alice", "amount_cents": 500}
    ).get_json()["invoice_id"]

    resp = client.post(f"/billing/invoices/{invoice_id}/pay")
    assert resp.status_code == 200
    assert client.get(f"/billing/invoices/{invoice_id}").get_json()["status"] == "paid"
