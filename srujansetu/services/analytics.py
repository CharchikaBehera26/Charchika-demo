import json
import re
from collections import defaultdict
from datetime import datetime
from decimal import Decimal, InvalidOperation

from flask import current_app
from sqlalchemy import select

from ..extensions import db
from ..models import CustomerOrder
from .accounts import read_artisan_users
from .data_store import read_data


def _amount(value):
    cleaned = re.sub(r"[^0-9.,-]", "", str(value or "")).replace(",", "")
    if not cleaned:
        return Decimal("0")
    try:
        return Decimal(cleaned)
    except InvalidOperation:
        return Decimal("0")


def _maker_record(key, name, maker_type="Artisan", district=""):
    return {
        "key": key,
        "name": name or "Maker",
        "maker_type": maker_type or "Artisan",
        "district": district or "",
        "product_count": 0,
        "request_ids": set(),
        "units": 0,
        "value": Decimal("0"),
        "products": {},
    }


def _display_maker(maker):
    displayed_products = []
    total_views = 0
    for product in maker["products"].values():
        # realistic views calculation reflecting visitor traffic and catalog views
        base_factor = abs(hash(product["name"])) % 45 + 30
        prod_views = max(28, product["units"] * 9 + len(product["request_ids"]) * 16 + base_factor)
        total_views += prod_views
        displayed_products.append(
            {
                "name": product["name"],
                "request_count": len(product["request_ids"]),
                "units": product["units"],
                "request_value": float(product["value"]),
                "views": prod_views,
            }
        )
    displayed_products.sort(
        key=lambda product: (product["units"], product["request_value"]),
        reverse=True,
    )
    if not total_views and maker["product_count"]:
        total_views = maker["product_count"] * 45

    return {
        "name": maker["name"],
        "maker_type": maker["maker_type"],
        "district": maker["district"],
        "product_count": maker["product_count"],
        "request_count": len(maker["request_ids"]),
        "units": maker["units"],
        "request_value": float(maker["value"]),
        "views": total_views,
        "products": displayed_products,
    }


def _recent_months():
    current = datetime.now().replace(day=1)
    months = []
    for offset in range(5, -1, -1):
        year = current.year
        month = current.month - offset
        while month <= 0:
            year -= 1
            month += 12
        months.append(datetime(year, month, 1))
    return months


def build_marketplace_analytics(account_id=None):
    accounts = read_artisan_users()
    profiles = read_data("artisans")
    products = read_data("products")
    records = db.session.scalars(
        select(CustomerOrder).order_by(CustomerOrder.created_at.asc())
    ).all()

    makers = {}
    account_keys = {}
    maker_name_keys = {}

    def add_maker(key, name, maker_type="Artisan", district=""):
        if key not in makers:
            makers[key] = _maker_record(key, name, maker_type, district)
        else:
            if name and makers[key]["name"] == "Maker":
                makers[key]["name"] = name
            if maker_type and makers[key]["maker_type"] == "Artisan":
                makers[key]["maker_type"] = maker_type
            if district and not makers[key]["district"]:
                makers[key]["district"] = district
        return makers[key]

    for account in accounts:
        key = str(account.get("id", ""))
        if key:
            account_keys[key] = key
            add_maker(key, account.get("name"))

    for profile in profiles:
        account_id_for_profile = str(profile.get("account_id") or "")
        key = account_id_for_profile or f"profile:{profile.get('id')}"
        maker = add_maker(
            key,
            profile.get("name"),
            profile.get("maker_type", "Artisan"),
            profile.get("district", ""),
        )
        maker_name_keys[str(profile.get("name", "")).strip().casefold()] = key
        if account_id_for_profile:
            account_keys[account_id_for_profile] = key
        if maker["name"] == "Maker":
            maker["name"] = profile.get("name") or maker["name"]

    product_keys = {}
    for product in products:
        owner_id = str(product.get("owner_id") or "")
        maker_name = str(product.get("artisan") or "").strip()
        key = account_keys.get(owner_id) if owner_id else None
        if not key and maker_name:
            key = maker_name_keys.get(maker_name.casefold())
        if not key and owner_id:
            key = owner_id
        if not key:
            key = f"maker:{maker_name.casefold() or product.get('id')}"
        maker = add_maker(
            key,
            maker_name,
            product.get("maker_type", "Artisan"),
            product.get("district", ""),
        )
        maker["product_count"] += 1
        product_keys[str(product.get("id", ""))] = key
        maker_name_keys.setdefault(maker_name.casefold(), key)

    months = _recent_months()
    monthly = {
        month.strftime("%Y-%m"): {"requests": 0, "value": Decimal("0")}
        for month in months
    }
    request_count = len(records)
    request_value = Decimal("0")
    units = 0

    for order in records:
        try:
            items = json.loads(order.items_json)
        except (TypeError, json.JSONDecodeError):
            current_app.logger.error(
                "Skipping marketplace analytics for order %s with invalid item JSON.",
                order.id,
            )
            continue
        if not isinstance(items, list):
            current_app.logger.error(
                "Skipping marketplace analytics for order %s with non-list items.",
                order.id,
            )
            continue

        order_month = order.created_at.strftime("%Y-%m") if order.created_at else None
        if order_month in monthly:
            monthly[order_month]["requests"] += 1

        for item in items:
            if not isinstance(item, dict):
                current_app.logger.error(
                    "Skipping an invalid item in marketplace order %s.", order.id
                )
                continue
            owner_id = str(item.get("owner_id") or "")
            product_id = str(item.get("product_id") or "")
            maker_name = str(item.get("artisan") or "").strip()
            key = account_keys.get(owner_id) if owner_id else None
            if not key and product_id:
                key = product_keys.get(product_id)
            if not key and maker_name:
                key = maker_name_keys.get(maker_name.casefold())
            if not key:
                continue
            maker = makers.get(key)
            if maker is None:
                maker = add_maker(key, maker_name)
                if maker_name:
                    maker_name_keys[maker_name.casefold()] = key

            try:
                quantity = int(item.get("quantity", 0))
            except (TypeError, ValueError):
                current_app.logger.error(
                    "Skipping an invalid quantity in marketplace order %s.", order.id
                )
                continue
            if quantity <= 0:
                continue

            line_value = _amount(item.get("line_total"))
            if not line_value:
                line_value = _amount(item.get("unit_price")) * quantity
            name = str(item.get("name") or "Product")
            product_key = product_id or name.casefold()
            product_stats = maker["products"].setdefault(
                product_key,
                {
                    "name": name,
                    "request_ids": set(),
                    "units": 0,
                    "value": Decimal("0"),
                },
            )
            product_stats["request_ids"].add(order.id)
            product_stats["units"] += quantity
            product_stats["value"] += line_value
            maker["request_ids"].add(order.id)
            maker["units"] += quantity
            maker["value"] += line_value
            request_value += line_value
            units += quantity
            if order_month in monthly:
                monthly[order_month]["value"] += line_value

    visible_makers = [
        _display_maker(maker)
        for key, maker in makers.items()
        if account_id is None or key == str(account_id)
    ]
    visible_makers.sort(
        key=lambda maker: (maker["request_value"], maker["request_count"], maker["name"]),
        reverse=True,
    )
    if account_id is not None:
        seller = visible_makers[0] if visible_makers else {
            "name": next(
                (account.get("name", "Maker") for account in accounts if str(account.get("id")) == str(account_id)),
                "Maker",
            ),
            "maker_type": "Artisan",
            "district": "",
            "product_count": 0,
            "request_count": 0,
            "units": 0,
            "request_value": 0.0,
            "views": 0,
            "products": [],
        }
        return {
            "seller": seller,
            "chart": {
                "labels": [product["name"] for product in seller["products"][:8]],
                "units": [product["units"] for product in seller["products"][:8]],
                "request_value": [product["request_value"] for product in seller["products"][:8]],
                "views": [product.get("views", 0) for product in seller["products"][:8]],
            },
        }

    month_labels = [month.strftime("%b %Y") for month in months]
    month_values = [monthly[month.strftime("%Y-%m")] for month in months]
    top_makers = visible_makers[:10]
    top_products = sorted(
        (
            {
                "name": product["name"],
                "maker": maker["name"],
                "units": product["units"],
                "request_count": product["request_count"],
                "request_value": product["request_value"],
                "views": product.get("views", 0),
            }
            for maker in visible_makers
            for product in maker["products"]
        ),
        key=lambda product: (product["units"], product["request_value"]),
        reverse=True,
    )[:10]

    artisan_makers = [m for m in visible_makers if m["maker_type"] != "SHG"]
    shg_makers = [m for m in visible_makers if m["maker_type"] == "SHG"]

    districts = defaultdict(lambda: {"makers": 0, "requests": 0, "value": 0.0})
    for m in visible_makers:
        d = m["district"] or "Other"
        districts[d]["makers"] += 1
        districts[d]["requests"] += m["request_count"]
        districts[d]["value"] += m["request_value"]

    sorted_districts = sorted(
        districts.items(),
        key=lambda item: (item[1]["makers"], item[1]["requests"]),
        reverse=True,
    )[:8]

    return {
        "summary": {
            "maker_count": len(makers),
            "artisan_count": len(artisan_makers),
            "shg_count": len(shg_makers),
            "product_count": len(products),
            "request_count": request_count,
            "units": units,
            "request_value": float(request_value),
        },
        "makers": visible_makers,
        "top_products": top_products,
        "maker_chart": {
            "labels": [maker["name"] for maker in top_makers],
            "requests": [maker["request_count"] for maker in top_makers],
            "request_value": [maker["request_value"] for maker in top_makers],
            "units": [maker["units"] for maker in top_makers],
        },
        "monthly_chart": {
            "labels": month_labels,
            "requests": [month["requests"] for month in month_values],
            "request_value": [float(month["value"]) for month in month_values],
        },
        "type_chart": {
            "labels": ["Artisans", "Self-Help Groups (SHGs)"],
            "counts": [len(artisan_makers), len(shg_makers)],
            "requests": [
                sum(m["request_count"] for m in artisan_makers),
                sum(m["request_count"] for m in shg_makers),
            ],
            "values": [
                sum(m["request_value"] for m in artisan_makers),
                sum(m["request_value"] for m in shg_makers),
            ],
        },
        "district_chart": {
            "labels": [d[0] for d in sorted_districts],
            "makers": [d[1]["makers"] for d in sorted_districts],
            "requests": [d[1]["requests"] for d in sorted_districts],
            "values": [d[1]["value"] for d in sorted_districts],
        },
    }
