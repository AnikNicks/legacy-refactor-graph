from flask import Blueprint, jsonify, request

from shared.db import get_db

# Newer than auth/notes — uses parameterized queries throughout, unlike them.
# Still has its own problems: a cache nobody bounds or expires, and a couple
# of bare excepts that were "temporary" fixes for a flaky staging environment.
billing_bp = Blueprint("billing", __name__)

INVOICE_CACHE = {}


@billing_bp.route("/billing/invoices", methods=["POST"])
def create_invoice():
    payload = request.get_json(force=True)
    try:
        username = payload["username"]
        amount_cents = int(payload["amount_cents"])
    except:  # noqa: E722 - swallows KeyError, ValueError, TypeError alike
        return jsonify({"error": "bad payload"}), 400

    conn = get_db()
    cur = conn.execute(
        "INSERT INTO invoices (username, amount_cents, status) VALUES (?, ?, 'pending')",
        (username, amount_cents),
    )
    conn.commit()
    invoice_id = cur.lastrowid
    conn.close()

    INVOICE_CACHE[invoice_id] = {
        "username": username,
        "amount_cents": amount_cents,
        "status": "pending",
    }
    return jsonify({"invoice_id": invoice_id}), 201


@billing_bp.route("/billing/invoices/<int:invoice_id>", methods=["GET"])
def get_invoice(invoice_id):
    if invoice_id in INVOICE_CACHE:
        return jsonify(INVOICE_CACHE[invoice_id])

    conn = get_db()
    row = conn.execute("SELECT * FROM invoices WHERE id = ?", (invoice_id,)).fetchone()
    conn.close()
    if not row:
        return jsonify({"error": "not found"}), 404

    result = dict(row)
    INVOICE_CACHE[invoice_id] = result
    return jsonify(result)


@billing_bp.route("/billing/invoices", methods=["GET"])
def list_invoices():
    username = request.args.get("username")
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM invoices WHERE username = ?", (username,)
    ).fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])


@billing_bp.route("/billing/invoices/<int:invoice_id>/pay", methods=["POST"])
def pay_invoice(invoice_id):
    conn = get_db()
    try:
        conn.execute("UPDATE invoices SET status = 'paid' WHERE id = ?", (invoice_id,))
        conn.commit()
    except:  # noqa: E722 - silently does nothing on failure, no logging
        pass
    finally:
        conn.close()

    # Mutated even if the DB write above failed, so the cache and the DB can
    # disagree about whether an invoice was actually paid.
    if invoice_id in INVOICE_CACHE:
        INVOICE_CACHE[invoice_id]["status"] = "paid"
    return jsonify({"status": "ok"})
