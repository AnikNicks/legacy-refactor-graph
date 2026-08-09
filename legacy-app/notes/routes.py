from flask import Blueprint, jsonify, request

from auth import directory
from shared.db import get_db

notes_bp = Blueprint("notes", __name__)


@notes_bp.route("/notes", methods=["POST"])
def create_note():
    data = request.get_json(force=True)
    username = data.get("username")
    title = data.get("title")
    body = data.get("body", "")

    # Goes through auth's declared interface instead of reaching into its
    # internal cache dict. is_known_user does a proper cache-then-DB
    # read-through, so (unlike the old direct _user_cache check) a user who
    # registered but never logged in is correctly recognized as known.
    if not directory.is_known_user(username):
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
