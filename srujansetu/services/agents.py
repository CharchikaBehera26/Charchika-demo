import re

from flask import url_for

from .data_store import read_data
from .gallery import media
from .i18n import CRAFT_TEXT, normalize_lang


def _price_value(product):
    digits = re.sub(r"[^\d]", "", str(product.get("price", "")))
    return int(digits) if digits else None


def _budget(message):
    amounts = [int(match) for match in re.findall(r"\d{3,6}", message)]
    return min(amounts) if amounts else None


def _mentions(text, *phrases):
    folded = text.casefold()
    return any(phrase.casefold() in folded for phrase in phrases)


def _matching_products(message, products):
    folded = message.casefold()
    matches = []
    for product in products:
        haystack = " ".join(
            str(product.get(key, ""))
            for key in ("name", "craft", "artisan", "district", "description")
        ).casefold()
        craft_words = [
            word.casefold()
            for word in str(product.get("craft", "")).split()
            if len(word) > 3
        ]
        if (
            str(product.get("name", "")).casefold() in folded
            or str(product.get("craft", "")).casefold() in folded
            or any(word in folded for word in craft_words)
            or any(word in folded for word in haystack.split() if len(word) > 4)
        ):
            matches.append(product)
    return matches


def sell_reply(message, lang):
    lang = normalize_lang(lang)
    products = read_data("products")
    if not products:
        text = {
            "en": "The sample marketplace has no listings yet. A maker can add one after signing in.",
            "hi": "नमूना बाज़ार में अभी कोई सूची नहीं है। साइन इन के बाद कारीगर एक सूची जोड़ सकता है।",
            "or": "ନମୁନା ବଜାରରେ ଏଯାଏଁ କୌଣସି ତାଲିକା ନାହିଁ। ସାଇନ୍ ଇନ୍ ପରେ କାରିଗର ଏକ ତାଲିକା ଯୋଡ଼ିପାରିବ।",
        }[lang]
        return text, [], [{"label": {
            "en": "Open the marketplace",
            "hi": "बाज़ार खोलें",
            "or": "ବଜାର ଖୋଲନ୍ତୁ",
        }[lang], "url": url_for("public.marketplace")}]

    budget = _budget(message)
    matched = _matching_products(message, products)
    pool = matched or products
    if budget is not None:
        affordable = [item for item in pool if (_price_value(item) or 0) <= budget]
        if not affordable:
            affordable = sorted(pool, key=lambda item: _price_value(item) or 0)[:2]
            limited = True
        else:
            limited = False
    else:
        affordable = pool[:3]
        limited = False

    wants_pitch = _mentions(
        message,
        "pitch", "caption", "describe", "write", "copy", "sell my",
        "कैप्शन", "लिख", "विवरण",
        "କ୍ୟାପସନ", "ଲେଖ", "ବିବରଣ",
    )
    chosen = affordable[0]
    if wants_pitch:
        text = _pitch(chosen, lang)
        picks = [chosen]
    else:
        text = _recommend(affordable[:3], lang, budget, limited, bool(matched))
        picks = affordable[:3]

    actions = [
        {"label": {"en": "Open the marketplace", "hi": "बाज़ार खोलें", "or": "ବଜାର ଖୋଲନ୍ତୁ"}[lang], "url": url_for("public.marketplace")},
        {"label": {"en": "Meet the makers", "hi": "कारीगरों से मिलें", "or": "କାରିଗରଙ୍କୁ ଭେଟନ୍ତୁ"}[lang], "url": url_for("public.artisans")},
    ]
    return text, picks, actions


def _pitch(product, lang):
    name = product.get("name", "This piece")
    artisan = product.get("artisan", "a local maker")
    district = product.get("district", "Odisha")
    craft = product.get("craft", "handmade craft")
    price = product.get("price", "")
    description = product.get("description", "")
    if lang == "hi":
        return (
            f"{name} — {district} के {artisan} का {craft} काम। {description} "
            f"प्रदर्शन मूल्य {price}। यह हाथ की बनी वस्तु है, कारखाने की प्रति नहीं। "
            "यह सूची नमूना है और ऑनलाइन भुगतान नहीं लेती।"
        )
    if lang == "or":
        return (
            f"{name} — {district}ର {artisan}ଙ୍କ {craft} କାମ। {description} "
            f"ପ୍ରଦର୍ଶନ ମୂଲ୍ୟ {price}। ଏହା ହାତରେ ତିଆରି, କାରଖାନା ନକଲ ନୁହେଁ। "
            "ଏହି ତାଲିକା ନମୁନା ଓ ଅନଲାଇନ୍ ପେମେଣ୍ଟ ନେଏ ନାହିଁ।"
        )
    return (
        f"{name} by {artisan} of {district}. {description} "
        f"Made in the {craft} tradition. Demonstration price {price}. "
        "A handmade piece with a maker’s name attached, not a factory copy. "
        "This listing is a sample and does not take payment."
    )


def _recommend(products, lang, budget, limited, matched):
    lines = []
    for product in products:
        lines.append(
            f"{product.get('name')} — {product.get('price')} — "
            f"{product.get('artisan')}, {product.get('district')}"
        )
    listing = " ".join(lines)
    if lang == "hi":
        if limited and budget:
            lead = f"{budget} तक कोई सटीक सूची नहीं मिली। सबसे नज़दीकी प्रदर्शन सूचियाँ ये हैं:"
        elif matched:
            lead = "आपकी बात से ये प्रदर्शन सूचियाँ मेल खाती हैं:"
        else:
            lead = "नमूना बाज़ार से ये सूचियाँ देख सकते हैं:"
        return f"{lead} {listing} भुगतान इस डेमो में नहीं होता।"
    if lang == "or":
        if limited and budget:
            lead = f"{budget} ଭିତରେ ସଠିକ୍ ତାଲିକା ମିଳିଲା ନାହିଁ। ସବୁଠୁ ପାଖାପାଖି ପ୍ରଦର୍ଶନ ତାଲିକା:"
        elif matched:
            lead = "ଆପଣଙ୍କ କଥା ସହ ଏହି ପ୍ରଦର୍ଶନ ତାଲିକା ମିଳେ:"
        else:
            lead = "ନମୁନା ବଜାରରୁ ଏହି ତାଲିକା ଦେଖିପାରିବେ:"
        return f"{lead} {listing} ଏହି ଡେମୋରେ ପେମେଣ୍ଟ ହୁଏ ନାହିଁ।"
    if limited and budget:
        lead = f"Nothing in the sample marketplace is at or under {budget}. The closest demonstration listings are:"
    elif matched:
        lead = "These demonstration listings match what you asked:"
    else:
        lead = "Here are demonstration listings from the sample marketplace:"
    return f"{lead} {listing} This demo does not take payment."


def generate_story(craft_name, lang, focus):
    lang = normalize_lang(lang)
    focus = focus if focus in {"making", "maker", "gift"} else "making"
    crafts = read_data("crafts")
    craft = next(
        (item for item in crafts if item.get("name", "").casefold() == craft_name.casefold()),
        None,
    )
    if craft is None:
        return None

    name = craft.get("name", "This craft")
    region = craft.get("region", "Odisha")
    description = craft.get("description", "")
    blurb = CRAFT_TEXT.get(name, {}).get(lang) if lang != "en" else (
        f"{name} is still practised in {region}. {description}"
    )
    artisans = [
        item for item in read_data("artisans")
        if name.casefold() in str(item.get("craft", "")).casefold()
    ]
    products = [
        item for item in read_data("products")
        if name.casefold() in str(item.get("craft", "")).casefold()
    ]
    artisan = artisans[0] if artisans else None
    product = products[0] if products else None

    if lang == "hi":
        title, paragraphs = _story_hi(name, region, blurb, description, artisan, product, focus)
    elif lang == "or":
        title, paragraphs = _story_or(name, region, blurb, description, artisan, product, focus)
    else:
        title, paragraphs = _story_en(name, region, blurb, description, artisan, product, focus)

    return {
        "title": title,
        "paragraphs": paragraphs,
        "image": media("craft", name),
        "craft": name,
        "category": region,
    }


def _story_en(name, region, blurb, description, artisan, product, focus):
    if focus == "maker" and artisan:
        title = f"{artisan.get('name')} and the {name} of {region}"
        opening = (
            f"{artisan.get('name')} of {artisan.get('district', region)} has spent "
            f"{artisan.get('experience', 'many years')} with {name}. {artisan.get('bio', '')}"
        )
    elif focus == "gift":
        title = f"A {name} gift from {region}"
        opening = f"Someone looking for a gift from {region} often begins with {name}. {blurb}"
    else:
        title = f"How {name} is still made in {region}"
        opening = blurb
    middle = f"The work asks for patience. {description}"
    if product:
        closing = (
            f"On SrujanSetu, a sample listing called {product.get('name')} "
            f"({product.get('price')}) shows how the tradition can enter a home. "
            "The listing is a demonstration, not a live shop."
        )
    elif artisan:
        closing = f"Makers such as {artisan.get('name')} carry the practice forward in {artisan.get('district', region)}."
    else:
        closing = f"The tradition continues with the makers of {region}."
    return title, [opening, middle, closing]


def _story_hi(name, region, blurb, description, artisan, product, focus):
    if focus == "maker" and artisan:
        title = f"{artisan.get('name')} और {region} का {name}"
        opening = (
            f"{artisan.get('district', region)} के {artisan.get('name')} ने {name} में "
            f"{artisan.get('experience', 'कई वर्ष')} दिए हैं। {artisan.get('bio', '')}"
        )
    elif focus == "gift":
        title = f"{region} से एक {name} उपहार"
        opening = f"{region} से उपहार खोजने वाला अक्सर {name} से शुरुआत करता है। {blurb}"
    else:
        title = f"{region} में {name} आज भी कैसे बनता है"
        opening = blurb
    middle = f"इस काम में धैर्य लगता है। {description}"
    if product:
        closing = (
            f"श्रीजनसेतु पर {product.get('name')} ({product.get('price')}) नाम की एक नमूना सूची "
            "दिखाती है कि यह परंपरा घर तक कैसे पहुँच सकती है। यह सूची प्रदर्शन है, जीवित दुकान नहीं।"
        )
    elif artisan:
        closing = f"{artisan.get('name')} जैसे कारीगर {artisan.get('district', region)} में इस काम को आगे बढ़ाते हैं।"
    else:
        closing = f"यह परंपरा {region} के कारीगरों के साथ जारी है।"
    return title, [opening, middle, closing]


def _story_or(name, region, blurb, description, artisan, product, focus):
    if focus == "maker" and artisan:
        title = f"{artisan.get('name')} ଓ {region}ର {name}"
        opening = (
            f"{artisan.get('district', region)}ର {artisan.get('name')} {name}ରେ "
            f"{artisan.get('experience', 'ଅନେକ ବର୍ଷ')} ଦେଇଛନ୍ତି। {artisan.get('bio', '')}"
        )
    elif focus == "gift":
        title = f"{region}ରୁ ଏକ {name} ଉପହାର"
        opening = f"{region}ରୁ ଉପହାର ଖୋଜୁଥିବା ବ୍ୟକ୍ତି ପ୍ରାୟ {name}ରୁ ଆରମ୍ଭ କରେ। {blurb}"
    else:
        title = f"{region}ରେ {name} ଆଜି ବି କିପରି ତିଆରି ହୁଏ"
        opening = blurb
    middle = f"ଏହି କାମ ଧୈର୍ଯ୍ୟ ମାଗେ। {description}"
    if product:
        closing = (
            f"ଶ୍ରୁଜନସେତୁରେ {product.get('name')} ({product.get('price')}) ନାମକ ଏକ ନମୁନା ତାଲିକା "
            "ଦେଖାଏ ଯେ ଏହି ପରମ୍ପରା ଘରକୁ କିପରି ଆସିପାରେ। ଏହି ତାଲିକା ପ୍ରଦର୍ଶନ, ସଚଳ ଦୋକାନ ନୁହେଁ।"
        )
    elif artisan:
        closing = f"{artisan.get('name')} ପରି କାରିଗର {artisan.get('district', region)}ରେ ଏହି କାମକୁ ଆଗକୁ ନେଉଛନ୍ତି।"
    else:
        closing = f"ଏହି ପରମ୍ପରା {region}ର କାରିଗରଙ୍କ ସହ ଜାରି ଅଛି।"
    return title, [opening, middle, closing]
