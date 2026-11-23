from datetime import datetime, timezone

from .extensions import db


class Artisan(db.Model):
    __tablename__ = "artisans"

    id = db.Column(db.Integer, primary_key=True)
    account_id = db.Column(db.String(64), index=True)
    name = db.Column(db.String(160), nullable=False)
    craft = db.Column(db.String(160), nullable=False)
    district = db.Column(db.String(120), nullable=False, index=True)
    maker_type = db.Column(db.String(40), nullable=False, default="Artisan")
    approximate_location = db.Column(db.Boolean, nullable=False, default=False)
    bio = db.Column(db.Text, nullable=False, default="")
    experience = db.Column(db.String(120), nullable=False, default="")
    emoji = db.Column(db.String(32), nullable=False, default="🧵")
    image = db.Column(db.Text)
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)


class Craft(db.Model):
    __tablename__ = "crafts"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(160), nullable=False)
    region = db.Column(db.String(200), nullable=False, default="")
    description = db.Column(db.Text, nullable=False, default="")
    emoji = db.Column(db.String(32), nullable=False, default="")
    tone = db.Column(db.String(40), nullable=False, default="")


class Product(db.Model):
    __tablename__ = "products"

    id = db.Column(db.Integer, primary_key=True)
    owner_id = db.Column(db.String(64), index=True)
    name = db.Column(db.String(200), nullable=False)
    craft = db.Column(db.String(160), nullable=False, default="")
    category = db.Column(db.String(160), nullable=False, default="")
    price = db.Column(db.String(80), nullable=False)
    deal_price = db.Column(db.String(80), nullable=False, default="")
    is_featured = db.Column(db.Boolean, nullable=False, default=False)
    artisan = db.Column(db.String(160), nullable=False, default="")
    district = db.Column(db.String(120), nullable=False, default="")
    description = db.Column(db.Text, nullable=False, default="")
    emoji = db.Column(db.String(32), nullable=False, default="")
    image = db.Column(db.Text)


class Scheme(db.Model):
    __tablename__ = "schemes"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    audience = db.Column(db.String(200), nullable=False, default="")
    description = db.Column(db.Text, nullable=False, default="")
    note = db.Column(db.Text, nullable=False, default="")


class Story(db.Model):
    __tablename__ = "stories"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    category = db.Column(db.String(160), nullable=False, default="")
    description = db.Column(db.Text, nullable=False, default="")
    emoji = db.Column(db.String(32), nullable=False, default="")


class CommunityPost(db.Model):
    __tablename__ = "community_posts"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(160), nullable=False)
    message = db.Column(db.Text, nullable=False)
    date = db.Column(db.String(40), nullable=False, default="")


class ArtisanAccount(db.Model):
    __tablename__ = "artisan_accounts"

    id = db.Column(db.String(64), primary_key=True)
    name = db.Column(db.String(160), nullable=False)
    email = db.Column(db.String(255), nullable=False, unique=True, index=True)
    password_hash = db.Column(db.String(255))
    supabase_user_id = db.Column(db.String(64), unique=True, index=True)


class CustomerAccount(db.Model):
    __tablename__ = "customer_accounts"

    id = db.Column(db.String(64), primary_key=True)
    name = db.Column(db.String(160), nullable=False)
    email = db.Column(db.String(255), nullable=False, unique=True, index=True)
    password_hash = db.Column(db.String(255))
    supabase_user_id = db.Column(db.String(64), unique=True, index=True)


class CustomerOrder(db.Model):
    __tablename__ = "customer_orders"

    id = db.Column(db.String(64), primary_key=True)
    customer_id = db.Column(db.String(64), nullable=False, index=True)
    customer_name = db.Column(db.String(160), nullable=False)
    phone = db.Column(db.String(40), nullable=False)
    address = db.Column(db.Text, nullable=False)
    items_json = db.Column(db.Text, nullable=False)
    total_price = db.Column(db.Numeric(12, 2), nullable=False)
    created_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )


class AdminAccount(db.Model):
    __tablename__ = "admin_accounts"

    id = db.Column(db.Integer, primary_key=True, default=1)
    username = db.Column(db.String(120), nullable=False, unique=True)
    password_hash = db.Column(db.String(255), nullable=False)


class AppMetadata(db.Model):
    __tablename__ = "app_metadata"

    key = db.Column(db.String(80), primary_key=True)
    value = db.Column(db.String(255), nullable=False)
