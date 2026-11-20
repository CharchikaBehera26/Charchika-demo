from srujansetu import create_app
from srujansetu.extensions import db
from sqlalchemy import inspect


app = create_app()


if __name__ == "__main__":
    with app.app_context():
        if not inspect(db.engine).has_table("app_metadata"):
            raise SystemExit(
                "Database schema is not initialized. Run "
                "'python -m flask --app app db upgrade' first."
            )
    app.run(debug=app.config.get("DEBUG", False))
