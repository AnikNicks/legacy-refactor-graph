from flask import Blueprint, jsonify, request

from shared.db import get_db

# Reaches directly into auth's internals instead of going through any
# interface — notes has no idea auth even has a database-backed users table.
from auth.routes import _user_cache

notes_bp = Blueprint("notes", __name__)


@notes_bp.route("/notes", methods=["POST"])
def create_note():
    data = request.get_json(force=True)
    username = data.get("username")
    title = data.get("title")
    body = data.get("body", "")

    # Only accepts notes for users already warm in auth's cache, so a
    # freshly-registered user who hasn't logged in yet in this process gets
    # rejected even though they exist in the users table.
    if username not in _user_cache:
        return jsonify({"error": "unknown user"}), 403

    db = get_db()
    db.execute(
        "INSERT INTO notes (username, title, body, created_at) VALUES (?, ?, ?, datetime('now'))",
        (username, title, body),
    )
    db.commit()
    db.close()
    return jsonify({"status": "created"}), 201


@notes_bp.route("/notes/<username>", methods=["GET"])
def list_notes(username):
    db = get_db()
    rows = db.execute(
        "SELECT id, title, body, created_at FROM notes WHERE username = ?", (username,)
    ).fetchall()
    db.close()
    return jsonify([dict(r) for r in rows])


@notes_bp.route("/notes/<int:note_id>", methods=["PUT"])
def update_note(note_id):
    data = request.get_json(force=True)
    title = data.get("title")
    body = data.get("body", "")

    db = get_db()
    db.execute(
        "UPDATE notes SET title = ?, body = ? WHERE id = ?", (title, body, note_id)
    )
    db.commit()
    db.close()
    return jsonify({"status": "updated"})


@notes_bp.route("/notes/<int:note_id>", methods=["DELETE"])
def delete_note(note_id):
    db = get_db()
    # The one route in this module that's parameterized correctly.
    db.execute("DELETE FROM notes WHERE id = ?", (note_id,))
    db.commit()
    db.close()
    return jsonify({"status": "deleted"})
