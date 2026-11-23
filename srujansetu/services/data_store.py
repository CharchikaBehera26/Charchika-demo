import json
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from flask import current_app
from sqlalchemy import delete, select

from ..extensions import db
from ..models import (
    AppMetadata,
    Artisan,
    ArtisanAccount,
    CommunityPost,
    Craft,
    CustomerOrder,
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


SAMPLE_DEMO_ORDERS = [
    {
        "id": "demo-order-101",
        "customer_id": "cust-asha",
        "customer_name": "Asha Mohapatra",
        "phone": "+91 98610 23456",
        "address": "Nayapalli, Bhubaneswar, Odisha - 751012",
        "items": [
            {
                "product_id": 1,
                "owner_id": "maker-sasmita",
                "name": "Jagannath Pattachitra Panel",
                "artisan": "Sasmita Das",
                "quantity": 1,
                "unit_price": "₹1,800.00",
                "line_total": "₹1,800.00",
            },
            {
                "product_id": 2,
                "owner_id": "maker-ramesh",
                "name": "Sambalpuri Stole",
                "artisan": "Ramesh Meher",
                "quantity": 1,
                "unit_price": "₹1,250.00",
                "line_total": "₹1,250.00",
            },
        ],
        "total_price": Decimal("3050.00"),
        "days_ago": 115,
    },
    {
        "id": "demo-order-102",
        "customer_id": "cust-debasis",
        "customer_name": "Debasis Panda",
        "phone": "+91 94371 87654",
        "address": "Bidanasi, Cuttack, Odisha - 753014",
        "items": [
            {
                "product_id": 4,
                "owner_id": "maker-bikash",
                "name": "Tarakasi Filigree Pendant",
                "artisan": "Bikash Mohanty",
                "quantity": 1,
                "unit_price": "₹2,400.00",
                "line_total": "₹2,400.00",
            },
            {
                "product_id": 13,
                "owner_id": "maker-bikash",
                "name": "Tarakasi Silver Filigree Earrings",
                "artisan": "Bikash Mohanty",
                "quantity": 1,
                "unit_price": "₹1,950.00",
                "line_total": "₹1,950.00",
            },
        ],
        "total_price": Decimal("4350.00"),
        "days_ago": 85,
    },
    {
        "id": "demo-order-103",
        "customer_id": "cust-sunita",
        "customer_name": "Sunita Jena",
        "phone": "+91 99370 45678",
        "address": "Grand Road, Puri, Odisha - 752001",
        "items": [
            {
                "product_id": 3,
                "owner_id": "maker-priyanka",
                "name": "Pipili Decorative Umbrella",
                "artisan": "Priyanka Sahoo",
                "quantity": 2,
                "unit_price": "₹950.00",
                "line_total": "₹1,900.00",
            },
            {
                "product_id": 8,
                "owner_id": "maker-priyanka",
                "name": "Pipili Appliqué Wall Hanging",
                "artisan": "Priyanka Sahoo",
                "quantity": 1,
                "unit_price": "₹780.00",
                "line_total": "₹780.00",
            },
        ],
        "total_price": Decimal("2680.00"),
        "days_ago": 60,
    },
    {
        "id": "demo-order-104",
        "customer_id": "cust-rohan",
        "customer_name": "Rohan Patnaik",
        "phone": "+91 94372 12345",
        "address": "Civil Township, Rourkela, Odisha - 769004",
        "items": [
            {
                "product_id": 6,
                "owner_id": "maker-dhaneswar",
                "name": "Dhokra Dancing Figure",
                "artisan": "Dhaneswar Naik",
                "quantity": 1,
                "unit_price": "₹1,650.00",
                "line_total": "₹1,650.00",
            },
            {
                "product_id": 14,
                "owner_id": "maker-dhaneswar",
                "name": "Dhokra Brass Desk Bell",
                "artisan": "Dhaneswar Naik",
                "quantity": 2,
                "unit_price": "₹720.00",
                "line_total": "₹1,440.00",
            },
        ],
        "total_price": Decimal("3090.00"),
        "days_ago": 48,
    },
    {
        "id": "demo-order-105",
        "customer_id": "cust-ananya",
        "customer_name": "Ananya Das",
        "phone": "+91 98611 98765",
        "address": "Dhanupali, Sambalpur, Odisha - 768005",
        "items": [
            {
                "product_id": 19,
                "owner_id": "shg-bargarh",
                "name": "Sambalpuri Silk Handloom Saree",
                "artisan": "Bargarh Meher Bunakar Handloom SHG",
                "quantity": 1,
                "unit_price": "₹4,999.00",
                "line_total": "₹4,999.00",
            },
        ],
        "total_price": Decimal("4999.00"),
        "days_ago": 32,
    },
    {
        "id": "demo-order-106",
        "customer_id": "cust-priya",
        "customer_name": "Priya Ray",
        "phone": "+91 94373 54321",
        "address": "OT Road, Balasore, Odisha - 756001",
        "items": [
            {
                "product_id": 5,
                "owner_id": "maker-laxmi",
                "name": "Terracotta Horse Pair",
                "artisan": "Laxmi Behera",
                "quantity": 1,
                "unit_price": "₹850.00",
                "line_total": "₹850.00",
            },
            {
                "product_id": 17,
                "owner_id": "maker-laxmi",
                "name": "Terracotta Oil Lamp Set",
                "artisan": "Laxmi Behera",
                "quantity": 2,
                "unit_price": "₹360.00",
                "line_total": "₹720.00",
            },
        ],
        "total_price": Decimal("1570.00"),
        "days_ago": 24,
    },
    {
        "id": "demo-order-107",
        "customer_id": "cust-jyoti",
        "customer_name": "Jyoti Sahoo",
        "phone": "+91 99371 67890",
        "address": "Baghra Road, Baripada, Mayurbhanj, Odisha - 757001",
        "items": [
            {
                "product_id": 22,
                "owner_id": "shg-mayurbhanj",
                "name": "Sabai Grass Handwoven Storage Basket",
                "artisan": "Mayurbhanj Sabai Grass Producers SHG",
                "quantity": 2,
                "unit_price": "₹850.00",
                "line_total": "₹1,700.00",
            },
            {
                "product_id": 23,
                "owner_id": "shg-mayurbhanj",
                "name": "Sabai Grass Dining Placemat Set",
                "artisan": "Mayurbhanj Sabai Grass Producers SHG",
                "quantity": 1,
                "unit_price": "₹550.00",
                "line_total": "₹550.00",
            },
        ],
        "total_price": Decimal("2250.00"),
        "days_ago": 15,
    },
    {
        "id": "demo-order-108",
        "customer_id": "cust-bikram",
        "customer_name": "Bikram Choudhury",
        "phone": "+91 98612 34567",
        "address": "Saheed Nagar, Bhubaneswar, Odisha - 751007",
        "items": [
            {
                "product_id": 18,
                "owner_id": "shg-raghurajpur",
                "name": "Tree of Life Pattachitra Canvas",
                "artisan": "Sample Raghurajpur Artisans SHG",
                "quantity": 1,
                "unit_price": "₹2,199.00",
                "line_total": "₹2,199.00",
            },
            {
                "product_id": 28,
                "owner_id": "shg-konark",
                "name": "Konark Sandstone Wheel Replica",
                "artisan": "Konark Heritage Stone Carvers SHG",
                "quantity": 1,
                "unit_price": "₹2,990.00",
                "line_total": "₹2,990.00",
            },
        ],
        "total_price": Decimal("5189.00"),
        "days_ago": 6,
    },
    {
        "id": "demo-order-109",
        "customer_id": "cust-rina",
        "customer_name": "Rina Pradhan",
        "phone": "+91 94374 98765",
        "address": "Tinikonia Bagicha, Cuttack, Odisha - 753001",
        "items": [
            {
                "product_id": 20,
                "owner_id": "shg-cuttack",
                "name": "Konark Wheel Silver Brooch",
                "artisan": "Sample Cuttack Silver Craft SHG",
                "quantity": 1,
                "unit_price": "₹2,850.00",
                "line_total": "₹2,850.00",
            },
            {
                "product_id": 24,
                "owner_id": "shg-kendrapara",
                "name": "Kaincha Golden Grass Jewellery Box",
                "artisan": "Kendrapara Golden Grass Craft SHG",
                "quantity": 1,
                "unit_price": "₹750.00",
                "line_total": "₹750.00",
            },
        ],
        "total_price": Decimal("3600.00"),
        "days_ago": 2,
    },
]


def seed_demo_data():
    from .accounts import read_artisan_users, save_admin_record, write_artisan_users

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
                    if collection == "products":
                        product = db.session.get(model, existing["id"])
                        if product is not None:
                            if not existing.get("image") or (
                                item.get("image") and item["image"] != existing.get("image")
                            ):
                                product.image = item["image"]
                            if item.get("category") and not existing.get("category"):
                                product.category = item["category"]
                            if item.get("deal_price") and not existing.get("deal_price"):
                                product.deal_price = item["deal_price"]
                            if item.get("owner_id") and not existing.get("owner_id"):
                                product.owner_id = item["owner_id"]
                    elif collection == "artisans":
                        artisan = db.session.get(model, existing["id"])
                        if artisan is not None:
                            if item.get("latitude") and not existing.get("latitude"):
                                artisan.latitude = item["latitude"]
                                artisan.longitude = item["longitude"]
                            if item.get("image") and not existing.get("image"):
                                artisan.image = item["image"]
                            if item.get("maker_type"):
                                artisan.maker_type = item["maker_type"]
                            if "approximate_location" in item:
                                artisan.approximate_location = item["approximate_location"]
                            if item.get("account_id") and not existing.get("account_id"):
                                artisan.account_id = item["account_id"]
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

        # Sync missing artisan accounts
        users_path = current_app.config["JSON_SEED_FILES"]["artisan_users"]
        if users_path.exists():
            existing_user_ids = {str(u.get("id", "")) for u in read_artisan_users()}
            existing_emails = {str(u.get("email", "")).lower() for u in read_artisan_users()}
            for u in json.loads(users_path.read_text(encoding="utf-8")):
                uid = str(u.get("id", ""))
                uemail = str(u.get("email", "")).lower()
                if uid and uid not in existing_user_ids and uemail not in existing_emails:
                    db.session.add(
                        ArtisanAccount(
                            id=uid,
                            name=u["name"],
                            email=u["email"],
                            password_hash=u["password_hash"],
                            supabase_user_id=u.get("supabase_user_id"),
                        )
                    )
                    existing_user_ids.add(uid)
                    existing_emails.add(uemail)
            db.session.commit()

        # Seed sample demo customer orders if none exist and not in test suite
        if not current_app.config.get("TESTING"):
            has_orders = db.session.scalar(select(CustomerOrder).limit(1))
            if not has_orders:
                now = datetime.now(timezone.utc)
                for order_info in SAMPLE_DEMO_ORDERS:
                    created_at = now - timedelta(days=order_info["days_ago"])
                    db.session.add(
                        CustomerOrder(
                            id=order_info["id"],
                            customer_id=order_info["customer_id"],
                            customer_name=order_info["customer_name"],
                            phone=order_info["phone"],
                            address=order_info["address"],
                            items_json=json.dumps(order_info["items"]),
                            total_price=order_info["total_price"],
                            created_at=created_at,
                        )
                    )
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
