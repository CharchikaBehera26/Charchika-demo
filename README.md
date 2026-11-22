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

The default database is `instance/srujansetu.sqlite`. To use Supabase locally, set `DATABASE_URL` in `.env` to the **Session pooler** connection string from your Supabase project's **Connect** dialog (port `5432`). Set `SECRET_KEY` to a long, random value. Keep `.env` private; never place database credentials or private provider keys in browser code or commit them.

Initialize the database and start the website:

```powershell
python startall.py
```

`startall.py` applies outstanding database migrations, then starts the Flask development server. Open the local address printed by Flask. The existing JSON files in `data/` are used once as starter content when the application first starts against an initialized database; later starts do not overwrite database content.

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

## Marketplace shopping

Customers can create an account or sign in from the SHG Marketplace, add products to a cart, and submit a demo order request. Order requests are saved to the configured database and can be reviewed from **My orders**. This sample marketplace does not process payments, confirm availability, or arrange delivery; customers must contact makers directly to complete a real purchase.

## Supabase Auth and Google sign-in

Google customer sign-in uses Supabase Auth's server-side PKCE flow. Existing email/password customer accounts continue to work; when a customer signs in with a Google account that has a verified matching email, the Google identity is linked to that customer record.

1. In Google Cloud Console, create a **Web application** OAuth client. Add the website origins (local `http://127.0.0.1:5000` and your Render URL) to **Authorized JavaScript origins**.
2. In Supabase, open **Authentication → Sign In / Providers → Google**, enable Google, and enter the Google client ID and secret. Copy the Supabase callback URL shown on that page (usually `https://<project-ref>.supabase.co/auth/v1/callback`) into the Google OAuth client's **Authorized redirect URIs**.
3. In Supabase **Authentication → URL Configuration**, set the Site URL to your deployed website and add these Redirect URLs:
   - `http://127.0.0.1:5000/shop/google/callback`
   - `https://<your-render-service>.onrender.com/shop/google/callback`
4. For local Google sign-in, set `SUPABASE_URL` and `SUPABASE_PUBLISHABLE_KEY` in `.env`. The legacy Supabase anon key is also accepted as `SUPABASE_ANON_KEY`. The publishable/anon key is intended for client identification; **never use a Supabase `service_role` or secret key here**.

The callback uses `PUBLIC_BASE_URL` when set; otherwise it uses the host and HTTPS scheme forwarded by Render. Set it to the exact public origin, such as `https://<your-render-service>.onrender.com`, in production.

## Deploy on Render with Supabase

The repository includes [render.yaml](./render.yaml) for a Render web service. Connect the GitHub repository to Render and deploy the Blueprint. In Render's environment settings, provide:

- `DATABASE_URL`: the Supabase **Session pooler** URI copied from **Connect** (port `5432`; use the username and host exactly as supplied).
- `SUPABASE_URL`: the project URL from Supabase.
- `SUPABASE_PUBLISHABLE_KEY`: the project's publishable key (or set `SUPABASE_ANON_KEY` instead).
- `PUBLIC_BASE_URL`: the final HTTPS Render URL.

Render generates `SECRET_KEY` and sets secure session cookies. The start command applies pending Flask-Migrate migrations before launching Gunicorn. Render's web service is the full Flask app (both pages and server routes); no separate static frontend host is needed. The free Render plan may sleep when idle. Render's filesystem is ephemeral, so maker-uploaded images in `static/uploads` will not survive redeploys; configure durable object storage before relying on uploaded product/profile photos in production.
