import os
from pathlib import Path
from datetime import datetime

from dotenv import load_dotenv
from flask import Flask, render_template, session
from sqlalchemy import inspect
from werkzeug.middleware.proxy_fix import ProxyFix

from .config import Config, PROJECT_ROOT, get_database_uri
from .extensions import db, migrate
from .services.data_store import seed_demo_data
from .services.gallery import media
from .services.i18n import craft_description, chrome_for, normalize_lang, translate_text
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
    app.config["SUPABASE_URL"] = os.environ.get(
        "SUPABASE_URL",
        app.config["SUPABASE_URL"],
    ).strip().rstrip("/")
    app.config["SUPABASE_ANON_KEY"] = os.environ.get(
        "SUPABASE_PUBLISHABLE_KEY",
        os.environ.get(
            "SUPABASE_ANON_KEY",
            app.config["SUPABASE_ANON_KEY"],
        ),
    ).strip()
    app.config["PUBLIC_BASE_URL"] = os.environ.get(
        "PUBLIC_BASE_URL",
        app.config["PUBLIC_BASE_URL"],
    ).strip().rstrip("/")
    app.config["SESSION_COOKIE_SECURE"] = os.environ.get(
        "SESSION_COOKIE_SECURE",
        str(app.config["SESSION_COOKIE_SECURE"]),
    ).lower() == "true"
    if test_config:
        app.config.update(test_config)
    app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1)

    Path(app.config["UPLOAD_FOLDER"]).mkdir(parents=True, exist_ok=True)
    (PROJECT_ROOT / "instance").mkdir(parents=True, exist_ok=True)

    db.init_app(app)
    migrate.init_app(app, db)

    from .blueprints.admin import admin_bp
    from .blueprints.artisan import artisan_bp
    from .blueprints.public import public_bp
    from .blueprints.shop import current_customer_account, shop_bp

    app.register_blueprint(public_bp)
    app.register_blueprint(artisan_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(shop_bp)

    @app.context_processor
    def inject_template_context():
        lang = normalize_lang(session.get("lang"))
        cart = session.get("cart", {})
        if not isinstance(cart, dict):
            cart = {}
        return {
            "current_year": datetime.now().year,
            "lang": lang,
            "chrome": chrome_for(lang),
            "tr": lambda value: translate_text(value, lang),
            "craft_description": lambda name, fallback: craft_description(name, fallback, lang),
            "media": media,
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
            "customer_logged_in": (
                session.get("role") == "customer"
                and bool(current_customer_account())
            ),
            "current_customer": current_customer_account(),
            "supabase_google_enabled": bool(
                app.config.get("SUPABASE_URL")
                and app.config.get("SUPABASE_ANON_KEY")
            ),
            "supabase_google_admin_enabled": bool(
                app.config.get("SUPABASE_URL")
                and app.config.get("SUPABASE_ANON_KEY")
                and app.config.get("GOOGLE_ADMIN_EMAILS")
            ),
            "cart_count": sum(
                int(quantity) for quantity in cart.values()
                if str(quantity).isdigit() and 0 <= int(quantity) <= 99
            ),
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
        schema = inspect(db.engine)
        if schema.has_table("app_metadata") and all(
            schema.has_table(table.name)
            and {
                column["name"]
                for column in schema.get_columns(table.name)
            } >= {column.name for column in table.columns}
            for table in db.metadata.sorted_tables
        ):
            seed_demo_data()

    return app
