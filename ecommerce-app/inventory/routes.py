from flask import Blueprint, jsonify, request

from shared.db import get_db

inventory_bp = Blueprint("inventory", __name__)


@inventory_bp.route("/inventory/<int:product_id>", methods=["GET"])
def get_stock(product_id):
    db = get_db()
    row = db.execute(
        "SELECT stock_qty FROM inventory WHERE product_id = ?", (product_id,)
    ).fetchone()
    db.close()
    if not row:
        return jsonify({"error": "not found"}), 404
    return jsonify({"product_id": product_id, "stock_qty": row["stock_qty"]})


@inventory_bp.route("/inventory/<int:product_id>/adjust", methods=["POST"])
def adjust_stock(product_id):
    data = request.get_json(force=True)
    delta = int(data.get("delta", 0))

    # Atomic and guarded: a single UPDATE with the "would it go negative"
    # check in its own WHERE clause, so sqlite's row locking - not a
    # Python-level read-then-write race - is what decides whether the
    # decrement applies. Two concurrent requests against the same product
    # can no longer both succeed off a stale read.
    db = get_db()
    cur = db.execute(
        "UPDATE inventory SET stock_qty = stock_qty + ? WHERE product_id = ? AND stock_qty + ? >= 0",
        (delta, product_id, delta),
    )
    db.commit()

    if cur.rowcount == 0:
        row = db.execute(
            "SELECT stock_qty FROM inventory WHERE product_id = ?", (product_id,)
        ).fetchone()
        db.close()
        if row is None:
            return jsonify({"error": "not found"}), 404
        return jsonify({"error": "insufficient stock"}), 400

    row = db.execute("SELECT stock_qty FROM inventory WHERE product_id = ?", (product_id,)).fetchone()
    db.close()
    return jsonify({"product_id": product_id, "stock_qty": row["stock_qty"]})
