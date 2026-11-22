import json
import re
from collections import Counter
from datetime import datetime

from flask import Blueprint, flash, jsonify, redirect, render_template, request, session, url_for
from sqlalchemy import select

from ..extensions import db
from ..models import CustomerOrder
from ..services.agents import generate_story, sell_reply
from ..services.data_store import read_data, write_data
from ..services.faq import cached_faqs, find_faq, normalize_question
from ..services.i18n import EN, localize_guide, normalize_lang, page_copy
from ..services.pricing import effective_product_price
from ..services.security import next_id, parse_optional_coordinates


public_bp = Blueprint("public", __name__)


@public_bp.route("/")
def home():
    artisans = read_data("artisans")
    crafts = read_data("crafts")
    products = read_data("products")
    return render_template(
        "index.html",
        artisans=artisans[:3],
        crafts=crafts[:5],
        artisan_count=len(artisans),
        craft_count=len(crafts),
        product_count=len(products),
    )


@public_bp.route("/crafts")
def crafts():
    query = request.args.get("q", "").strip().casefold()
    items = read_data("crafts")
    if query:
        items = [
            item for item in items
            if query in " ".join(
                item.get(key, "") for key in ("name", "region", "description")
            ).casefold()
        ]
    return render_template("crafts.html", crafts=items, query=query)


@public_bp.route("/artisans")
def artisans():
    query = request.args.get("q", "").strip().casefold()
    district = request.args.get("region", "").strip().casefold()
    items = read_data("artisans")
    if query:
        items = [
            item for item in items
            if query in " ".join(
                item.get(key, "") for key in ("name", "craft", "district")
            ).casefold()
        ]
    if district:
        items = [
            item for item in items
            if district in item.get("district", "").casefold()
        ]
    regions = sorted({
        item.get("district", "")
        for item in read_data("artisans")
        if item.get("district")
    })
    return render_template(
        "artisans.html",
        artisans=items,
        query=query,
        region=district,
        regions=regions,
    )


@public_bp.route("/marketplace")
def marketplace():
    all_products = read_data("products")
    categories = sorted({
        product.get("category") or product.get("craft") or "Other"
        for product in all_products
    })
    selected_category = request.args.get("category", "").strip()
    products = [
        product for product in all_products
        if not selected_category
        or (product.get("category") or product.get("craft") or "Other") == selected_category
    ]

    for product in all_products:
        product["current_price"] = effective_product_price(product)
        product["has_valid_deal"] = bool(
            product.get("deal_price") and product["current_price"] is not None
        )
        product["current_price_label"] = (
            f"₹{product['current_price']:,.2f}"
            if product["current_price"] is not None
            else ""
        )
        product["deal_price_label"] = (
            f"₹{product['current_price']:,.2f}"
            if product["has_valid_deal"]
            else ""
        )

    request_counts = Counter()
    for items_json in db.session.scalars(select(CustomerOrder.items_json)):
        for item in json.loads(items_json):
            name = item.get("name")
            quantity = item.get("quantity", 0)
            if name and isinstance(quantity, int) and quantity > 0:
                request_counts[name] += quantity
    most_requested = sorted(
        (
            (product, request_counts[product.get("name", "")])
            for product in all_products
            if request_counts[product.get("name", "")] > 0
        ),
        key=lambda item: (-item[1], item[0].get("name", "")),
    )[:4]

    featured = [product for product in all_products if product.get("is_featured")]
    featured = (featured or all_products)[:4]
    deals = [product for product in all_products if product["has_valid_deal"]]

    seller_counts = Counter(
        product.get("artisan", "")
        for product in all_products
        if product.get("artisan")
    )
    artisans = {
        artisan.get("name"): artisan
        for artisan in read_data("artisans")
    }
    sellers = [
        {
            "name": name,
            "listing_count": count,
            "profile": artisans.get(name),
        }
        for name, count in seller_counts.most_common(4)
    ]

    return render_template(
        "marketplace.html",
        products=products,
        categories=categories,
        selected_category=selected_category,
        featured=featured,
        most_requested=most_requested,
        deals=deals,
        sellers=sellers,
    )


@public_bp.route("/stories", methods=["GET", "POST"])
def stories():
    lang = normalize_lang(session.get("lang"))
    story_lang = lang
    generated = None
    selected_craft = request.form.get("craft", "") if request.method == "POST" else ""
    focus = request.form.get("focus", "making") if request.method == "POST" else "making"
    if request.method == "POST":
        story_lang = normalize_lang(request.form.get("story_lang") or lang)
        if not selected_craft:
            flash("Choose a craft before weaving a story.", "error")
        else:
            generated = generate_story(selected_craft, story_lang, focus)
            if generated is None:
                flash("That craft is not in the catalog.", "error")
    return render_template(
        "stories.html",
        stories=read_data("stories"),
        crafts=read_data("crafts"),
        generated=generated,
        selected_craft=selected_craft,
        focus=focus,
        copy=page_copy(lang),
        story_lang=story_lang,
    )


@public_bp.route("/schemes")
def schemes():
    query = request.args.get("q", "").strip().casefold()
    items = read_data("schemes")
    if query:
        items = [
            item for item in items
            if query in " ".join(
                item.get(key, "") for key in ("name", "audience", "description")
            ).casefold()
        ]
    return render_template("schemes.html", schemes=items, query=query)


@public_bp.route("/planner")
def planner():
    artisans = read_data("artisans")
    districts = sorted({
        "Puri",
        "Cuttack",
        "Sambalpur",
        "Bhubaneswar",
        "Raghurajpur",
        "Pipili",
        *(artisan.get("district", "").strip() for artisan in artisans if artisan.get("district")),
    })
    districts.insert(0, "All districts")
    selected = request.args.get("district", "All districts").strip()
    if selected not in districts:
        selected = "All districts"

    matches = (
        artisans
        if selected == "All districts"
        else [
            artisan for artisan in artisans
            if artisan.get("district", "").casefold() == selected.casefold()
        ]
    )
    map_artisans = []
    for artisan in matches:
        try:
            coordinates = parse_optional_coordinates(
                str(artisan.get("latitude", "")),
                str(artisan.get("longitude", "")),
            )
        except ValueError:
            continue
        if coordinates is not None:
            map_artisans.append({
                "name": artisan.get("name", "Artisan"),
                "craft": artisan.get("craft", ""),
                "district": artisan.get("district", ""),
                "latitude": coordinates[0],
                "longitude": coordinates[1],
            })
    return render_template(
        "planner.html",
        districts=districts,
        selected=selected,
        artisans=matches,
        map_artisans=map_artisans,
    )


def assistant_reply(message):
    faq = find_faq(message)
    if faq:
        return faq.answer, [
            {"label": label, "url": url_for(endpoint)}
            for label, endpoint in faq.actions
        ]

    normalized = normalize_question(message)

    def mentions(*phrases):
        return any(
            re.search(rf"(?<!\w){re.escape(phrase)}(?!\w)", normalized)
            for phrase in phrases
        )

    def action(label, endpoint, **values):
        return {"label": label, "url": url_for(f"public.{endpoint}", **values)}

    if mentions("sign in", "sign-in", "login", "log in", "my account"):
        return (
            EN["signin"],
            [{"label": "Open artisan sign in", "url": url_for("artisan.artisan_login")}],
        )

    if mentions("register", "registration", "sign up", "create account", "join as"):
        return (
            EN["register"],
            [{"label": "Create a maker account", "url": url_for("artisan.artisan_register")}],
        )

    if mentions("nearby", "near me", "map", "location", "directions"):
        return (
            EN["map"],
            [
                action("Open the artisan map", "planner"),
                action("Browse all artisan profiles", "artisans"),
            ],
        )

    if mentions("find artisan", "find artisans", "meet artisan", "meet artisans", "maker", "shg", "self help group"):
        return (
            EN["find"],
            [
                action("Find artisans", "artisans"),
                action("Open the artisan map", "planner"),
            ],
        )

    if mentions("business", "sell", "selling", "add product", "list product"):
        if session.get("role") == "artisan":
            return (
                EN["sell_in"],
                [{
                    "label": "Add a product",
                    "url": url_for("artisan.artisan_product_new"),
                }],
            )
        return (
            EN["sell_out"],
            [
                {"label": "Create a maker account", "url": url_for("artisan.artisan_register")},
                {"label": "Sign in", "url": url_for("artisan.artisan_login")},
                {"label": "Ask the sell assistant", "url": url_for("public.sell")},
            ],
        )

    if mentions("buy", "shop", "marketplace", "product", "products", "price"):
        return (
            EN["buy"],
            [
                action("Explore the SHG marketplace", "marketplace"),
                {"label": "Ask the sell assistant", "url": url_for("public.sell")},
            ],
        )

    if mentions("scheme", "schemes", "government", "grant", "support", "benefit"):
        return (
            EN["scheme"],
            [action("Open the scheme finder", "schemes")],
        )

    if mentions("story", "stories", "history", "tradition"):
        return (
            EN["story"],
            [
                action("Read craft stories", "stories"),
                {"label": "Write a craft story", "url": url_for("public.stories")},
            ],
        )

    if mentions("community", "share a note", "post a message"):
        return (
            EN["community"],
            [action("Visit the community", "community")],
        )

    craft = next(
        (
            item for item in read_data("crafts")
            if item.get("name", "").casefold() in normalized
            or any(
                re.search(rf"(?<!\w){re.escape(word.casefold())}(?!\w)", normalized)
                for word in item.get("name", "").split()
                if len(word) > 3
            )
        ),
        None,
    )
    if craft:
        return (
            f"{craft['name']}: {craft.get('description', '')} It is associated with {craft.get('region', 'Odisha')}.",
            [
                action("Explore this craft", "crafts", q=craft["name"]),
                action("Find its makers", "artisans", q=craft["name"]),
            ],
        )

    if mentions("hello", "hi", "hey", "namaskar", "help", "what can you do"):
        return (
            EN["hello"],
            [
                action("Explore crafts", "crafts"),
                action("Find artisans", "artisans"),
                action("Visit the marketplace", "marketplace"),
                action("Browse schemes", "schemes"),
            ],
        )

    if mentions("craft", "crafts", "handicraft", "handicrafts", "weaving"):
        return (
            EN["crafts"],
            [action("Browse Odisha crafts", "crafts")],
        )

    return (
        EN["fallback"],
        [
            action("Explore crafts", "crafts"),
            action("Find artisans", "artisans"),
            action("Open the map", "planner"),
            action("Ask another question", "assistant"),
        ],
    )


def _safe_next(value):
    if not value or not value.startswith("/") or value.startswith("//"):
        return url_for("public.home")
    return value


@public_bp.route("/language", methods=["POST"])
def set_language():
    session["lang"] = normalize_lang(request.form.get("lang"))
    return redirect(_safe_next(request.form.get("next")))


@public_bp.route("/assistant", methods=["GET", "POST"])
def assistant():
    message = ""
    answer = None
    actions = []
    lang = normalize_lang(session.get("lang"))
    if request.method == "POST":
        message = request.form.get("message", "").strip()
        lang = normalize_lang(request.form.get("lang") or lang)
        session["lang"] = lang
        is_async = request.headers.get("X-Requested-With") == "XMLHttpRequest"
        if not message:
            if is_async:
                return jsonify(error="Enter a question before sending it."), 400
            flash("Enter a question before sending it.", "error")
        elif len(message) > 500:
            if is_async:
                return jsonify(error="Please keep your question under 500 characters."), 400
            flash("Please keep your question under 500 characters.", "error")
        else:
            answer, actions = localize_guide(*assistant_reply(message), lang)
            if is_async:
                return jsonify(
                    answer=answer,
                    actions=actions,
                    message=message,
                    lang=lang,
                )
    return render_template(
        "assistant.html",
        message=message,
        answer=answer,
        actions=actions,
        faq_items=cached_faqs(),
        copy=page_copy(lang),
    )


@public_bp.route("/sell", methods=["GET", "POST"])
def sell():
    message = ""
    answer = None
    actions = []
    picks = []
    lang = normalize_lang(session.get("lang"))
    if request.method == "POST":
        message = request.form.get("message", "").strip()
        lang = normalize_lang(request.form.get("lang") or lang)
        session["lang"] = lang
        if not message:
            flash("Tell the sell assistant what you are looking for.", "error")
        elif len(message) > 500:
            flash("Please keep your note under 500 characters.", "error")
        else:
            answer, picks, actions = sell_reply(message, lang)
    return render_template(
        "sell.html",
        message=message,
        answer=answer,
        actions=actions,
        picks=picks,
        copy=page_copy(lang),
    )


@public_bp.route("/business")
def business():
    tips = [
        "Use clear product photos with a plain background and natural light.",
        "Tell the story behind the craft, materials and artisan community.",
        "List dimensions, care instructions and shipping details clearly.",
        "Keep prices, stock information and contact details up to date.",
    ]
    return render_template("business.html", tips=tips)


@public_bp.route("/community", methods=["GET", "POST"])
def community():
    if request.method == "POST":
        entries = read_data("community")
        name = request.form.get("name", "").strip()
        message = request.form.get("message", "").strip()
        if name and message:
            entries.insert(0, {
                "id": next_id(entries),
                "name": name,
                "message": message,
                "date": datetime.now().strftime("%d %b %Y"),
            })
            write_data("community", entries[:100])
            flash("Your community note has been added.", "success")
        else:
            flash("Please add your name and a message.", "error")
        return redirect(url_for("public.community"))
    return render_template("community.html", entries=read_data("community"))


@public_bp.route("/about")
def about():
    return render_template("about.html")


@public_bp.route("/api/search")
def api_search():
    query = request.args.get("q", "").strip().casefold()
    results = []
    route_names = {
        "artisans": "public.artisans",
        "crafts": "public.crafts",
        "products": "public.marketplace",
    }
    for collection, endpoint in route_names.items():
        for item in read_data(collection):
            searchable_text = " ".join(str(value) for value in item.values()).casefold()
            if query and query in searchable_text:
                results.append({
                    "type": collection[:-1],
                    "name": item.get("name", "Untitled"),
                    "url": url_for(endpoint),
                })
    return jsonify(results[:8])
