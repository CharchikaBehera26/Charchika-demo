import re
from datetime import datetime

from flask import Blueprint, flash, jsonify, redirect, render_template, request, session, url_for

from ..services.data_store import read_data, write_data
from ..services.faq import cached_faqs, find_faq, normalize_question
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
    return render_template("marketplace.html", products=read_data("products"))


@public_bp.route("/stories")
def stories():
    return render_template("stories.html", stories=read_data("stories"))


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
            "Use the artisan and SHG portal to sign in and manage your public profile or product listings.",
            [{"label": "Open artisan sign in", "url": url_for("artisan.artisan_login")}],
        )

    if mentions("register", "registration", "sign up", "create account", "join as"):
        return (
            "Create an artisan or SHG account to publish a profile and manage marketplace listings. You can add an exact public map location from your profile later.",
            [{"label": "Create a maker account", "url": url_for("artisan.artisan_register")}],
        )

    if mentions("nearby", "near me", "map", "location", "directions"):
        return (
            "The map is centered on Odisha. It shows exact public pins only for makers who have added coordinates to their profile.",
            [
                action("Open the artisan map", "planner"),
                action("Browse all artisan profiles", "artisans"),
            ],
        )

    if mentions("find artisan", "find artisans", "meet artisan", "meet artisans", "maker", "shg", "self help group"):
        return (
            "Browse maker profiles by name, craft or district. You can also use the map to see profiles that have shared an exact public location.",
            [
                action("Find artisans", "artisans"),
                action("Open the artisan map", "planner"),
            ],
        )

    if mentions("business", "sell", "selling", "add product", "list product"):
        if session.get("role") == "artisan":
            return (
                "You are signed in. Add a product listing from your maker workspace.",
                [{
                    "label": "Add a product",
                    "url": url_for("artisan.artisan_product_new"),
                }],
            )
        return (
            "To sell through the demonstration marketplace, first create a maker account. Already registered? Sign in to manage your listings.",
            [
                {"label": "Create a maker account", "url": url_for("artisan.artisan_register")},
                {"label": "Sign in", "url": url_for("artisan.artisan_login")},
            ],
        )

    if mentions("buy", "shop", "marketplace", "product", "products", "price"):
        return (
            "The marketplace contains demonstration listings. Open a product listing to discover its maker and craft.",
            [action("Explore the SHG marketplace", "marketplace")],
        )

    if mentions("scheme", "schemes", "government", "grant", "support", "benefit"):
        return (
            "The scheme finder contains illustrative information only. Confirm eligibility, availability and application details with the official department before applying.",
            [action("Open the scheme finder", "schemes")],
        )

    if mentions("story", "stories", "history", "tradition"):
        return (
            "Explore short introductions to Odisha's living craft traditions and the people who carry them forward.",
            [action("Read craft stories", "stories")],
        )

    if mentions("community", "share a note", "post a message"):
        return (
            "You can share an encouraging note with the SrujanSetu community.",
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
            "Namaskar! I can answer questions using the site's craft information and guide you to artisans, the map, marketplace, stories, community or scheme finder. What would you like to do?",
            [
                action("Explore crafts", "crafts"),
                action("Find artisans", "artisans"),
                action("Visit the marketplace", "marketplace"),
                action("Browse schemes", "schemes"),
            ],
        )

    if mentions("craft", "crafts", "handicraft", "handicrafts", "weaving"):
        return (
            "The craft directory covers Odisha traditions, including Pattachitra, Sambalpuri Ikat, Pipili Appliqué, Silver Filigree, Terracotta and Dhokra.",
            [action("Browse Odisha crafts", "crafts")],
        )

    return (
        "I couldn't find that in the site's information yet. I can help with Odisha crafts, finding artisans, exact map locations, marketplace listings, community posts and scheme information.",
        [
            action("Explore crafts", "crafts"),
            action("Find artisans", "artisans"),
            action("Open the map", "planner"),
            action("Ask another question", "assistant"),
        ],
    )


@public_bp.route("/assistant", methods=["GET", "POST"])
def assistant():
    message = ""
    answer = None
    actions = []
    if request.method == "POST":
        message = request.form.get("message", "").strip()
        if not message:
            flash("Enter a question before sending it.", "error")
        elif len(message) > 500:
            flash("Please keep your question under 500 characters.", "error")
        else:
            answer, actions = assistant_reply(message)
    return render_template(
        "assistant.html",
        message=message,
        answer=answer,
        actions=actions,
        faq_items=cached_faqs(),
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
