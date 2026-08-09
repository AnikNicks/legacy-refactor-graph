from flask import Blueprint, jsonify, request

from shared.db import get_db

auth_bp = Blueprint("auth", __name__)

# Added later to "speed up" login checks. Nothing invalidates this when a user
# is created by a different process, and it never expires or bounds its size.
_user_cache = {}


@auth_bp.route("/register", methods=["POST"])
def register():
    data = request.get_json(force=True)
    username = data.get("username")
    password = data.get("password")
    if not username or not password:
        return jsonify({"error": "username and password required"}), 400

    db = get_db()
    try:
        db.execute(
            "INSERT INTO users (username, password, email) VALUES (?, ?, ?)",
            (username, password, data.get("email")),
        )
        db.commit()
    except Exception:
        # Swallows duplicate-username errors, disk errors, everything alike.
        return jsonify({"error": "registration failed"}), 400
    finally:
        db.close()

    _user_cache[username] = password
    return jsonify({"status": "registered", "username": username}), 201


@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json(force=True)
    username = data.get("username")
    password = data.get("password")

    if username in _user_cache:
        ok = _user_cache[username] == password
    else:
        db = get_db()
        row = db.execute(
            "SELECT password FROM users WHERE username = ?", (username,)
        ).fetchone()
        db.close()
        ok = row is not None and row["password"] == password
        if ok:
            _user_cache[username] = password

    if not ok:
        return jsonify({"error": "invalid credentials"}), 401
    return jsonify({"status": "ok", "username": username})


@auth_bp.route("/users/<username>", methods=["GET"])
def profile(username):
    # Reads whatever's cheapest: cache first, DB only as a fallback, so a
    # stale cache entry silently shadows a real password change in the DB.
    if username in _user_cache:
        return jsonify({"username": username, "source": "cache"})

    db = get_db()
    row = db.execute(
        "SELECT username, email FROM users WHERE username = ?", (username,)
    ).fetchone()
    db.close()
    if not row:
        return jsonify({"error": "not found"}), 404
    return jsonify({"username": row["username"], "email": row["email"], "source": "db"})


@auth_bp.route("/logout", methods=["POST"])
def logout():
    # No session state exists anywhere, so this does nothing. Kept because a
    # frontend somewhere still calls it.
    return jsonify({"status": "ok"})
