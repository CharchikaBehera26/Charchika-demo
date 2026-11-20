from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session, abort
from pathlib import Path
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from functools import wraps
import os, secrets, json, threading
from datetime import datetime

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-only-change-this-secret-before-deployment")
app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024  # 5 MB upload limit
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
UPLOAD_DIR = BASE_DIR / "static" / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
LOCK = threading.Lock()

DATA_FILES = {
    "artisans": DATA_DIR / "artisans.json",
    "crafts": DATA_DIR / "crafts.json",
    "products": DATA_DIR / "products.json",
    "schemes": DATA_DIR / "schemes.json",
    "stories": DATA_DIR / "stories.json",
    "community": DATA_DIR / "community.json",
}

def read_data(kind):
    path = DATA_FILES[kind]
    with LOCK:
        if not path.exists():
            return []
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return []

def write_data(kind, items):
    path = DATA_FILES[kind]
    with LOCK:
        temp = path.with_suffix(".tmp")
        temp.write_text(json.dumps(items, ensure_ascii=False, indent=2), encoding="utf-8")
        temp.replace(path)



ADMIN_FILE = DATA_DIR / "admin.json"
ARTISAN_USERS_FILE = DATA_DIR / "artisan_users.json"
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}
ADMIN_SECTIONS = {
    "artisans": {
        "title": "Artisans", "singular": "Artisan",
        "fields": [("name","Name","text",True),("craft","Craft","text",True),
                   ("district","District","text",True),("bio","Biography","textarea",False),
                   ("experience","Experience","text",False),("emoji","Icon / Emoji","text",False),
                   ("image","Image URL or uploaded image","text",False)],
        "image": True
    },
    "crafts": {
        "title": "Crafts", "singular": "Craft",
        "fields": [("name","Craft name","text",True),("region","Region","text",True),
                   ("description","Description","textarea",False),("emoji","Icon / Emoji","text",False),
                   ("tone","Card colour theme","text",False)],
        "image": True
    },
    "products": {
        "title": "Products", "singular": "Product",
        "fields": [("name","Product name","text",True),("craft","Craft type","text",False),
                   ("price","Price","text",True),("artisan","Artisan / SHG","text",False),
                   ("district","District","text",False),("description","Description","textarea",False),
                   ("emoji","Icon / Emoji","text",False)],
        "image": True
    },
    "schemes": {
        "title": "Schemes", "singular": "Scheme",
        "fields": [("name","Scheme name","text",True),("audience","Intended audience","text",False),
                   ("description","Description","textarea",False),("note","Important note","textarea",False)],
        "image": False
    },
    "community": {
        "title": "Community posts", "singular": "Community post",
        "fields": [("name","Author name","text",True),("message","Message","textarea",True),
                   ("date","Date","text",False)],
        "image": False
    }
}

def admin_record():
    if not ADMIN_FILE.exists():
        return None
    try:
        return json.loads(ADMIN_FILE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None

def csrf_value():
    if "_csrf" not in session:
        session["_csrf"] = secrets.token_urlsafe(32)
    return session["_csrf"]

@app.context_processor
def inject_admin_helpers():
    return {
        "csrf_token": csrf_value,
        "admin_logged_in": session.get("role") == "admin" and bool(session.get("admin_user")),
        "artisan_logged_in": session.get("role") == "artisan" and bool(session.get("artisan_user_id")),
        "current_artisan": current_artisan_account(),
    }

def read_artisan_users():
    if not ARTISAN_USERS_FILE.exists():
        return []
    try:
        return json.loads(ARTISAN_USERS_FILE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []

def write_artisan_users(users):
    DATA_DIR.mkdir(exist_ok=True)
    temp = ARTISAN_USERS_FILE.with_suffix(".tmp")
    temp.write_text(json.dumps(users, ensure_ascii=False, indent=2), encoding="utf-8")
    temp.replace(ARTISAN_USERS_FILE)

def current_artisan_account():
    if session.get("role") != "artisan":
        return None
    uid = session.get("artisan_user_id")
    return next((u for u in read_artisan_users() if u.get("id") == uid), None)

def artisan_profile(account=None):
    account = account or current_artisan_account()
    if not account:
        return None
    return next((a for a in read_data("artisans") if a.get("account_id") == account.get("id")), None)

def verify_csrf():
    supplied = request.form.get("_csrf", "")
    expected = session.get("_csrf", "")
    if not expected or not secrets.compare_digest(supplied, expected):
        abort(400, description="Invalid or expired form token. Please go back and try again.")

def admin_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if session.get("role") != "admin" or not session.get("admin_user"):
            return redirect(url_for("admin_login", next=request.path))
        return view(*args, **kwargs)
    return wrapped

def artisan_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if session.get("role") != "artisan" or not current_artisan_account():
            return redirect(url_for("artisan_login", next=request.path))
        return view(*args, **kwargs)
    return wrapped

def login_redirect_target(endpoint):
    target = request.args.get("next", "")
    if not target.startswith("/") or target.startswith("//"):
        return url_for(endpoint)
    return target

def next_id(items):
    return max([int(item.get("id", 0)) for item in items if str(item.get("id", "")).isdigit()] + [0]) + 1

def allowed_image(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

def save_uploaded_image(file):
    if not file or not file.filename:
        return None
    if not allowed_image(file.filename):
        raise ValueError("Please upload a PNG, JPG, JPEG, GIF or WEBP image.")
    original = secure_filename(file.filename)
    ext = original.rsplit(".", 1)[1].lower()
    filename = f"{secrets.token_hex(12)}.{ext}"
    file.save(UPLOAD_DIR / filename)
    return "/static/uploads/" + filename

def admin_counts():
    return {kind: len(read_data(kind)) for kind in ADMIN_SECTIONS}

@app.route("/admin")
def admin_index():
    if not admin_record():
        return redirect(url_for("admin_setup"))
    if session.get("admin_user"):
        return redirect(url_for("admin_dashboard"))
    return redirect(url_for("admin_login"))

@app.route("/admin/setup", methods=["GET", "POST"])
def admin_setup():
    if admin_record():
        return redirect(url_for("admin_login"))
    if request.method == "POST":
        verify_csrf()
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        confirm = request.form.get("confirm", "")
        if len(username) < 3 or len(password) < 10:
            flash("Use a username of at least 3 characters and a password of at least 10 characters.", "error")
        elif password != confirm:
            flash("The passwords do not match.", "error")
        else:
            DATA_DIR.mkdir(exist_ok=True)
            ADMIN_FILE.write_text(json.dumps({
                "username": username,
                "password_hash": generate_password_hash(password)
            }, indent=2), encoding="utf-8")
            session.clear()
            session["role"] = "admin"
            session["admin_user"] = username
            csrf_value()
            flash("Administrator account created. Welcome to your dashboard.", "success")
            return redirect(url_for("admin_dashboard"))
    return render_template("admin_setup.html")

@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if not admin_record():
        return redirect(url_for("admin_setup"))
    if request.method == "POST":
        verify_csrf()
        record = admin_record()
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        if record and secrets.compare_digest(username, record.get("username", "")) and check_password_hash(record.get("password_hash", ""), password):
            session.clear()
            session["role"] = "admin"
            session["admin_user"] = username
            csrf_value()
            flash("You are now signed in.", "success")
            return redirect(login_redirect_target("admin_dashboard"))
        flash("Incorrect username or password.", "error")
    return render_template("admin_login.html")

@app.route("/admin/logout", methods=["POST"])
@admin_required
def admin_logout():
    verify_csrf()
    session.clear()
    flash("You have been signed out.", "success")
    return redirect(url_for("admin_login"))

@app.route("/admin/dashboard")
@admin_required
def admin_dashboard():
    return render_template("admin_dashboard.html", counts=admin_counts(), sections=ADMIN_SECTIONS)

@app.route("/admin/<kind>")
@admin_required
def admin_manage(kind):
    if kind not in ADMIN_SECTIONS:
        abort(404)
    items = read_data(kind)
    return render_template("admin_manage.html", kind=kind, config=ADMIN_SECTIONS[kind], items=items)

@app.route("/admin/<kind>/new", methods=["GET", "POST"])
@admin_required
def admin_new(kind):
    if kind not in ADMIN_SECTIONS:
        abort(404)
    config = ADMIN_SECTIONS[kind]
    if request.method == "POST":
        verify_csrf()
        item = {"id": next_id(read_data(kind))}
        for key, _label, _type, _required in config["fields"]:
            item[key] = request.form.get(key, "").strip()
        if kind == "community" and not item.get("date"):
            item["date"] = datetime.now().strftime("%d %b %Y")
        try:
            uploaded = save_uploaded_image(request.files.get("image_file")) if config["image"] else None
            if uploaded:
                item["image"] = uploaded
        except ValueError as exc:
            flash(str(exc), "error")
            return render_template("admin_form.html", kind=kind, config=config, item=item, mode="Add")
        if any(required and not item.get(key) for key, _label, _type, required in config["fields"]):
            flash("Please complete all required fields.", "error")
            return render_template("admin_form.html", kind=kind, config=config, item=item, mode="Add")
        items = read_data(kind)
        items.append(item)
        write_data(kind, items)
        flash(f'{config["singular"]} added successfully.', "success")
        return redirect(url_for("admin_manage", kind=kind))
    return render_template("admin_form.html", kind=kind, config=config, item={}, mode="Add")

@app.route("/admin/<kind>/<int:item_id>/edit", methods=["GET", "POST"])
@admin_required
def admin_edit(kind, item_id):
    if kind not in ADMIN_SECTIONS:
        abort(404)
    config = ADMIN_SECTIONS[kind]
    items = read_data(kind)
    item = next((x for x in items if int(x.get("id", -1)) == item_id), None)
    if item is None:
        abort(404)
    if request.method == "POST":
        verify_csrf()
        updated = dict(item)
        for key, _label, _type, _required in config["fields"]:
            updated[key] = request.form.get(key, "").strip()
        try:
            uploaded = save_uploaded_image(request.files.get("image_file")) if config["image"] else None
            if uploaded:
                updated["image"] = uploaded
        except ValueError as exc:
            flash(str(exc), "error")
            return render_template("admin_form.html", kind=kind, config=config, item=updated, mode="Edit")
        if any(required and not updated.get(key) for key, _label, _type, required in config["fields"]):
            flash("Please complete all required fields.", "error")
            return render_template("admin_form.html", kind=kind, config=config, item=updated, mode="Edit")
        items = [updated if int(x.get("id", -1)) == item_id else x for x in items]
        write_data(kind, items)
        flash(f'{config["singular"]} updated successfully.', "success")
        return redirect(url_for("admin_manage", kind=kind))
    return render_template("admin_form.html", kind=kind, config=config, item=item, mode="Edit")

@app.route("/admin/<kind>/<int:item_id>/delete", methods=["POST"])
@admin_required
def admin_delete(kind, item_id):
    if kind not in ADMIN_SECTIONS:
        abort(404)
    verify_csrf()
    items = read_data(kind)
    kept = [x for x in items if int(x.get("id", -1)) != item_id]
    if len(kept) == len(items):
        abort(404)
    write_data(kind, kept)
    flash(f'{ADMIN_SECTIONS[kind]["singular"]} deleted.', "success")
    return redirect(url_for("admin_manage", kind=kind))



# Artisan self-service portal routes
@app.route("/artisan/register", methods=["GET", "POST"])
def artisan_register():
    if request.method == "POST":
        verify_csrf()
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        craft = request.form.get("craft", "").strip()
        district = request.form.get("district", "").strip()
        password = request.form.get("password", "")
        confirm = request.form.get("confirm", "")
        users = read_artisan_users()
        if not name or not email or not craft or not district:
            flash("Please complete all required fields.", "error")
        elif any(u.get("email", "").lower() == email for u in users):
            flash("An account with this email already exists. Please sign in.", "error")
        elif len(password) < 10:
            flash("Your password must contain at least 10 characters.", "error")
        elif password != confirm:
            flash("The passwords do not match.", "error")
        else:
            account_id = secrets.token_urlsafe(16)
            account = {"id": account_id, "name": name, "email": email,
                       "password_hash": generate_password_hash(password)}
            users.append(account)
            write_artisan_users(users)
            artisans = read_data("artisans")
            artisans.append({"id": next_id(artisans), "account_id": account_id,
                             "name": name, "craft": craft, "district": district,
                             "bio": "", "experience": "", "emoji": "🧵"})
            write_data("artisans", artisans)
            session.clear()
            session["role"] = "artisan"
            session["artisan_user_id"] = account_id
            csrf_value()
            flash("Your artisan account has been created.", "success")
            return redirect(url_for("artisan_dashboard"))
    return render_template("artisan_register.html")

@app.route("/artisan/login", methods=["GET", "POST"])
def artisan_login():
    if request.method == "POST":
        verify_csrf()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        account = next((u for u in read_artisan_users() if u.get("email", "").lower() == email), None)
        if account and check_password_hash(account.get("password_hash", ""), password):
            session.clear()
            session["role"] = "artisan"
            session["artisan_user_id"] = account["id"]
            csrf_value()
            flash("You are now signed in.", "success")
            return redirect(login_redirect_target("artisan_dashboard"))
        flash("Incorrect email or password.", "error")
    return render_template("artisan_login.html")

@app.route("/artisan/logout", methods=["POST"])
@artisan_required
def artisan_logout():
    verify_csrf()
    session.clear()
    flash("You have been signed out.", "success")
    return redirect(url_for("artisan_login"))

@app.route("/artisan/dashboard")
@artisan_required
def artisan_dashboard():
    account = current_artisan_account()
    profile = artisan_profile(account)
    products = [p for p in read_data("products") if p.get("owner_id") == account.get("id")]
    return render_template("artisan_dashboard.html", account=account, profile=profile, products=products)

@app.route("/artisan/profile", methods=["GET", "POST"])
@artisan_required
def artisan_profile_edit():
    account = current_artisan_account()
    artisans = read_data("artisans")
    profile = next((a for a in artisans if a.get("account_id") == account.get("id")), None)
    if profile is None:
        profile = {"id": next_id(artisans), "account_id": account["id"]}
        artisans.append(profile)
    if request.method == "POST":
        verify_csrf()
        updated = dict(profile)
        for key in ("name", "craft", "district", "experience", "bio"):
            updated[key] = request.form.get(key, "").strip()
        if not updated.get("name") or not updated.get("craft") or not updated.get("district"):
            flash("Name, craft and district are required.", "error")
        else:
            try:
                uploaded = save_uploaded_image(request.files.get("image_file"))
            except ValueError as exc:
                flash(str(exc), "error")
                return render_template("artisan_profile.html", profile=updated)
            if uploaded:
                updated["image"] = uploaded
            artisans = [updated if a.get("account_id") == account.get("id") else a for a in artisans]
            write_data("artisans", artisans)
            account["name"] = updated["name"]
            users = [account if u.get("id") == account.get("id") else u for u in read_artisan_users()]
            write_artisan_users(users)
            flash("Your artisan profile has been updated.", "success")
            return redirect(url_for("artisan_dashboard"))
        profile = updated
    return render_template("artisan_profile.html", profile=profile)

@app.route("/artisan/products")
@artisan_required
def artisan_products():
    account = current_artisan_account()
    products = [p for p in read_data("products") if p.get("owner_id") == account.get("id")]
    return render_template("artisan_products.html", products=products)

@app.route("/artisan/products/new", methods=["GET", "POST"])
@artisan_required
def artisan_product_new():
    account = current_artisan_account()
    product = {}
    if request.method == "POST":
        verify_csrf()
        product = {key: request.form.get(key, "").strip() for key in ("name", "craft", "price", "description")}
        if not product["name"] or not product["price"]:
            flash("Product name and price are required.", "error")
        else:
            try:
                uploaded = save_uploaded_image(request.files.get("image_file"))
            except ValueError as exc:
                flash(str(exc), "error")
                return render_template("artisan_product_form.html", product=product, mode="Add")
            if uploaded:
                product["image"] = uploaded
            profile = artisan_profile(account) or {}
            product.update({"id": next_id(read_data("products")), "owner_id": account["id"],
                            "artisan": profile.get("name", account.get("name", "")),
                            "district": profile.get("district", "")})
            products = read_data("products")
            products.append(product)
            write_data("products", products)
            flash("Your product has been added to the marketplace.", "success")
            return redirect(url_for("artisan_products"))
    return render_template("artisan_product_form.html", product=product, mode="Add")

@app.route("/artisan/products/<int:product_id>/edit", methods=["GET", "POST"])
@artisan_required
def artisan_product_edit(product_id):
    account = current_artisan_account()
    products = read_data("products")
    product = next((p for p in products if int(p.get("id", -1)) == product_id and p.get("owner_id") == account.get("id")), None)
    if product is None:
        abort(404)
    if request.method == "POST":
        verify_csrf()
        updated = dict(product)
        for key in ("name", "craft", "price", "description"):
            updated[key] = request.form.get(key, "").strip()
        if not updated.get("name") or not updated.get("price"):
            flash("Product name and price are required.", "error")
        else:
            try:
                uploaded = save_uploaded_image(request.files.get("image_file"))
            except ValueError as exc:
                flash(str(exc), "error")
                return render_template("artisan_product_form.html", product=updated, mode="Edit")
            if uploaded:
                updated["image"] = uploaded
            profile = artisan_profile(account) or {}
            updated["artisan"] = profile.get("name", account.get("name", ""))
            updated["district"] = profile.get("district", "")
            write_data("products", [updated if p.get("id") == product_id else p for p in products])
            flash("Your product has been updated.", "success")
            return redirect(url_for("artisan_products"))
        product = updated
    return render_template("artisan_product_form.html", product=product, mode="Edit")

@app.route("/artisan/products/<int:product_id>/delete", methods=["POST"])
@artisan_required
def artisan_product_delete(product_id):
    verify_csrf()
    account = current_artisan_account()
    products = read_data("products")
    owned = [p for p in products if int(p.get("id", -1)) == product_id and p.get("owner_id") == account.get("id")]
    if not owned:
        abort(404)
    write_data("products", [p for p in products if not (int(p.get("id", -1)) == product_id and p.get("owner_id") == account.get("id"))])
    flash("Your product has been deleted.", "success")
    return redirect(url_for("artisan_products"))

@app.context_processor
def inject_globals():
    return {"current_year": datetime.now().year}

@app.route("/")
def home():
    artisans = read_data("artisans")
    crafts = read_data("crafts")
    products = read_data("products")
    return render_template("index.html", artisans=artisans[:3], crafts=crafts[:5],
                           artisan_count=len(artisans), craft_count=len(crafts),
                           product_count=len(products))

@app.route("/crafts")
def crafts():
    q = request.args.get("q", "").strip().lower()
    items = read_data("crafts")
    if q:
        items = [x for x in items if q in (x.get("name","") + " " + x.get("region","") + " " + x.get("description","")).lower()]
    return render_template("crafts.html", crafts=items, query=q)

@app.route("/artisans")
def artisans():
    q = request.args.get("q", "").strip().lower()
    region = request.args.get("region", "").strip().lower()
    items = read_data("artisans")
    if q:
        items = [x for x in items if q in (x.get("name","") + " " + x.get("craft","") + " " + x.get("district","")).lower()]
    if region:
        items = [x for x in items if region in x.get("district","").lower()]
    regions = sorted({x.get("district","") for x in read_data("artisans") if x.get("district")})
    return render_template("artisans.html", artisans=items, query=q, region=region, regions=regions)

@app.route("/marketplace")
def marketplace():
    return render_template("marketplace.html", products=read_data("products"))


@app.route("/stories")
def stories():
    return render_template("stories.html", stories=read_data("stories"))

@app.route("/schemes")
def schemes():
    q = request.args.get("q", "").strip().lower()
    items = read_data("schemes")
    if q:
        items = [x for x in items if q in (x.get("name","") + " " + x.get("audience","") + " " + x.get("description","")).lower()]
    return render_template("schemes.html", schemes=items, query=q)

@app.route("/planner", methods=["GET", "POST"])
def planner():
    districts = ["Puri", "Cuttack", "Sambalpur", "Bhubaneswar", "Raghurajpur", "Pipili"]
    selected = request.form.get("district", "Puri") if request.method == "POST" else "Puri"
    matches = [a for a in read_data("artisans") if selected.lower() in a.get("district","").lower()]
    return render_template("planner.html", districts=districts, selected=selected, artisans=matches)

@app.route("/assistant", methods=["GET", "POST"])
def assistant():
    answer = None
    if request.method == "POST":
        message = request.form.get("message", "").strip().lower()
        answers = [
            (["pattachitra", "painting"], "Pattachitra is a traditional cloth-based scroll painting associated with Odisha, especially the Raghurajpur area."),
            (["sambalpuri", "ikat"], "Sambalpuri textiles are known for their ikat weaving tradition. Explore the craft collection to learn more."),
            (["artisan", "nearby", "find"], "Visit Find Artisans to browse artisan profiles by name, craft and district."),
            (["scheme", "government", "support"], "Open Scheme Finder to browse the sample support programmes listed in this educational demo."),
            (["market", "product", "buy"], "Visit the SHG Marketplace to explore sample products or add a demonstration listing."),
            (["hello", "hi", "namaskar"], "Namaskar! I am Srujan AI, your digital saathi. Ask me about Odisha crafts, artisans or the marketplace.")
        ]
        answer = next((a for keys, a in answers if any(k in message for k in keys)),
                      "I can help with Odisha crafts, artisan discovery, marketplace listings and scheme information. Try asking about Pattachitra, Sambalpuri or finding artisans.")
    return render_template("assistant.html", answer=answer)

@app.route("/business")
def business():
    tips = [
        "Use clear product photos with a plain background and natural light.",
        "Tell the story behind the craft, materials and artisan community.",
        "List dimensions, care instructions and shipping details clearly.",
        "Keep prices, stock information and contact details up to date."
    ]
    return render_template("business.html", tips=tips)

@app.route("/community", methods=["GET", "POST"])
def community():
    if request.method == "POST":
        entries = read_data("community")
        name = request.form.get("name", "").strip()
        message = request.form.get("message", "").strip()
        if name and message:
            entries.insert(0, {"id": next_id(entries), "name": name, "message": message, "date": datetime.now().strftime("%d %b %Y")})
            write_data("community", entries[:100])
            flash("Your community note has been added.", "success")
        else:
            flash("Please add your name and a message.", "error")
        return redirect(url_for("community"))
    return render_template("community.html", entries=read_data("community"))

@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/api/search")
def api_search():
    q = request.args.get("q", "").strip().lower()
    results = []
    for kind in ("artisans", "crafts", "products"):
        for item in read_data(kind):
            haystack = " ".join(str(v) for v in item.values()).lower()
            if q and q in haystack:
                results.append({"type": kind[:-1], "name": item.get("name", "Untitled"), "url": {
                    "artisans": url_for("artisans"), "crafts": url_for("crafts"),
                    "products": url_for("marketplace")
                }[kind]})
    return jsonify(results[:8])

@app.errorhandler(404)
def not_found(_error):
    return render_template("404.html"), 404

if __name__ == "__main__":
    DATA_DIR.mkdir(exist_ok=True)
    app.run(debug=True)
