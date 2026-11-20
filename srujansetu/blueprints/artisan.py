import secrets

from flask import (
    Blueprint,
    abort,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from werkzeug.security import check_password_hash, generate_password_hash

from ..services.accounts import read_artisan_users, write_artisan_users
from ..services.data_store import read_data, write_data
from ..services.media import save_uploaded_image
from ..services.security import (
    artisan_profile,
    artisan_required,
    csrf_value,
    current_artisan_account,
    login_redirect_target,
    next_id,
    parse_optional_coordinates,
    verify_csrf,
)


artisan_bp = Blueprint("artisan", __name__, url_prefix="/artisan")


@artisan_bp.route("/register", methods=["GET", "POST"])
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
        elif any(user.get("email", "").lower() == email for user in users):
            flash("An account with this email already exists. Please sign in.", "error")
        elif len(password) < 10:
            flash("Your password must contain at least 10 characters.", "error")
        elif password != confirm:
            flash("The passwords do not match.", "error")
        else:
            account_id = secrets.token_urlsafe(16)
            account = {
                "id": account_id,
                "name": name,
                "email": email,
                "password_hash": generate_password_hash(password),
            }
            users.append(account)
            write_artisan_users(users)

            artisans = read_data("artisans")
            artisans.append({
                "id": next_id(artisans),
                "account_id": account_id,
                "name": name,
                "craft": craft,
                "district": district,
                "bio": "",
                "experience": "",
                "emoji": "🧵",
            })
            write_data("artisans", artisans)

            session.clear()
            session["role"] = "artisan"
            session["artisan_user_id"] = account_id
            csrf_value()
            flash("Your artisan account has been created.", "success")
            return redirect(url_for("artisan.artisan_dashboard"))

    return render_template("artisan_register.html")


@artisan_bp.route("/login", methods=["GET", "POST"])
def artisan_login():
    if request.method == "POST":
        verify_csrf()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        account = next(
            (
                user for user in read_artisan_users()
                if user.get("email", "").lower() == email
            ),
            None,
        )
        if account and check_password_hash(account.get("password_hash", ""), password):
            session.clear()
            session["role"] = "artisan"
            session["artisan_user_id"] = account["id"]
            csrf_value()
            flash("You are now signed in.", "success")
            return redirect(
                login_redirect_target("artisan.artisan_dashboard")
            )
        flash("Incorrect email or password.", "error")

    return render_template("artisan_login.html")


@artisan_bp.route("/logout", methods=["POST"])
@artisan_required
def artisan_logout():
    verify_csrf()
    session.clear()
    flash("You have been signed out.", "success")
    return redirect(url_for("artisan.artisan_login"))


@artisan_bp.route("/dashboard")
@artisan_required
def artisan_dashboard():
    account = current_artisan_account()
    profile = artisan_profile(account)
    products = [
        product for product in read_data("products")
        if product.get("owner_id") == account.get("id")
    ]
    return render_template(
        "artisan_dashboard.html",
        account=account,
        profile=profile,
        products=products,
    )


@artisan_bp.route("/profile", methods=["GET", "POST"])
@artisan_required
def artisan_profile_edit():
    account = current_artisan_account()
    artisans = read_data("artisans")
    profile = next(
        (
            artisan for artisan in artisans
            if artisan.get("account_id") == account.get("id")
        ),
        None,
    )
    if profile is None:
        profile = {"id": next_id(artisans), "account_id": account["id"]}
        artisans.append(profile)

    if request.method == "POST":
        verify_csrf()
        updated = dict(profile)
        for key in ("name", "craft", "district", "experience", "bio"):
            updated[key] = request.form.get(key, "").strip()
        latitude = request.form.get("latitude", "").strip()
        longitude = request.form.get("longitude", "").strip()
        updated["latitude"] = latitude
        updated["longitude"] = longitude

        if not updated.get("name") or not updated.get("craft") or not updated.get("district"):
            flash("Name, craft and district are required.", "error")
        else:
            try:
                coordinates = parse_optional_coordinates(latitude, longitude)
            except ValueError as exc:
                flash(str(exc), "error")
                return render_template("artisan_profile.html", profile=updated)

            if coordinates is None:
                updated.pop("latitude", None)
                updated.pop("longitude", None)
            else:
                updated["latitude"], updated["longitude"] = coordinates

            try:
                uploaded = save_uploaded_image(request.files.get("image_file"))
            except ValueError as exc:
                flash(str(exc), "error")
                return render_template("artisan_profile.html", profile=updated)
            if uploaded:
                updated["image"] = uploaded

            artisans = [
                updated if item.get("account_id") == account.get("id") else item
                for item in artisans
            ]
            write_data("artisans", artisans)
            account["name"] = updated["name"]
            users = [
                account if user.get("id") == account.get("id") else user
                for user in read_artisan_users()
            ]
            write_artisan_users(users)
            flash("Your artisan profile has been updated.", "success")
            return redirect(url_for("artisan.artisan_dashboard"))
        profile = updated

    return render_template("artisan_profile.html", profile=profile)


@artisan_bp.route("/products")
@artisan_required
def artisan_products():
    account = current_artisan_account()
    products = [
        product for product in read_data("products")
        if product.get("owner_id") == account.get("id")
    ]
    return render_template("artisan_products.html", products=products)


@artisan_bp.route("/products/new", methods=["GET", "POST"])
@artisan_required
def artisan_product_new():
    account = current_artisan_account()
    product = {}
    if request.method == "POST":
        verify_csrf()
        product = {
            key: request.form.get(key, "").strip()
            for key in ("name", "craft", "price", "description")
        }
        if not product["name"] or not product["price"]:
            flash("Product name and price are required.", "error")
        else:
            try:
                uploaded = save_uploaded_image(request.files.get("image_file"))
            except ValueError as exc:
                flash(str(exc), "error")
                return render_template(
                    "artisan_product_form.html",
                    product=product,
                    mode="Add",
                )
            if uploaded:
                product["image"] = uploaded

            profile = artisan_profile(account) or {}
            product.update({
                "id": next_id(read_data("products")),
                "owner_id": account["id"],
                "artisan": profile.get("name", account.get("name", "")),
                "district": profile.get("district", ""),
            })
            products = read_data("products")
            products.append(product)
            write_data("products", products)
            flash("Your product has been added to the marketplace.", "success")
            return redirect(url_for("artisan.artisan_products"))

    return render_template(
        "artisan_product_form.html",
        product=product,
        mode="Add",
    )


@artisan_bp.route("/products/<int:product_id>/edit", methods=["GET", "POST"])
@artisan_required
def artisan_product_edit(product_id):
    account = current_artisan_account()
    products = read_data("products")
    product = next(
        (
            item for item in products
            if int(item.get("id", -1)) == product_id
            and item.get("owner_id") == account.get("id")
        ),
        None,
    )
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
                return render_template(
                    "artisan_product_form.html",
                    product=updated,
                    mode="Edit",
                )
            if uploaded:
                updated["image"] = uploaded

            profile = artisan_profile(account) or {}
            updated["artisan"] = profile.get("name", account.get("name", ""))
            updated["district"] = profile.get("district", "")
            write_data(
                "products",
                [
                    updated if item.get("id") == product_id else item
                    for item in products
                ],
            )
            flash("Your product has been updated.", "success")
            return redirect(url_for("artisan.artisan_products"))
        product = updated

    return render_template(
        "artisan_product_form.html",
        product=product,
        mode="Edit",
    )


@artisan_bp.route("/products/<int:product_id>/delete", methods=["POST"])
@artisan_required
def artisan_product_delete(product_id):
    verify_csrf()
    account = current_artisan_account()
    products = read_data("products")
    owned = [
        product for product in products
        if int(product.get("id", -1)) == product_id
        and product.get("owner_id") == account.get("id")
    ]
    if not owned:
        abort(404)
    write_data(
        "products",
        [
            product for product in products
            if not (
                int(product.get("id", -1)) == product_id
                and product.get("owner_id") == account.get("id")
            )
        ],
    )
    flash("Your product has been deleted.", "success")
    return redirect(url_for("artisan.artisan_products"))
