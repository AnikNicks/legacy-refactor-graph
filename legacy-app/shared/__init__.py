import os

from flask import Flask

from shared.db import init_db

# Obviously-fake fallback, used only when SECRET_KEY isn't set in the
# environment - keeps local/dev usage and this repo's own tests working
# without requiring the variable, without being a real secret anyone could
# mistake for production-worthy.
_FALLBACK_SECRET_KEY = "insecure-dev-only-fallback-not-a-real-secret"


def create_app():
    app = Flask(__name__)
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", _FALLBACK_SECRET_KEY)

    init_db()

    from auth.routes import auth_bp
    from billing.routes import billing_bp
    from notes.routes import notes_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(notes_bp)
    app.register_blueprint(billing_bp)

    return app
