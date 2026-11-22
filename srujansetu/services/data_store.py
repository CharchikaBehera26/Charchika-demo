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
        for collection in ("artisans", "products"):
            path = current_app.config["JSON_SEED_FILES"][collection]
            if not path.exists():
                continue
            model = COLLECTION_MODELS[collection]
            records = read_data(collection)
            records_by_id = {str(item.get("id")): item for item in records}
            existing_ids = {str(item.get("id")) for item in records}
            existing_names = {
                str(item.get("name", "")).casefold() for item in records
            }
            for item in json.loads(path.read_text(encoding="utf-8")):
                item_id = str(item.get("id", ""))
                item_name = str(item.get("name", "")).casefold()
                if item_id in existing_ids:
                    existing = records_by_id[item_id]
                    if (
                        collection == "products"
                        and str(existing.get("name", "")).casefold() == item_name
                        and not existing.get("image")
                        and item.get("image")
                    ):
                        product = db.session.get(model, existing["id"])
                        if product is not None:
                            product.image = item["image"]
                    continue
                if item_name in existing_names:
                    continue
                values = {
                    column.name: item[column.name]
                    for column in model.__table__.columns
                    if column.name in item
                }
                db.session.add(model(**values))
                existing_ids.add(item_id)
                existing_names.add(item_name)
                records_by_id[item_id] = item
        db.session.commit()
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
