import base64
import hashlib
import json
import secrets
from decimal import Decimal
from functools import wraps

from flask import (
    Blueprint,
    abort,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from sqlalchemy import select
from werkzeug.security import check_password_hash, generate_password_hash

from ..extensions import db
from ..models import ArtisanAccount, CustomerAccount, CustomerOrder
from ..services.accounts import admin_record
from ..services.data_store import read_data
from ..services.pricing import effective_product_price, product_price
from ..services.security import csrf_value, login_redirect_target, verify_csrf
from ..services.supabase_auth import (
    SupabaseAuthError,
    exchange_google_code,
    google_authorization_url,
    revoke_auth_session,
)


shop_bp = Blueprint("shop", __name__, url_prefix="/shop")


def current_customer_account():
    if session.get("role") != "customer":
        return None
    return db.session.get(CustomerAccount, session.get("customer_user_id"))


def customer_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not current_customer_account():
            return redirect(url_for("shop.customer_login", next=request.path))
        return view(*args, **kwargs)

    return wrapped


def signed_in_customer(account):
    cart = session.get("cart", {})
    session.clear()
    session["role"] = "customer"
    session["customer_user_id"] = account.id
    if isinstance(cart, dict):
        session["cart"] = cart
    csrf_value()


def google_callback_url():
    callback_path = url_for("shop.google_callback")
    base_url = current_app.config.get("PUBLIC_BASE_URL", "").rstrip("/")
    if base_url:
        return f"{base_url}{callback_path}"
    return url_for("shop.google_callback", _external=True)


def format_price(amount):
    return f"₹{amount:,.2f}"


def cart_contents():
    stored = session.get("cart", {})
    if not isinstance(stored, dict):
        stored = {}
    products = {
        int(product["id"]): product
        for product in read_data("products")
        if str(product.get("id", "")).isdigit()
    }
    lines = []
    total = Decimal("0.00")
    for product_id, raw_quantity in stored.items():
        if not str(product_id).isdigit():
            continue
        product = products.get(int(product_id))
        try:
            quantity = int(raw_quantity)
        except (TypeError, ValueError):
            continue
        if not product or not 1 <= quantity <= 99:
            continue
        price = effective_product_price(product)
        line_total = price * quantity if price is not None else None
        if line_total is not None:
            total += line_total
        lines.append({
            "product": product,
            "quantity": quantity,
            "price": price,
            "line_total": line_total,
        })
    return lines, total


@shop_bp.route("/register", methods=["GET", "POST"])
def customer_register():
    if request.method == "POST":
        verify_csrf()
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm = request.form.get("confirm", "")

        if len(name) < 2 or not email or "@" not in email:
            flash("Enter your name and a valid email address.", "error")
        elif existing_account := db.session.scalar(
            select(CustomerAccount).where(CustomerAccount.email == email)
        ):
            if existing_account.supabase_user_id and not existing_account.password_hash:
                flash("This account uses Google. Continue with Google to sign in.", "error")
            else:
                flash("An account with this email already exists. Please sign in.", "error")
        elif len(password) < 10:
            flash("Your password must contain at least 10 characters.", "error")
        elif password != confirm:
            flash("The passwords do not match.", "error")
        else:
            account = CustomerAccount(
                id=secrets.token_urlsafe(16),
                name=name,
                email=email,
                password_hash=generate_password_hash(password),
            )
            db.session.add(account)
            db.session.commit()
            signed_in_customer(account)
            flash("Your customer account has been created.", "success")
            return redirect(login_redirect_target("public.marketplace"))

    return render_template("customer_register.html")


@shop_bp.route("/login", methods=["GET", "POST"])
def customer_login():
    if request.method == "POST":
        verify_csrf()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        account = db.session.scalar(
            select(CustomerAccount).where(CustomerAccount.email == email)
        )
        if (
            account
            and account.password_hash
            and check_password_hash(account.password_hash, password)
        ):
            signed_in_customer(account)
            flash("You are now signed in.", "success")
            return redirect(login_redirect_target("public.marketplace"))
        if account and account.supabase_user_id and not account.password_hash:
            flash("This account uses Google. Continue with Google to sign in.", "error")
        else:
            flash("Incorrect email or password.", "error")

    return render_template("customer_login.html")


@shop_bp.route("/google/login")
def google_login():
    role = request.args.get("role", "customer")
    if role not in {"customer", "artisan", "admin"}:
        abort(400)
    login_endpoint = {
        "customer": "shop.customer_login",
        "artisan": "artisan.artisan_login",
        "admin": "admin.admin_login",
    }[role]
    default_endpoint = {
        "customer": "public.marketplace",
        "artisan": "artisan.artisan_dashboard",
        "admin": "admin.admin_dashboard",
    }[role]
    verifier = secrets.token_urlsafe(64)
    challenge = base64.urlsafe_b64encode(
        hashlib.sha256(verifier.encode("ascii")).digest()
    ).rstrip(b"=").decode("ascii")
    session["supabase_oauth_verifier"] = verifier
    session["supabase_oauth_role"] = role
    session["supabase_oauth_next"] = login_redirect_target(default_endpoint)
    try:
        authorization_url = google_authorization_url(
            google_callback_url(),
            challenge,
        )
    except SupabaseAuthError:
        current_app.logger.exception("Google sign-in is not configured.")
        session.pop("supabase_oauth_verifier", None)
        session.pop("supabase_oauth_role", None)
        session.pop("supabase_oauth_next", None)
        flash("Google sign-in is not configured yet.", "error")
        return redirect(url_for(login_endpoint))
    return redirect(authorization_url)


@shop_bp.route("/google/callback")
def google_callback():
    verifier = session.pop("supabase_oauth_verifier", None)
    role = session.pop("supabase_oauth_role", "customer")
    if role not in {"customer", "artisan", "admin"}:
        role = "customer"
    login_endpoint = {
        "customer": "shop.customer_login",
        "artisan": "artisan.artisan_login",
        "admin": "admin.admin_login",
    }[role]
    next_endpoint = {
        "customer": "public.marketplace",
        "artisan": "artisan.artisan_dashboard",
        "admin": "admin.admin_dashboard",
    }[role]
    next_url = session.pop("supabase_oauth_next", url_for(next_endpoint))
    if request.args.get("error") or not verifier:
        flash("Google sign-in was cancelled or expired. Please try again.", "error")
        return redirect(url_for(login_endpoint))

    auth_code = request.args.get("code", "")
    if not auth_code:
        flash("Google sign-in could not be completed. Please try again.", "error")
        return redirect(url_for(login_endpoint))

    try:
        auth_result = exchange_google_code(auth_code, verifier)
        access_token = auth_result.get("access_token")
        user = auth_result.get("user")
        if not isinstance(access_token, str) or not access_token:
            raise SupabaseAuthError("Supabase Auth did not return an access token.")
        if not isinstance(user, dict):
            revoke_auth_session(access_token)
            raise SupabaseAuthError("Supabase Auth did not return a user.")
        revoke_auth_session(access_token)
    except SupabaseAuthError:
        current_app.logger.exception("Supabase Google sign-in failed.")
        flash("Google sign-in could not be completed. Please try again.", "error")
        return redirect(url_for(login_endpoint))

    email = str(user.get("email", "")).strip().lower()
    user_id = str(user.get("id", "")).strip()
    confirmed = bool(
        user.get("email_confirmed_at")
        or user.get("confirmed_at")
        or user.get("email_verified") is True
        or (
            isinstance(user.get("user_metadata"), dict)
            and user["user_metadata"].get("email_verified") is True
        )
    )
    if not email or not user_id or len(user_id) > 64 or not confirmed:
        flash("Google did not provide a verified email address.", "error")
        return redirect(url_for(login_endpoint))

    if role == "artisan":
        account = db.session.scalar(
            select(ArtisanAccount).where(ArtisanAccount.supabase_user_id == user_id)
        )
        if account is None:
            account = db.session.scalar(
                select(ArtisanAccount).where(ArtisanAccount.email == email)
            )
        if account is None:
            flash(
                "Create your artisan account with this email before using Google sign-in.",
                "error",
            )
            return redirect(url_for("artisan.artisan_login"))
        if account.supabase_user_id not in (None, user_id):
            flash("This email is already linked to another Google account.", "error")
            return redirect(url_for("artisan.artisan_login"))
        account.supabase_user_id = user_id
        db.session.commit()
        session.clear()
        session["role"] = "artisan"
        session["artisan_user_id"] = account.id
        csrf_value()
        flash("You are now signed in with Google.", "success")
        return redirect(next_url)

    if role == "admin":
        allowed_emails = {
            entry.strip().lower()
            for entry in current_app.config.get("GOOGLE_ADMIN_EMAILS", "").split(",")
            if entry.strip()
        }
        if email not in allowed_emails or not admin_record():
            flash("This Google account is not authorized for administrator access.", "error")
            return redirect(url_for("admin.admin_login"))
        session.clear()
        session["role"] = "admin"
        session["admin_user"] = email
        csrf_value()
        flash("You are now signed in with Google.", "success")
        return redirect(next_url)

    account = db.session.scalar(
        select(CustomerAccount).where(
            CustomerAccount.supabase_user_id == user_id
        )
    )
    if account is None:
        account = db.session.scalar(
            select(CustomerAccount).where(CustomerAccount.email == email)
        )
        if account and account.supabase_user_id not in (None, user_id):
            flash("This email is already linked to another Google account.", "error")
            return redirect(url_for("shop.customer_login"))
        if account is None:
            metadata = user.get("user_metadata")
            metadata = metadata if isinstance(metadata, dict) else {}
            name = str(
                metadata.get("full_name")
                or metadata.get("name")
                or email.partition("@")[0]
            ).strip()[:160]
            account = CustomerAccount(
                id=user_id,
                name=name or email,
                email=email,
                password_hash=None,
                supabase_user_id=user_id,
            )
            db.session.add(account)
        else:
            account.supabase_user_id = user_id
        db.session.commit()

    signed_in_customer(account)
    flash("You are now signed in with Google.", "success")
    return redirect(next_url)


@shop_bp.route("/logout", methods=["POST"])
@customer_required
def customer_logout():
    verify_csrf()
    session.clear()
    flash("You have been signed out.", "success")
    return redirect(url_for("public.marketplace"))


@shop_bp.route("/cart")
def cart():
    lines, total = cart_contents()
    return render_template(
        "cart.html",
        lines=lines,
        total=total,
        format_price=format_price,
    )


@shop_bp.route("/cart/add/<int:product_id>", methods=["POST"])
def cart_add(product_id):
    verify_csrf()
    product = next(
        (
            item for item in read_data("products")
            if str(item.get("id", "")) == str(product_id)
        ),
        None,
    )
    if product is None:
        abort(404)
    stored = session.get("cart", {})
    if not isinstance(stored, dict):
        stored = {}
    key = str(product_id)
    is_ajax = request.headers.get("X-Requested-With") == "XMLHttpRequest"
    try:
        requested_quantity = int(request.form.get("quantity", "1"))
        current_quantity = int(stored.get(key, 0))
    except (TypeError, ValueError):
        if is_ajax:
            return {"status": "error", "message": "Enter a valid quantity."}, 400
        flash("Enter a valid quantity.", "error")
        return redirect(request.referrer or url_for("public.marketplace"))
    quantity = current_quantity + requested_quantity
    if not 1 <= quantity <= 99:
        if is_ajax:
            return {"status": "error", "message": "Cart quantities must be between 1 and 99."}, 400
        flash("Cart quantities must be between 1 and 99.", "error")
    else:
        stored[key] = quantity
        session["cart"] = stored
        flash(f"{product.get('name', 'Product')} added to your cart.", "success")

    total_cart_items = sum(
        int(v) for v in stored.values() if str(v).isdigit() and 1 <= int(v) <= 99
    )
    if is_ajax:
        return {
            "status": "success",
            "message": f"{product.get('name', 'Product')} added to your cart.",
            "cart_count": total_cart_items,
            "product_id": product_id,
            "product_name": product.get("name", "Product"),
        }

    return redirect(request.referrer or url_for("public.marketplace"))


@shop_bp.route("/cart/update", methods=["POST"])
def cart_update():
    verify_csrf()
    stored = session.get("cart", {})
    product_id = request.form.get("product_id", "")
    if not isinstance(stored, dict) or product_id not in stored:
        abort(404)
    try:
        quantity = int(request.form.get("quantity", ""))
    except ValueError:
        flash("Enter a valid quantity.", "error")
        return redirect(url_for("shop.cart"))
    if quantity == 0:
        stored.pop(product_id)
    elif 1 <= quantity <= 99:
        stored[product_id] = quantity
    else:
        flash("Cart quantities must be between 1 and 99, or zero to remove.", "error")
    session["cart"] = stored
    return redirect(url_for("shop.cart"))


@shop_bp.route("/checkout", methods=["GET", "POST"])
def checkout():
    account = current_customer_account()
    if account is None:
        return redirect(url_for("shop.customer_login", next=url_for("shop.checkout")))

    lines, total = cart_contents()
    if not lines:
        flash("Your cart is empty.", "error")
        return redirect(url_for("shop.cart"))

    if request.method == "POST":
        verify_csrf()
        customer_name = request.form.get("name", "").strip()
        phone = request.form.get("phone", "").strip()
        address = request.form.get("address", "").strip()
        if not customer_name or not phone or not address:
            flash("Enter your name, phone number and delivery address.", "error")
        elif any(line["price"] is None for line in lines):
            flash("A product in your cart has an invalid price and cannot be ordered.", "error")
        else:
            order_id = secrets.token_urlsafe(16)
            items = [
                {
                    "product_id": line["product"].get("id"),
                    "owner_id": line["product"].get("owner_id"),
                    "name": line["product"]["name"],
                    "artisan": line["product"].get("artisan", ""),
                    "quantity": line["quantity"],
                    "unit_price": format_price(line["price"]),
                    "line_total": format_price(line["line_total"]),
                }
                for line in lines
            ]
            order = CustomerOrder(
                id=order_id,
                customer_id=account.id,
                customer_name=customer_name,
                phone=phone,
                address=address,
                items_json=json.dumps(items),
                total_price=total,
            )
            db.session.add(order)
            db.session.commit()
            session["cart"] = {}
            flash("Your demo order request has been recorded.", "success")
            return redirect(url_for("shop.order_detail", order_id=order_id))

    return render_template(
        "checkout.html",
        account=account,
        lines=lines,
        total=total,
        format_price=format_price,
    )


@shop_bp.route("/orders")
@customer_required
def customer_orders():
    account = current_customer_account()
    orders = db.session.scalars(
        select(CustomerOrder)
        .where(CustomerOrder.customer_id == account.id)
        .order_by(CustomerOrder.created_at.desc())
    ).all()
    return render_template(
        "customer_orders.html",
        orders=orders,
        format_price=format_price,
    )


@shop_bp.route("/orders/<order_id>")
@customer_required
def order_detail(order_id):
    account = current_customer_account()
    order = db.session.scalar(
        select(CustomerOrder).where(
            CustomerOrder.id == order_id,
            CustomerOrder.customer_id == account.id,
        )
    )
    if order is None:
        abort(404)
    return render_template(
        "order_detail.html",
        order=order,
        items=json.loads(order.items_json),
        format_price=format_price,
    )
