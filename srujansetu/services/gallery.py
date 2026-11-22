"""Photographic stand-ins for pages that do not yet have an uploaded picture."""

SCENE_IMAGES = {
    "hero": "https://images.unsplash.com/photo-1610030469983-98e550d6193c?auto=format&fit=crop&w=1400&q=80",
    "crafts": "https://images.unsplash.com/photo-1579783902614-a3fb3927b6a5?auto=format&fit=crop&w=1400&q=80",
    "artisans": "https://images.unsplash.com/photo-1452860606245-08befc0ff44b?auto=format&fit=crop&w=1400&q=80",
    "market": "https://images.unsplash.com/photo-1610701596007-11502861dcfa?auto=format&fit=crop&w=1400&q=80",
    "stories": "https://images.unsplash.com/photo-1579783902614-a3fb3927b6a5?auto=format&fit=crop&w=1400&q=80",
    "schemes": "https://images.unsplash.com/photo-1452860606245-08befc0ff44b?auto=format&fit=crop&w=1400&q=80",
    "about": "https://images.unsplash.com/photo-1606293926075-69a00dbfde81?auto=format&fit=crop&w=1400&q=80",
    "map": "https://images.unsplash.com/photo-1605721911519-3dfeb3be25e7?auto=format&fit=crop&w=1400&q=80",
    "community": "https://images.unsplash.com/photo-1528459801416-a9e53bbf4e17?auto=format&fit=crop&w=1400&q=80",
    "business": "https://images.unsplash.com/photo-1610701596007-11502861dcfa?auto=format&fit=crop&w=1400&q=80",
    "planner": "https://images.unsplash.com/photo-1606293926075-69a00dbfde81?auto=format&fit=crop&w=1400&q=80",
}

CRAFT_IMAGES = {
    "Pattachitra": "https://images.unsplash.com/photo-1579783902614-a3fb3927b6a5?auto=format&fit=crop&w=1200&q=80",
    "Sambalpuri Ikat": "https://images.unsplash.com/photo-1610030469983-98e550d6193c?auto=format&fit=crop&w=1200&q=80",
    "Pipili Appliqué": "https://images.unsplash.com/photo-1528459801416-a9e53bbf4e17?auto=format&fit=crop&w=1200&q=80",
    "Silver Filigree": "https://images.unsplash.com/photo-1515562141207-7a88fb7ce338?auto=format&fit=crop&w=1200&q=80",
    "Terracotta": "https://images.unsplash.com/photo-1565193566173-7a0ee3dbe261?auto=format&fit=crop&w=1200&q=80",
    "Dhokra Metal Craft": "https://images.unsplash.com/photo-1605721911519-3dfeb3be25e7?auto=format&fit=crop&w=1200&q=80",
}

ARTISAN_IMAGES = {
    "Sasmita Das": CRAFT_IMAGES["Pattachitra"],
    "Ramesh Meher": "https://images.unsplash.com/photo-1606293926075-69a00dbfde81?auto=format&fit=crop&w=1200&q=80",
    "Priyanka Sahoo": "https://images.unsplash.com/photo-1452860606245-08befc0ff44b?auto=format&fit=crop&w=1200&q=80",
    "Bikash Mohanty": CRAFT_IMAGES["Silver Filigree"],
}

PRODUCT_IMAGES = {
    "Jagannath Pattachitra Panel": CRAFT_IMAGES["Pattachitra"],
    "Sambalpuri Stole": CRAFT_IMAGES["Sambalpuri Ikat"],
    "Pipili Decorative Umbrella": CRAFT_IMAGES["Pipili Appliqué"],
}

STORY_IMAGES = {
    "The living colours of Pattachitra": CRAFT_IMAGES["Pattachitra"],
    "Threads that tell Sambalpuri stories": CRAFT_IMAGES["Sambalpuri Ikat"],
    "Pipili: a celebration in fabric": CRAFT_IMAGES["Pipili Appliqué"],
}

CATALOGS = {
    "scene": SCENE_IMAGES,
    "craft": CRAFT_IMAGES,
    "artisan": ARTISAN_IMAGES,
    "product": PRODUCT_IMAGES,
    "story": STORY_IMAGES,
}


def media(kind, key=None, uploaded=None):
    """Prefer a maker's own upload, then a curated photo for known demo records."""
    if uploaded and "/static/uploads/" in str(uploaded):
        return uploaded
    curated = CATALOGS.get(kind, {}).get(key) if key else None
    if curated:
        return curated
    if kind == "craft":
        return CRAFT_IMAGES.get(key, SCENE_IMAGES["crafts"])
    if uploaded:
        return uploaded
    return SCENE_IMAGES.get(key) or SCENE_IMAGES["hero"]
