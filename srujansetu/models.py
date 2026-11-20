from .extensions import db


class Artisan(db.Model):
    __tablename__ = "artisans"

    id = db.Column(db.Integer, primary_key=True)
    account_id = db.Column(db.String(64), index=True)
    name = db.Column(db.String(160), nullable=False)
    craft = db.Column(db.String(160), nullable=False)
    district = db.Column(db.String(120), nullable=False, index=True)
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
    price = db.Column(db.String(80), nullable=False)
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
    password_hash = db.Column(db.String(255), nullable=False)


class AdminAccount(db.Model):
    __tablename__ = "admin_accounts"

    id = db.Column(db.Integer, primary_key=True, default=1)
    username = db.Column(db.String(120), nullable=False, unique=True)
    password_hash = db.Column(db.String(255), nullable=False)


class AppMetadata(db.Model):
    __tablename__ = "app_metadata"

    key = db.Column(db.String(80), primary_key=True)
    value = db.Column(db.String(255), nullable=False)
