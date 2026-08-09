import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "legacy-app"))

import shared.db as db_module  # noqa: E402


@pytest.fixture()
def client(tmp_path, monkeypatch):
    # Each test gets its own throwaway sqlite file — never legacy-app/shared/data.db.
    db_path = tmp_path / "test_data.db"
    monkeypatch.setattr(db_module, "DB_PATH", str(db_path))

    # auth._user_cache and billing.INVOICE_CACHE are process-global dicts;
    # reset them per test so state can't leak across tests through the cache
    # the way it can leak across requests in the real (unmodified) app.
    import auth.routes as auth_routes

    auth_routes._user_cache.clear()

    from auth import directory as auth_directory

    auth_directory._directory_cache.clear()

    import billing.routes as billing_routes

    billing_routes.INVOICE_CACHE.clear()

    from shared import create_app

    app = create_app()
    app.config["TESTING"] = True

    with app.test_client() as c:
        yield c
