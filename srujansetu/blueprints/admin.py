import secrets
from datetime import datetime

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

from ..constants import ADMIN_SECTIONS
from ..services.accounts import admin_record, save_admin_record
from ..services.data_store import read_data, write_data
from ..services.media import save_uploaded_image
from ..services.security import (
    admin_required,
    csrf_value,
    login_redirect_target,
    next_id,
    verify_csrf,
)


admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


def admin_counts():
    return {
        collection: len(read_data(collection))
        for collection in ADMIN_SECTIONS
    }


@admin_bp.route("", strict_slashes=False)
def admin_index():
    if not admin_record():
        return redirect(url_for("admin.admin_setup"))
    if session.get("admin_user"):
        return redirect(url_for("admin.admin_dashboard"))
    return redirect(url_for("admin.admin_login"))


@admin_bp.route("/setup", methods=["GET", "POST"])
def admin_setup():
    if admin_record():
        return redirect(url_for("admin.admin_login"))

    if request.method == "POST":
        verify_csrf()
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        confirm = request.form.get("confirm", "")

        if len(username) < 3 or len(password) < 10:
            flash(
                "Use a username of at least 3 characters and a password of at least 10 characters.",
                "error",
            )
        elif password != confirm:
            flash("The passwords do not match.", "error")
        else:
            save_admin_record({
                "username": username,
                "password_hash": generate_password_hash(password),
            })
            session.clear()
            session["role"] = "admin"
            session["admin_user"] = username
            csrf_value()
            flash("Administrator account created. Welcome to your dashboard.", "success")
            return redirect(url_for("admin.admin_dashboard"))

    return render_template("admin_setup.html")


@admin_bp.route("/login", methods=["GET", "POST"])
def admin_login():
    if not admin_record():
        return redirect(url_for("admin.admin_setup"))

    if request.method == "POST":
        verify_csrf()
        record = admin_record()
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        if (
            record
            and secrets.compare_digest(username, record.get("username", ""))
            and check_password_hash(record.get("password_hash", ""), password)
        ):
            session.clear()
            session["role"] = "admin"
            session["admin_user"] = username
            csrf_value()
            flash("You are now signed in.", "success")
            return redirect(
                login_redirect_target("admin.admin_dashboard")
            )
        flash("Incorrect username or password.", "error")

    return render_template("admin_login.html")


@admin_bp.route("/logout", methods=["POST"])
@admin_required
def admin_logout():
    verify_csrf()
    session.clear()
    flash("You have been signed out.", "success")
    return redirect(url_for("admin.admin_login"))


@admin_bp.route("/dashboard")
@admin_required
def admin_dashboard():
    return render_template(
        "admin_dashboard.html",
        counts=admin_counts(),
        sections=ADMIN_SECTIONS,
    )


@admin_bp.route("/<kind>")
@admin_required
def admin_manage(kind):
    if kind not in ADMIN_SECTIONS:
        abort(404)
    return render_template(
        "admin_manage.html",
        kind=kind,
        config=ADMIN_SECTIONS[kind],
        items=read_data(kind),
    )


@admin_bp.route("/<kind>/new", methods=["GET", "POST"])
@admin_required
def admin_new(kind):
    if kind not in ADMIN_SECTIONS:
        abort(404)
    config = ADMIN_SECTIONS[kind]

    if request.method == "POST":
        verify_csrf()
        item = {"id": next_id(read_data(kind))}
        for key, _label, _field_type, _required in config["fields"]:
            item[key] = request.form.get(key, "").strip()
        if kind == "community" and not item.get("date"):
            item["date"] = datetime.now().strftime("%d %b %Y")

        try:
            uploaded = (
                save_uploaded_image(request.files.get("image_file"))
                if config["image"]
                else None
            )
        except ValueError as exc:
            flash(str(exc), "error")
            return render_template(
                "admin_form.html",
                kind=kind,
                config=config,
                item=item,
                mode="Add",
            )
        if uploaded:
            item["image"] = uploaded
        if any(
            required and not item.get(key)
            for key, _label, _field_type, required in config["fields"]
        ):
            flash("Please complete all required fields.", "error")
            return render_template(
                "admin_form.html",
                kind=kind,
                config=config,
                item=item,
                mode="Add",
            )

        items = read_data(kind)
        items.append(item)
        write_data(kind, items)
        flash(f'{config["singular"]} added successfully.', "success")
        return redirect(url_for("admin.admin_manage", kind=kind))

    return render_template(
        "admin_form.html",
        kind=kind,
        config=config,
        item={},
        mode="Add",
    )


@admin_bp.route("/<kind>/<int:item_id>/edit", methods=["GET", "POST"])
@admin_required
def admin_edit(kind, item_id):
    if kind not in ADMIN_SECTIONS:
        abort(404)
    config = ADMIN_SECTIONS[kind]
    items = read_data(kind)
    item = next(
        (record for record in items if int(record.get("id", -1)) == item_id),
        None,
    )
    if item is None:
        abort(404)

    if request.method == "POST":
        verify_csrf()
        updated = dict(item)
        for key, _label, _field_type, _required in config["fields"]:
            updated[key] = request.form.get(key, "").strip()
        try:
            uploaded = (
                save_uploaded_image(request.files.get("image_file"))
                if config["image"]
                else None
            )
        except ValueError as exc:
            flash(str(exc), "error")
            return render_template(
                "admin_form.html",
                kind=kind,
                config=config,
                item=updated,
                mode="Edit",
            )
        if uploaded:
            updated["image"] = uploaded
        if any(
            required and not updated.get(key)
            for key, _label, _field_type, required in config["fields"]
        ):
            flash("Please complete all required fields.", "error")
            return render_template(
                "admin_form.html",
                kind=kind,
                config=config,
                item=updated,
                mode="Edit",
            )

        write_data(
            kind,
            [
                updated if int(record.get("id", -1)) == item_id else record
                for record in items
            ],
        )
        flash(f'{config["singular"]} updated successfully.', "success")
        return redirect(url_for("admin.admin_manage", kind=kind))

    return render_template(
        "admin_form.html",
        kind=kind,
        config=config,
        item=item,
        mode="Edit",
    )


@admin_bp.route("/<kind>/<int:item_id>/delete", methods=["POST"])
@admin_required
def admin_delete(kind, item_id):
    if kind not in ADMIN_SECTIONS:
        abort(404)
    verify_csrf()
    items = read_data(kind)
    kept = [
        item for item in items
        if int(item.get("id", -1)) != item_id
    ]
    if len(kept) == len(items):
        abort(404)

    write_data(kind, kept)
    flash(f'{ADMIN_SECTIONS[kind]["singular"]} deleted.', "success")
    return redirect(url_for("admin.admin_manage", kind=kind))
