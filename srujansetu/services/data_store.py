import json

from flask import current_app
from sqlalchemy import delete, select

from ..extensions import db
from ..models import (
    AppMetadata,
    Artisan,
    CommunityPost,
    Craft,
    Product,
    Scheme,
    Story,
)


COLLECTION_MODELS = {
    "artisans": Artisan,
    "community": CommunityPost,
    "crafts": Craft,
    "products": Product,
    "schemes": Scheme,
    "stories": Story,
}


def read_data(collection):
    model = COLLECTION_MODELS[collection]
    records = db.session.scalars(select(model).order_by(model.id)).all()
    return [
        {
            column.name: getattr(record, column.name)
            for column in model.__table__.columns
        }
        for record in records
    ]


def write_data(collection, items):
    model = COLLECTION_MODELS[collection]
    db.session.execute(delete(model))
    for item in items:
        values = {
            column.name: item[column.name]
            for column in model.__table__.columns
            if column.name in item
        }
        db.session.add(model(**values))
    db.session.commit()


def seed_demo_data():
    from .accounts import save_admin_record, write_artisan_users

    metadata = db.session.get(AppMetadata, "demo_data_seeded")
    if metadata:
        return

    for collection, path in current_app.config["JSON_SEED_FILES"].items():
        if not path.exists():
            continue
        items = json.loads(path.read_text(encoding="utf-8"))
        if collection == "admin":
            if items:
                save_admin_record(items)
        elif collection == "artisan_users":
            if items:
                write_artisan_users(items)
        elif items and not read_data(collection):
            write_data(collection, items)

    db.session.add(AppMetadata(key="demo_data_seeded", value="true"))
    db.session.commit()
