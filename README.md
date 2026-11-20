# SrujanSetu

SrujanSetu is a Flask multi-page website for exploring Odisha crafts, artisan and SHG profiles, a sample marketplace, and a map of makers who choose to publish their location. Pages are rendered with Jinja templates; opening a template directly in a static preview will not render Flask template syntax or load routes correctly.

## Requirements

- Python 3.10 or newer
- A Supabase PostgreSQL database for hosted use; local development can use SQLite

## Local setup

From the project directory in PowerShell:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

The default database is `instance/srujansetu.sqlite`. To use Supabase, edit `.env` and set `DATABASE_URL` to the PostgreSQL connection URI from the Supabase project settings. Keep `.env` private and never place database credentials in browser code or commit them. Set `SECRET_KEY` in `.env` to a long, random value before deployment.

Initialize the database and start the website:

```powershell
python -m flask --app app db upgrade
python app.py
```

Open the local address printed by Flask. The existing JSON files in `data/` are used once as starter content when the application first starts against an initialized database; later starts do not overwrite database content.

If a local database already contains the application tables but has no Alembic migration record, back it up and verify that its schema matches the current models before marking it at the current revision:

```powershell
python -m flask --app app db stamp head
```

Do not run `stamp` on an unknown or mismatched database; it records migration state without changing the tables.

## Project layout

- `app.py` — Flask entry point
- `srujansetu/` — application factory, configuration, SQLAlchemy models, blueprints, and services
- `templates/` — shared layout and multi-page Jinja templates
- `static/` — CSS, JavaScript, and uploaded product images
- `data/` — starter JSON files imported into an empty database
- `migrations/` — Flask-Migrate / Alembic schema history
- `tests/` — focused FAQ and assistant route tests

## Tests

Run the focused tests with:

```powershell
python -m unittest discover -s tests -v
```

The guide uses a cached local FAQ catalog and links to relevant site pages. It is not a generative AI service and does not send questions to an external provider.
