from flask import Flask

from shared.db import init_db


def create_app():
    app = Flask(__name__)

    init_db()

    from appointments.routes import appointments_bp
    from patients.routes import patients_bp
    from records.routes import records_bp

    app.register_blueprint(patients_bp)
    app.register_blueprint(appointments_bp)
    app.register_blueprint(records_bp)

    return app
