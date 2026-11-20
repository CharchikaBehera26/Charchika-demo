import math
import secrets
from functools import wraps

from flask import abort, flash, redirect, request, session, url_for

from .accounts import read_artisan_users
from .data_store import read_data


def csrf_value():
    if "_csrf" not in session:
        session["_csrf"] = secrets.token_urlsafe(32)
    return session["_csrf"]


def verify_csrf():
    supplied = request.form.get("_csrf", "")
    expected = session.get("_csrf", "")
    if not expected or not secrets.compare_digest(supplied, expected):
        abort(400, description="Invalid or expired form token. Please go back and try again.")


def current_artisan_account():
    if session.get("role") != "artisan":
        return None
    user_id = session.get("artisan_user_id")
    return next(
        (user for user in read_artisan_users() if user.get("id") == user_id),
        None,
    )


def artisan_profile(account=None):
    account = account or current_artisan_account()
    if not account:
        return None
    return next(
        (
            artisan for artisan in read_data("artisans")
            if artisan.get("account_id") == account.get("id")
        ),
        None,
    )


def admin_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if session.get("role") != "admin" or not session.get("admin_user"):
            return redirect(url_for("admin.admin_login", next=request.path))
        return view(*args, **kwargs)

    return wrapped


def artisan_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if session.get("role") != "artisan" or not current_artisan_account():
            return redirect(url_for("artisan.artisan_login", next=request.path))
        return view(*args, **kwargs)

    return wrapped


def login_redirect_target(endpoint):
    target = request.args.get("next", "")
    if not target.startswith("/") or target.startswith("//"):
        return url_for(endpoint)
    return target


def next_id(items):
    existing_ids = [
        int(item.get("id", 0))
        for item in items
        if str(item.get("id", "")).isdigit()
    ]
    return max(existing_ids + [0]) + 1


def parse_optional_coordinates(latitude, longitude):
    if not latitude and not longitude:
        return None
    if not latitude or not longitude:
        raise ValueError("Enter both latitude and longitude, or leave both empty.")
    try:
        latitude_value = float(latitude)
        longitude_value = float(longitude)
    except ValueError as exc:
        raise ValueError("Latitude and longitude must be valid numbers.") from exc
    if (
        not -90 <= latitude_value <= 90
        or not -180 <= longitude_value <= 180
        or not math.isfinite(latitude_value)
        or not math.isfinite(longitude_value)
    ):
        raise ValueError("Enter a valid latitude (-90 to 90) and longitude (-180 to 180).")
    return latitude_value, longitude_value
