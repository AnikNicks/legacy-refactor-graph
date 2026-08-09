def _register_and_login(client, username="alice", password="hunter2"):
    client.post("/register", json={"username": username, "password": password, "email": "a@x.com"})
    client.post("/login", json={"username": username, "password": password})


def test_create_note_for_known_user(client):
    _register_and_login(client)
    resp = client.post("/notes", json={"username": "alice", "title": "hi", "body": "first note"})
    assert resp.status_code == 201
    assert resp.get_json() == {"status": "created"}


def test_create_note_for_unknown_user_is_rejected(client):
    # Characterizes current behavior, which is arguably a bug: a user who
    # exists in the database but hasn't logged in yet *in this process* gets
    # rejected, because notes gates on auth's in-memory cache, not the DB.
    resp = client.post("/notes", json={"username": "nobody", "title": "x", "body": "y"})
    assert resp.status_code == 403
    assert resp.get_json() == {"error": "unknown user"}


def test_list_notes_returns_created_note(client):
    _register_and_login(client)
    client.post("/notes", json={"username": "alice", "title": "hi", "body": "first note"})
    resp = client.get("/notes/alice")
    assert resp.status_code == 200
    notes = resp.get_json()
    assert len(notes) == 1
    assert notes[0]["title"] == "hi"
    assert notes[0]["body"] == "first note"


def test_update_note(client):
    _register_and_login(client)
    client.post("/notes", json={"username": "alice", "title": "hi", "body": "first note"})
    note_id = client.get("/notes/alice").get_json()[0]["id"]

    resp = client.put(f"/notes/{note_id}", json={"title": "updated", "body": "new body"})
    assert resp.status_code == 200

    notes = client.get("/notes/alice").get_json()
    assert notes[0]["title"] == "updated"
    assert notes[0]["body"] == "new body"


def test_delete_note(client):
    _register_and_login(client)
    client.post("/notes", json={"username": "alice", "title": "hi", "body": "first note"})
    note_id = client.get("/notes/alice").get_json()[0]["id"]

    resp = client.delete(f"/notes/{note_id}")
    assert resp.status_code == 200
    assert client.get("/notes/alice").get_json() == []


def test_create_note_with_apostrophe_in_title_is_stored_literally(client):
    # Stage 1 (parameterize notes' SQL) fixed this: an apostrophe in the
    # title used to crash the string-formatted INSERT with
    # sqlite3.OperationalError. It's now stored as ordinary data — this
    # test's flip from "raises" to "succeeds" is the proof the fix worked.
    _register_and_login(client)
    resp = client.post("/notes", json={"username": "alice", "title": "it's broken", "body": "x"})
    assert resp.status_code == 201

    notes = client.get("/notes/alice").get_json()
    assert notes[0]["title"] == "it's broken"
