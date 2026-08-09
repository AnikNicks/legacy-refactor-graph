# These tests create their own app instances directly (rather than using the
# `client` fixture's app) to control SECRET_KEY per test, but still need the
# fixture's DB_PATH monkeypatching active so create_app()'s init_db() call
# doesn't touch the real legacy-app/shared/data.db.


def test_secret_key_falls_back_when_env_var_unset(client, monkeypatch):
    monkeypatch.delenv("SECRET_KEY", raising=False)

    from shared import _FALLBACK_SECRET_KEY, create_app

    app = create_app()
    assert app.config["SECRET_KEY"] == _FALLBACK_SECRET_KEY


def test_secret_key_reads_from_environment_when_set(client, monkeypatch):
    # Stage 5: SECRET_KEY is no longer hardcoded - setting the environment
    # variable before the app is created must actually take effect.
    monkeypatch.setenv("SECRET_KEY", "a-real-secret-set-via-env")

    from shared import create_app

    app = create_app()
    assert app.config["SECRET_KEY"] == "a-real-secret-set-via-env"
