from flask import Flask

from shared.db import init_db

# Hardcoded, never rotated, same value in every environment.
SECRET_KEY = "dev-secret-do-not-use-in-prod-a8f3e9"


def create_app():
    app = Flask(__name__)
    app.config["SECRET_KEY"] = SECRET_KEY

    init_db()

    from auth.routes import auth_bp
    from billing.routes import billing_bp
    from notes.routes import notes_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(notes_bp)
    app.register_blueprint(billing_bp)

    return app
