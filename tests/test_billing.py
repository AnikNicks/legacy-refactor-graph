import sqlite3


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


def test_pay_invoice_does_not_mark_cache_paid_when_db_write_fails(client, monkeypatch):
    # Stage 4 fixed the bug this test locks in: pay_invoice's bare except
    # used to swallow any DB failure and still mark the cache "paid"
    # regardless, so the cache and the DB could disagree about whether money
    # was actually collected. Forces a real failure via a fake connection
    # rather than relying on real DB locking, which isn't reliably
    # reproducible in a test.
    import billing.routes as billing_routes

    invoice_id = client.post(
        "/billing/invoices", json={"username": "alice", "amount_cents": 500}
    ).get_json()["invoice_id"]

    # Warm the cache via a GET so INVOICE_CACHE actually holds this invoice.
    client.get(f"/billing/invoices/{invoice_id}")
    assert billing_routes.INVOICE_CACHE[invoice_id]["status"] == "pending"

    class _FailingConn:
        def execute(self, *args, **kwargs):
            raise sqlite3.OperationalError("simulated DB failure")

        def close(self):
            pass

    monkeypatch.setattr(billing_routes, "get_db", lambda: _FailingConn())

    resp = client.post(f"/billing/invoices/{invoice_id}/pay")
    assert resp.status_code == 500

    # The fix: cache must NOT say "paid" when the DB write failed.
    assert billing_routes.INVOICE_CACHE[invoice_id]["status"] == "pending"
