from sqlalchemy import delete, select

from ..extensions import db
from ..models import AdminAccount, ArtisanAccount


def admin_record():
    account = db.session.scalar(select(AdminAccount).limit(1))
    if account is None:
        return None
    return {
        "username": account.username,
        "password_hash": account.password_hash,
    }


def save_admin_record(record):
    db.session.execute(delete(AdminAccount))
    db.session.add(
        AdminAccount(
            username=record["username"],
            password_hash=record["password_hash"],
        )
    )
    db.session.commit()


def read_artisan_users():
    accounts = db.session.scalars(
        select(ArtisanAccount).order_by(ArtisanAccount.name)
    ).all()
    return [
        {
            "id": account.id,
            "name": account.name,
            "email": account.email,
            "password_hash": account.password_hash,
            "supabase_user_id": account.supabase_user_id,
        }
        for account in accounts
    ]


def write_artisan_users(users):
    db.session.execute(delete(ArtisanAccount))
    db.session.add_all(
        ArtisanAccount(
            id=user["id"],
            name=user["name"],
            email=user["email"],
            password_hash=user["password_hash"],
            supabase_user_id=user.get("supabase_user_id"),
        )
        for user in users
    )
    db.session.commit()
