def test_register_creates_user(client):
    resp = client.post("/register", json={"username": "bob", "password": "pw1", "email": "b@x.com"})
    assert resp.status_code == 201
    assert resp.get_json() == {"status": "registered", "username": "bob"}


def test_register_missing_fields(client):
    resp = client.post("/register", json={"username": "bob"})
    assert resp.status_code == 400


def test_register_duplicate_username_fails(client):
    client.post("/register", json={"username": "bob", "password": "pw1"})
    resp = client.post("/register", json={"username": "bob", "password": "pw2"})
    assert resp.status_code == 400
    assert resp.get_json() == {"error": "registration failed"}


def test_login_success(client):
    client.post("/register", json={"username": "bob", "password": "pw1"})
    resp = client.post("/login", json={"username": "bob", "password": "pw1"})
    assert resp.status_code == 200
    assert resp.get_json() == {"status": "ok", "username": "bob"}


def test_login_wrong_password(client):
    client.post("/register", json={"username": "bob", "password": "pw1"})
    resp = client.post("/login", json={"username": "bob", "password": "wrong"})
    assert resp.status_code == 401


def test_login_reads_through_to_db_when_cache_cold(client):
    # Characterizes the cache-miss path: register warms the cache, but if we
    # clear it (simulating a fresh process), login must still succeed by
    # reading the users table directly rather than failing.
    import auth.routes as auth_routes

    client.post("/register", json={"username": "carol", "password": "pw3"})
    auth_routes._user_cache.clear()

    resp = client.post("/login", json={"username": "carol", "password": "pw3"})
    assert resp.status_code == 200


def test_profile_lookup(client):
    client.post("/register", json={"username": "dave", "password": "pw4", "email": "d@x.com"})
    resp = client.get("/users/dave")
    assert resp.status_code == 200
    assert resp.get_json()["username"] == "dave"


def test_profile_lookup_unknown_user(client):
    resp = client.get("/users/ghost")
    assert resp.status_code == 404


def test_logout_is_a_noop(client):
    resp = client.post("/logout")
    assert resp.status_code == 200
    assert resp.get_json() == {"status": "ok"}
