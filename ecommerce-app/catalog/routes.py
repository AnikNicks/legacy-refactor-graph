from flask import Blueprint, jsonify, request

from shared.db import get_db

catalog_bp = Blueprint("catalog", __name__)


@catalog_bp.route("/products", methods=["GET"])
def list_products():
    db = get_db()
    products = db.execute("SELECT id, name, price_cents, category FROM products").fetchall()

    # N+1: one query to list products, then one more query PER product to get
    # its stock instead of a single join. Fine at demo scale, falls over as
    # the catalog grows - a classic "worked in the demo" performance smell.
    result = []
    for p in products:
        stock_row = db.execute(
            "SELECT stock_qty FROM inventory WHERE product_id = ?", (p["id"],)
        ).fetchone()
        result.append(
            {
                "id": p["id"],
                "name": p["name"],
                "price_cents": p["price_cents"],
                "category": p["category"],
                "stock_qty": stock_row["stock_qty"] if stock_row else 0,
            }
        )
    db.close()
    return jsonify(result)


@catalog_bp.route("/products/<int:product_id>", methods=["GET"])
def get_product(product_id):
    db = get_db()
    row = db.execute(
        "SELECT id, name, price_cents, category FROM products WHERE id = ?", (product_id,)
    ).fetchone()
    if not row:
        db.close()
        return jsonify({"error": "not found"}), 404

    stock_row = db.execute(
        "SELECT stock_qty FROM inventory WHERE product_id = ?", (product_id,)
    ).fetchone()
    db.close()
    return jsonify(
        {
            "id": row["id"],
            "name": row["name"],
            "price_cents": row["price_cents"],
            "category": row["category"],
            "stock_qty": stock_row["stock_qty"] if stock_row else 0,
        }
    )


@catalog_bp.route("/products", methods=["POST"])
def create_product():
    data = request.get_json(force=True)
    db = get_db()
    cur = db.execute(
        "INSERT INTO products (name, price_cents, category) VALUES (?, ?, ?)",
        (data.get("name"), data.get("price_cents"), data.get("category")),
    )
    product_id = cur.lastrowid
    db.execute(
        "INSERT INTO inventory (product_id, stock_qty) VALUES (?, ?)",
        (product_id, data.get("initial_stock", 0)),
    )
    db.commit()
    db.close()
    return jsonify({"id": product_id}), 201
