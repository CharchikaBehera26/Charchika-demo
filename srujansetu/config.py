import os
import warnings
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent


def _sqlite_database_uri():
    sqlite_path = (PROJECT_ROOT / "instance" / "srujansetu.sqlite").as_posix()
    return f"sqlite:///{sqlite_path}"


def get_database_uri():
    database_uri = os.environ.get("DATABASE_URL", "").strip()
    require_database = os.environ.get("REQUIRE_DATABASE_URL", "").lower() == "true"
    if not database_uri:
        if require_database:
            raise RuntimeError(
                "DATABASE_URL is required for this deployment. Configure the "
                "Supabase PostgreSQL connection string."
            )
        return _sqlite_database_uri()
    if "<" in database_uri and ">" in database_uri:
        if require_database:
            raise RuntimeError(
                "DATABASE_URL still contains template placeholders. Configure "
                "the Supabase PostgreSQL connection string."
            )
        warnings.warn(
            "DATABASE_URL still contains template placeholders; using the local "
            "SQLite database. Set DATABASE_URL to a real database URL to use it.",
            RuntimeWarning,
            stacklevel=2,
        )
        return _sqlite_database_uri()
    if require_database and not database_uri.startswith(
        ("postgres://", "postgresql://", "postgresql+psycopg://")
    ):
        raise RuntimeError(
            "DATABASE_URL must point to PostgreSQL when "
            "REQUIRE_DATABASE_URL=true."
        )
    if (
        os.name == "nt"
        and (database_uri.startswith("postgres://") or database_uri.startswith("postgresql://"))
    ):
        try:
            import psycopg  # noqa: F401
        except (ImportError, OSError):
            warnings.warn(
                "PostgreSQL driver could not be loaded; "
                "using the local SQLite database.",
                RuntimeWarning,
                stacklevel=2,
            )
            return _sqlite_database_uri()
    if database_uri.startswith("postgres://"):
        return database_uri.replace("postgres://", "postgresql+psycopg://", 1)
    if database_uri.startswith("postgresql://"):
        return database_uri.replace("postgresql://", "postgresql+psycopg://", 1)
    return database_uri


class Config:
    SECRET_KEY = os.environ.get(
        "SECRET_KEY",
        "dev-only-change-this-secret-before-deployment",
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SUPABASE_URL = os.environ.get("SUPABASE_URL", "").strip().rstrip("/")
    SUPABASE_ANON_KEY = os.environ.get(
        "SUPABASE_PUBLISHABLE_KEY",
        os.environ.get("SUPABASE_ANON_KEY", ""),
    ).strip()
    PUBLIC_BASE_URL = os.environ.get("PUBLIC_BASE_URL", "").strip().rstrip("/")
    GOOGLE_ADMIN_EMAILS = os.environ.get("GOOGLE_ADMIN_EMAILS", "").strip()
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = (
        os.environ.get("SESSION_COOKIE_SECURE", "false").lower() == "true"
    )
    PREFERRED_URL_SCHEME = "https"
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
        "pool_recycle": 300,
    }
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024
    DATA_DIR = PROJECT_ROOT / "data"
    UPLOAD_FOLDER = PROJECT_ROOT / "static" / "uploads"
    JSON_SEED_FILES = {
        "artisans": DATA_DIR / "artisans.json",
        "crafts": DATA_DIR / "crafts.json",
        "products": DATA_DIR / "products.json",
        "schemes": DATA_DIR / "schemes.json",
        "stories": DATA_DIR / "stories.json",
        "community": DATA_DIR / "community.json",
        "artisan_users": DATA_DIR / "artisan_users.json",
        "admin": DATA_DIR / "admin.json",
    }
