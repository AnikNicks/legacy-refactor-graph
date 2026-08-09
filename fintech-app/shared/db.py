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
        CREATE TABLE IF NOT EXISTS accounts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            owner TEXT NOT NULL,
            balance REAL NOT NULL DEFAULT 0
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            from_account INTEGER NOT NULL REFERENCES accounts(id),
            to_account INTEGER NOT NULL REFERENCES accounts(id),
            amount REAL NOT NULL,
            status TEXT NOT NULL DEFAULT 'completed',
            created_at TEXT,
            idempotency_key TEXT UNIQUE
        )
        """
    )
    conn.commit()
    conn.close()
