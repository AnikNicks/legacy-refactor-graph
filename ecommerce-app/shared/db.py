import os
import sqlite3

DB_PATH = os.path.join(os.path.dirname(__file__), "data.db")


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            price_cents INTEGER NOT NULL,
            category TEXT
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS inventory (
            product_id INTEGER PRIMARY KEY REFERENCES products(id),
            stock_qty INTEGER NOT NULL DEFAULT 0
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            status TEXT NOT NULL DEFAULT 'placed',
            total_cents INTEGER NOT NULL,
            created_at TEXT,
            idempotency_key TEXT UNIQUE
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS order_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER NOT NULL REFERENCES orders(id),
            product_id INTEGER NOT NULL REFERENCES products(id),
            qty INTEGER NOT NULL,
            unit_price_cents INTEGER NOT NULL
        )
        """
    )
    conn.commit()
    conn.close()
