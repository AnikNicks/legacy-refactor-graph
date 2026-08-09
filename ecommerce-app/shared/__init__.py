from flask import Flask

from shared.db import init_db


def create_app():
    app = Flask(__name__)

    init_db()

    from cart.routes import cart_bp
    from catalog.routes import catalog_bp
    from inventory.routes import inventory_bp

    app.register_blueprint(catalog_bp)
    app.register_blueprint(inventory_bp)
    app.register_blueprint(cart_bp)

    return app
