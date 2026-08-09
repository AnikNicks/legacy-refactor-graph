# Stage 2 introduced auth.directory as the interface other modules should
# use instead of reaching into auth.routes._user_cache directly (that's
# exactly what stage 3 does for notes). This stage keeps both the old dict
# and the new interface alive and updated in parallel, which means they're
# now two independently-populated caches that *could* drift apart if a
# future edit updates one path but not the other. These tests lock in that
# they don't, across every scenario the acceptance criteria named: register,
# login cache-hit, login cache-miss, and profile lookup.


def test_directory_interface_agrees_with_legacy_cache_after_register(client):
    import auth.routes as auth_routes
    from auth import directory

    client.post("/register", json={"username": "erin", "password": "pw5", "email": "e@x.com"})

    assert directory.is_known_user("erin") == ("erin" in auth_routes._user_cache)
    assert directory.verify("erin", "pw5") == (auth_routes._user_cache.get("erin") == "pw5")


def test_directory_interface_agrees_with_legacy_cache_after_login_cache_hit(client):
    import auth.routes as auth_routes
    from auth import directory

    client.post("/register", json={"username": "frank", "password": "pw6"})
    client.post("/login", json={"username": "frank", "password": "pw6"})

    assert directory.is_known_user("frank") == ("frank" in auth_routes._user_cache)
    assert directory.verify("frank", "pw6") == (auth_routes._user_cache.get("frank") == "pw6")


def test_directory_interface_agrees_with_legacy_cache_after_login_cache_cold(client):
    import auth.routes as auth_routes
    from auth import directory

    client.post("/register", json={"username": "grace", "password": "pw7"})
    auth_routes._user_cache.clear()
    directory._directory_cache.clear()

    resp = client.post("/login", json={"username": "grace", "password": "pw7"})
    assert resp.status_code == 200

    assert directory.is_known_user("grace") == ("grace" in auth_routes._user_cache)
    assert directory.verify("grace", "pw7") == (auth_routes._user_cache.get("grace") == "pw7")


def test_directory_interface_agrees_for_profile_lookup(client):
    import auth.routes as auth_routes
    from auth import directory

    client.post("/register", json={"username": "henry", "password": "pw8", "email": "h@x.com"})
    client.get("/users/henry")

    assert directory.is_known_user("henry") == ("henry" in auth_routes._user_cache)


def test_directory_interface_agrees_on_unknown_user(client):
    from auth import directory

    assert directory.is_known_user("nobody-at-all") is False
    assert directory.verify("nobody-at-all", "whatever") is False
