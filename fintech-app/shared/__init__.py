from flask import Flask

from shared.db import init_db


def create_app():
    app = Flask(__name__)

    init_db()

    from accounts.routes import accounts_bp
    from ledger.routes import ledger_bp
    from transactions.routes import transactions_bp

    app.register_blueprint(accounts_bp)
    app.register_blueprint(transactions_bp)
    app.register_blueprint(ledger_bp)

    return app
