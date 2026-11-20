import secrets

from flask import current_app

from ..constants import ALLOWED_IMAGE_EXTENSIONS


def save_uploaded_image(uploaded_file):
    if not uploaded_file or not uploaded_file.filename:
        return None
    if "." not in uploaded_file.filename:
        raise ValueError("Please upload a PNG, JPG, JPEG, GIF or WEBP image.")

    extension = uploaded_file.filename.rsplit(".", 1)[1].lower()
    if extension not in ALLOWED_IMAGE_EXTENSIONS:
        raise ValueError("Please upload a PNG, JPG, JPEG, GIF or WEBP image.")

    filename = f"{secrets.token_hex(12)}.{extension}"
    uploaded_file.save(current_app.config["UPLOAD_FOLDER"] / filename)
    return f"/static/uploads/{filename}"
