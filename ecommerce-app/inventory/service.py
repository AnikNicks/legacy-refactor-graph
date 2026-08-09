"""The interface inventory deliberately exposes to other modules.

cart should depend on this, not reimplement its own stock-decrement SQL -
that duplication (two independent, non-atomic implementations of the same
operation) is exactly what stage 2 removes from cart.
"""

from shared.db import get_db


class UnknownProductError(Exception):
    pass


class InsufficientStockError(Exception):
    pass


def decrement_stock(product_id, qty, conn=None):
    """Atomically decrement stock_qty by qty. Returns the new stock_qty.

    Raises UnknownProductError if product_id doesn't exist, or
    InsufficientStockError if qty exceeds the current stock.

    Pass `conn` when the caller needs this decrement to participate in its
    own transaction (e.g. cart.checkout, so a later item failing rolls back
    an earlier item's already-applied decrement along with everything else
    in the same checkout) - without it, this opens, commits, and closes its
    own connection, appropriate for a standalone call like the /adjust route.
    """
    owns_connection = conn is None
    db = conn if conn is not None else get_db()

    cur = db.execute(
        "UPDATE inventory SET stock_qty = stock_qty - ? WHERE product_id = ? AND stock_qty - ? >= 0",
        (qty, product_id, qty),
    )
    if owns_connection:
        db.commit()

    if cur.rowcount == 0:
        row = db.execute(
            "SELECT stock_qty FROM inventory WHERE product_id = ?", (product_id,)
        ).fetchone()
        if owns_connection:
            db.close()
        if row is None:
            raise UnknownProductError(product_id)
        raise InsufficientStockError(product_id)

    row = db.execute("SELECT stock_qty FROM inventory WHERE product_id = ?", (product_id,)).fetchone()
    if owns_connection:
        db.close()
    return row["stock_qty"]
