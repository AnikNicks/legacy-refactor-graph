import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "fintech-app"))

import shared.db as db_module  # noqa: E402


@pytest.fixture()
def client(tmp_path, monkeypatch):
    # Each test gets its own throwaway sqlite file — never fintech-app/shared/data.db.
    db_path = tmp_path / "test_data.db"
    monkeypatch.setattr(db_module, "DB_PATH", str(db_path))

    from shared import create_app

    app = create_app()
    app.config["TESTING"] = True

    with app.test_client() as c:
        yield c
