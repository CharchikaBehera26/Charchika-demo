ADMIN_SECTIONS = {
    "artisans": {
        "title": "Artisans",
        "singular": "Artisan",
        "fields": [
            ("name", "Name", "text", True),
            ("craft", "Craft", "text", True),
            ("district", "District", "text", True),
            ("bio", "Biography", "textarea", False),
            ("experience", "Experience", "text", False),
            ("emoji", "Icon / Emoji", "text", False),
            ("image", "Image URL or uploaded image", "text", False),
        ],
        "image": True,
    },
    "crafts": {
        "title": "Crafts",
        "singular": "Craft",
        "fields": [
            ("name", "Craft name", "text", True),
            ("region", "Region", "text", True),
            ("description", "Description", "textarea", False),
            ("emoji", "Icon / Emoji", "text", False),
            ("tone", "Card colour theme", "text", False),
        ],
        "image": True,
    },
    "products": {
        "title": "Products",
        "singular": "Product",
        "fields": [
            ("name", "Product name", "text", True),
            ("craft", "Craft type", "text", False),
            ("category", "Category", "text", False),
            ("price", "Price", "text", True),
            ("deal_price", "Deal price (optional)", "text", False),
            ("is_featured", "Feature on marketplace", "checkbox", False),
            ("artisan", "Artisan / SHG", "text", False),
            ("district", "District", "text", False),
            ("description", "Description", "textarea", False),
            ("emoji", "Icon / Emoji", "text", False),
        ],
        "image": True,
    },
    "schemes": {
        "title": "Schemes",
        "singular": "Scheme",
        "fields": [
            ("name", "Scheme name", "text", True),
            ("audience", "Intended audience", "text", False),
            ("description", "Description", "textarea", False),
            ("note", "Important note", "textarea", False),
        ],
        "image": False,
    },
    "community": {
        "title": "Community posts",
        "singular": "Community post",
        "fields": [
            ("name", "Author name", "text", True),
            ("message", "Message", "textarea", True),
            ("date", "Date", "text", False),
        ],
        "image": False,
    },
}

ALLOWED_IMAGE_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}
