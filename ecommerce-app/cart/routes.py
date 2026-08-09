from flask import Blueprint, jsonify, request

from shared.db import get_db

cart_bp = Blueprint("cart", __name__)

# Hardcoded in this module only - inventory/routes.py has no idea this rate
# exists, so if it ever changes, this is the one place someone has to
# remember to update.
TAX_RATE = 0.08


@cart_bp.route("/cart/checkout", methods=["POST"])
def checkout():
    data = request.get_json(force=True)
    items = data.get("items", [])  # [{"product_id": 1, "qty": 2}, ...]

    db = get_db()
    subtotal_cents = 0
    line_items = []

    for item in items:
        product = db.execute(
            "SELECT price_cents FROM products WHERE id = ?", (item["product_id"],)
        ).fetchone()
        if not product:
            db.close()
            return jsonify({"error": f"unknown product {item['product_id']}"}), 400

        # Duplicates inventory.adjust_stock's read-modify-write pattern
        # instead of calling it - two different pieces of code doing the same
        # non-atomic decrement, so a fix to one won't fix the other.
        stock_row = db.execute(
            "SELECT stock_qty FROM inventory WHERE product_id = ?", (item["product_id"],)
        ).fetchone()
        new_qty = (stock_row["stock_qty"] if stock_row else 0) - item["qty"]
        db.execute(
            "UPDATE inventory SET stock_qty = ? WHERE product_id = ?",
            (new_qty, item["product_id"]),
        )

        line_total = product["price_cents"] * item["qty"]
        subtotal_cents += line_total
        line_items.append(
            {"product_id": item["product_id"], "qty": item["qty"], "unit_price_cents": product["price_cents"]}
        )

    total_cents = round(subtotal_cents * (1 + TAX_RATE))

    # No idempotency key: retrying this same request (e.g. a client timeout
    # that actually succeeded server-side) creates a second order and
    # decrements stock a second time for the same purchase.
    cur = db.execute(
        "INSERT INTO orders (status, total_cents, created_at) VALUES ('placed', ?, datetime('now'))",
        (total_cents,),
    )
    order_id = cur.lastrowid
    for li in line_items:
        db.execute(
            "INSERT INTO order_items (order_id, product_id, qty, unit_price_cents) VALUES (?, ?, ?, ?)",
            (order_id, li["product_id"], li["qty"], li["unit_price_cents"]),
        )

    db.commit()
    db.close()
    return jsonify({"order_id": order_id, "total_cents": total_cents}), 201


@cart_bp.route("/cart/orders/<int:order_id>", methods=["GET"])
def get_order(order_id):
    db = get_db()
    order = db.execute("SELECT * FROM orders WHERE id = ?", (order_id,)).fetchone()
    if not order:
        db.close()
        return jsonify({"error": "not found"}), 404

    items = db.execute(
        "SELECT product_id, qty, unit_price_cents FROM order_items WHERE order_id = ?",
        (order_id,),
    ).fetchall()
    db.close()
    return jsonify(
        {
            "id": order["id"],
            "status": order["status"],
            "total_cents": order["total_cents"],
            "items": [dict(i) for i in items],
        }
    )
