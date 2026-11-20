import os
from pathlib import Path
from datetime import datetime

from dotenv import load_dotenv
from flask import Flask, render_template, session
from sqlalchemy import inspect

from .config import Config, PROJECT_ROOT, get_database_uri
from .extensions import db, migrate
from .services.data_store import seed_demo_data
from .services.security import csrf_value, current_artisan_account


def create_app(test_config=None):
    load_dotenv(PROJECT_ROOT / ".env")

    app = Flask(
        __name__,
        template_folder=str(PROJECT_ROOT / "templates"),
        static_folder=str(PROJECT_ROOT / "static"),
    )
    app.config.from_object(Config)
    app.config["SQLALCHEMY_DATABASE_URI"] = get_database_uri()
    app.config["SECRET_KEY"] = os.environ.get(
        "SECRET_KEY",
        "dev-only-change-this-secret-before-deployment",
    )
    if test_config:
        app.config.update(test_config)

    Path(app.config["UPLOAD_FOLDER"]).mkdir(parents=True, exist_ok=True)
    (PROJECT_ROOT / "instance").mkdir(parents=True, exist_ok=True)

    db.init_app(app)
    migrate.init_app(app, db)

    from .blueprints.admin import admin_bp
    from .blueprints.artisan import artisan_bp
    from .blueprints.public import public_bp

    app.register_blueprint(public_bp)
    app.register_blueprint(artisan_bp)
    app.register_blueprint(admin_bp)

    @app.context_processor
    def inject_template_context():
        return {
            "current_year": datetime.now().year,
            "csrf_token": csrf_value,
            "admin_logged_in": (
                session.get("role") == "admin"
                and bool(session.get("admin_user"))
            ),
            "artisan_logged_in": (
                session.get("role") == "artisan"
                and bool(session.get("artisan_user_id"))
            ),
            "current_artisan": current_artisan_account(),
        }

    @app.errorhandler(404)
    def not_found(_error):
        return render_template("404.html"), 404

    @app.cli.command("seed-demo-data")
    def seed_demo_data_command():
        """Import the existing sample JSON files into an empty database."""
        seed_demo_data()
        print("Demo data import complete.")

    with app.app_context():
        if inspect(db.engine).has_table("app_metadata"):
            seed_demo_data()

    return app
