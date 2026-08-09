"""The interface auth deliberately exposes to other modules.

Other modules should depend on this, not on auth.routes' internal
_user_cache dict directly — that direct-dict coupling is exactly what
stage 3 removes from notes. This stage only introduces the interface and
proves it behaves the same as the old direct-dict pattern; auth.routes still
keeps _user_cache alive and in sync so nothing importing it breaks before
stage 3 migrates.
"""

from shared.db import get_db

# Intentionally a separate dict from auth.routes' _user_cache for this
# stage — both exist and are kept in sync by auth.routes so the old and new
# paths can be proven equivalent (see tests/test_auth_directory_contract.py)
# before anything depends solely on this one.
_directory_cache = {}


def is_known_user(username):
    """True if username exists, checking cache first then the users table."""
    if username in _directory_cache:
        return True
    db = get_db()
    row = db.execute("SELECT password FROM users WHERE username = ?", (username,)).fetchone()
    db.close()
    if row is not None:
        _directory_cache[username] = row["password"]
    return row is not None


def verify(username, password):
    """True if username/password match, checking cache first then the users table."""
    if username in _directory_cache:
        return _directory_cache[username] == password

    db = get_db()
    row = db.execute("SELECT password FROM users WHERE username = ?", (username,)).fetchone()
    db.close()
    ok = row is not None and row["password"] == password
    if ok:
        _directory_cache[username] = password
    return ok


def remember(username, password):
    """Explicitly warm the cache after a write (e.g. a successful register)."""
    _directory_cache[username] = password
