# SrujanSetu AI — Odisha Crafts Educational Website

A responsive Flask website inspired by the supplied SrujanSetu screenshots. It uses JSON files for simple local data storage.

## Features
- Home dashboard and impact counters
- Explore Crafts with search
- Find Artisans with search and district filter
- SHG Marketplace with demonstration product submission
- Craft Stories
- Scheme Finder (sample educational information)
- Odisha Craft Explorer / visit planner
- Rule-based Srujan AI FAQ assistant
- Business Copilot tips
- Community message board
- About page
- JSON file storage with atomic writes

## Requirements
- Python 3.9+
- pip

## Run locally

### Windows
```powershell
cd SrujanSetu
py -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

### macOS / Linux
```bash
cd SrujanSetu
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

Open http://127.0.0.1:5000

## Data management
Edit the JSON files inside `data/`:
- `artisans.json`
- `crafts.json`
- `products.json`
- `schemes.json`
- `stories.json`
- `community.json`

Keep valid JSON syntax. You can add or edit sample records with a text editor. Marketplace submissions and community messages are written to the corresponding JSON files.

## Important educational-project notes
- All bundled people, profiles, prices, counters and programme descriptions are demonstration content. Replace or verify them before public use.
- The scheme page explicitly labels its entries as illustrative, not verified live government schemes.
- The assistant is a simple keyword-based FAQ demo, not a connected generative AI service.
- This starter has no user authentication, role-based admin panel, payment gateway, image upload, or production-grade security.
- Before public deployment: set a strong `SECRET_KEY` using an environment variable, disable Flask debug mode, add authentication and CSRF protection, validate uploads, add backups, and use a production WSGI server.
- Do not store passwords or other sensitive personal information in plain JSON files.
- Some artisan card image URLs are remote Unsplash demo images and require internet access. Replace them with licensed local images if preferred.

## Project structure
```text
SrujanSetu/
├── app.py
├── requirements.txt
├── README.md
├── data/
│   ├── artisans.json
│   ├── crafts.json
│   ├── products.json
│   ├── schemes.json
│   ├── stories.json
│   └── community.json
├── static/
│   ├── css/style.css
│   └── js/app.js
└── templates/
    ├── base.html
    ├── index.html
    ├── crafts.html
    ├── artisans.html
    ├── marketplace.html
    ├── stories.html
    ├── schemes.html
    ├── planner.html
    ├── assistant.html
    ├── business.html
    ├── community.html
    ├── about.html
    └── 404.html
```


## Admin dashboard

1. Start the app with `python app.py`.
2. Open `http://127.0.0.1:5000/admin`.
3. On first run, create an administrator username and password. Passwords are stored as Werkzeug password hashes in `data/admin.json`.
4. Sign in to manage Artisans, Crafts, Products, Schemes and Community posts.
5. Use Add, Edit and Delete actions. Image-enabled sections accept PNG, JPG, JPEG, GIF and WEBP files up to 5 MB. Uploaded files are saved in `static/uploads/`; their paths are stored in the JSON record.

### Admin security notes
- The admin forms include session-based CSRF tokens, login-protected management routes, hashed passwords, secure upload filenames, extension checks and a 5 MB request limit.
- This is a learning-project security baseline, not a production security audit. Before internet deployment, set a long random `SECRET_KEY` environment variable, run behind HTTPS with a production WSGI server, add login rate limiting and account recovery, validate image file contents (not only extensions), configure secure cookie flags, and keep off-site backups.
- Protect the `data/` and `static/uploads/` directories from public write access. The JSON store is intended for a small single-process educational demo; use a database for concurrent or high-volume use.


## Artisan accounts and role permissions

- Admin: uses `/admin`, can manage all artisan profiles, crafts, products, schemes and community records.
- Artisan: registers at `/artisan/register` and signs in at `/artisan/login`. Registration creates the artisan's public profile and a separate account record.
- An artisan can update only the profile linked to their account and can create, edit or delete only products carrying their `owner_id`.
- The public marketplace is read-only. Product submissions now require an authenticated artisan account.
- Artisan account hashes are stored in `data/artisan_users.json`. Public profile data stays in `data/artisans.json`; product ownership is stored as `owner_id` in `data/products.json`.
- Existing sample products remain visible and remain manageable by the Admin. They are not automatically assigned to any artisan.

The role checks are enforced server-side. Hiding buttons in the interface is not used as the security boundary.
