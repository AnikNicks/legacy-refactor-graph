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
        CREATE TABLE IF NOT EXISTS patients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            dob TEXT,
            ssn TEXT,
            phone TEXT
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS appointments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id INTEGER NOT NULL REFERENCES patients(id),
            provider TEXT NOT NULL,
            scheduled_at TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'scheduled'
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS medical_notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id INTEGER NOT NULL REFERENCES patients(id),
            note TEXT NOT NULL,
            author TEXT,
            created_at TEXT
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS audit_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            action TEXT NOT NULL,
            patient_id INTEGER,
            query TEXT,
            requester TEXT,
            created_at TEXT NOT NULL
        )
        """
    )
    conn.commit()
    conn.close()
