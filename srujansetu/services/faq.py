import re
import unicodedata
from dataclasses import dataclass
from functools import lru_cache


@dataclass(frozen=True)
class FAQ:
    question: str
    triggers: tuple
    answer: str
    actions: tuple = ()
    exact: bool = False


@lru_cache(maxsize=1)
def cached_faqs():
    return (
        FAQ(
            "Hi / hello",
            ("hi", "hii", "hello", "hellow", "hey", "namaskar", "good morning", "good evening"),
            "Namaskar! I’m the SrujanSetu Guide. Ask about Odisha crafts, or tell me if you want to find a maker, use the map, shop or join as an artisan or SHG.",
            (
                ("Explore crafts", "public.crafts"),
                ("Find artisans", "public.artisans"),
                ("Open the map", "public.planner"),
            ),
            exact=True,
        ),
        FAQ(
            "What is SrujanSetu?",
            ("what is srujansetu", "what does srujansetu do", "about this website", "about the website"),
            "SrujanSetu is an educational project that brings Odisha craft information, artisan and SHG profiles, a sample marketplace and map into one place.",
            (("About SrujanSetu", "public.about"),),
        ),
        FAQ(
            "What can I ask the guide?",
            ("what can you do", "what can i ask", "help me", "help"),
            "I can answer common questions about this site and Odisha craft data, then link you to artisans, the map, marketplace, stories, community or scheme information.",
            (
                ("Explore crafts", "public.crafts"),
                ("Find artisans", "public.artisans"),
                ("Open the map", "public.planner"),
            ),
        ),
        FAQ(
            "What is an SHG?",
            ("what is an shg", "what does shg mean", "self help group"),
            "SHG stands for self-help group. This site is designed to help artisan and SHG makers share their work and reach customers.",
            (("Visit the marketplace", "public.marketplace"), ("Join as a maker", "artisan.artisan_register")),
        ),
        FAQ(
            "How do I find artisans near me?",
            ("find artisans", "find artisan", "find an artisan", "find makers", "near me", "nearby artisan", "artisan map"),
            "Browse profiles by craft or district, or open the Odisha map. Exact pins appear only when a maker has chosen to publish coordinates for a public workshop or shop.",
            (("Browse artisans", "public.artisans"), ("Open the map", "public.planner")),
        ),
        FAQ(
            "Why are there no pins on the map?",
            ("why no pins", "no pins", "no locations", "map is empty", "map pins"),
            "The map does not guess or invent maker locations. A profile appears as a pin only after its owner adds both latitude and longitude to their public profile.",
            (("Open the map", "public.planner"), ("Maker sign in", "artisan.artisan_login")),
        ),
        FAQ(
            "How do I register as an artisan or SHG?",
            ("register", "create account", "sign up", "join as an artisan", "join as a maker"),
            "Create a maker account with your name, email, craft or product category and district. After registration, edit your profile and add a public location only if you want it shown on the map.",
            (("Create a maker account", "artisan.artisan_register"),),
        ),
        FAQ(
            "How do I add or update my products?",
            ("add product", "list product", "sell my", "sell products", "manage products"),
            "Sign in to your maker account, open your dashboard and choose My Products. You can add a listing, update it or remove it later.",
            (("Maker sign in", "artisan.artisan_login"), ("Open the marketplace", "public.marketplace")),
        ),
        FAQ(
            "How do I add a product photo?",
            ("product photo", "upload product image", "add product image"),
            "Sign in and open My Products, then add or edit a listing and choose a PNG, JPG, GIF or WEBP image under 5 MB.",
            (("Maker sign in", "artisan.artisan_login"),),
        ),
        FAQ(
            "Can I buy products on this site?",
            ("buy online", "place an order", "checkout", "purchase product", "buy product"),
            "You can add products to a cart and submit a demo order request from a customer account. This site does not process payment or arrange delivery; contact the maker directly to complete a real purchase.",
            (
                ("Browse the marketplace", "public.marketplace"),
                ("View your cart", "shop.cart"),
                ("Create a customer account", "shop.customer_register"),
                ("Customer sign in", "shop.customer_login"),
            ),
        ),
        FAQ(
            "How can I contact a maker?",
            ("contact artisan", "contact maker", "message an artisan", "contact seller"),
            "Direct messaging and verified contact details are not available in this demo yet. Product listings are samples, not live offers.",
            (("Browse artisan profiles", "public.artisans"), ("Visit the marketplace", "public.marketplace")),
        ),
        FAQ(
            "Do I have to pay to register?",
            ("registration fee", "pay to register", "is registration free", "cost to join"),
            "This demonstration account registration does not ask for payment. Before a real launch, publish verified terms and privacy information for makers.",
            (("Create a maker account", "artisan.artisan_register"),),
        ),
        FAQ(
            "Are the government schemes verified?",
            ("are schemes verified", "official scheme", "apply for scheme", "scheme eligibility"),
            "No. Scheme cards are illustrative project content, not verified or live government guidance. Confirm current eligibility and application details with the official department.",
            (("Open scheme information", "public.schemes"),),
        ),
        FAQ(
            "How can I change my profile or map location?",
            ("edit my profile", "update my profile", "change my location", "add map location", "add map pin"),
            "Sign in to the maker portal and open Edit profile. Enter both latitude and longitude for a public pin, or leave both empty to remove it. Only publish a workshop or shop address you are comfortable sharing.",
            (("Maker sign in", "artisan.artisan_login"), ("Open the map", "public.planner")),
        ),
        FAQ(
            "Can I reset my password?",
            ("forgot password", "reset password", "change password"),
            "Self-service password recovery is not available in this demo yet. Contact the site administrator; do not share your password in chat.",
            (("Open the maker portal", "artisan.artisan_login"),),
        ),
        FAQ(
            "Are the assistant answers generated by AI?",
            ("are you ai", "generative ai", "how do you answer", "chatbot"),
            "The guide, sell assistant and story weaver answer from the records on this site in English, Odia and Hindi. They do not send your question to an external AI service.",
            (("Browse the FAQ", "public.assistant"), ("Explore crafts", "public.crafts")),
        ),
        FAQ(
            "Where is Odisha?",
            ("where is odisha", "which state is odisha", "odisha location"),
            "Odisha is a state on the eastern coast of India, along the Bay of Bengal. This site focuses on its craft communities and maker profiles.",
            (("Explore the Odisha map", "public.planner"),),
        ),
        FAQ(
            "What crafts can I explore?",
            ("what crafts", "which crafts", "crafts on this site", "crafts are featured", "crafts available"),
            "The directory covers Pattachitra, Sambalpuri Ikat, Pipili Appliqué, Silver Filigree, Terracotta and Dhokra Metal Craft. Open a craft to learn about its techniques and region.",
            (("Browse Odisha crafts", "public.crafts"),),
        ),
        FAQ(
            "How do I search products by craft?",
            ("search products", "find products", "browse products", "shop by category", "product category"),
            "Open the SHG Marketplace and use Shop by category to filter sample listings. Product cards show the maker, craft, district and listed price; confirm availability with the maker.",
            (("Visit the marketplace", "public.marketplace"),),
        ),
        FAQ(
            "Can I place a real order?",
            ("real order", "real purchase", "is this a real shop", "place a real order"),
            "The marketplace is a demonstration. You can submit a demo order request with a customer account, but checkout does not process payment or arrange delivery.",
            (("Visit the marketplace", "public.marketplace"), ("Create a customer account", "shop.customer_register")),
        ),
        FAQ(
            "Do you deliver products?",
            ("delivery", "deliver products", "shipping", "ship orders", "delivery available", "can you deliver", "do you deliver"),
            "Delivery is not enabled on this demonstration site. A submitted checkout is only a demo order request; contact a maker directly to discuss a real purchase.",
            (("Visit the marketplace", "public.marketplace"),),
        ),
        FAQ(
            "How do I create a customer account?",
            ("customer account", "buyer account", "track my order", "order status", "my orders"),
            "Choose Create customer account in the marketplace and provide your name, email and password. Sign in afterward to submit and track demo order requests.",
            (("Create a customer account", "shop.customer_register"), ("Customer sign in", "shop.customer_login")),
        ),
        FAQ(
            "How do I share a note with the community?",
            ("community note", "community message", "community post", "share a note", "share a message", "post a message"),
            "Open Community, enter your name and message in Share a community note, then choose Post message. Community notes are public, so do not include private information.",
            (("Visit the community", "public.community"),),
        ),
        FAQ(
            "Where can I read craft stories?",
            ("read craft stories", "craft stories", "stories about crafts", "how crafts are made"),
            "Open Craft Stories to browse saved stories or create a story about a listed craft. You can choose a making, maker or gift focus and select English, Odia or Hindi.",
            (("Read craft stories", "public.stories"),),
        ),
        FAQ(
            "Can I change the guide language?",
            ("change language", "switch language", "guide language", "what languages", "speak odia", "speak hindi"),
            "Choose English, Odia or Hindi from the language selector above the chat. The guide's answers and spoken responses use the selected language.",
            (("Ask another question", "public.assistant"),),
        ),
        FAQ(
            "Thank you",
            ("thanks", "thank you", "thankyou"),
            "You’re welcome! I’m here to help you explore crafts, find makers or navigate the site.",
            (("Explore crafts", "public.crafts"), ("Find artisans", "public.artisans")),
            exact=True,
        ),
        FAQ(
            "Goodbye",
            ("bye", "goodbye", "see you"),
            "Dhanyabad for visiting SrujanSetu. Come back any time to explore Odisha’s makers and crafts.",
            (("Return home", "public.home"),),
            exact=True,
        ),
    )


def normalize_question(message):
    normalized = unicodedata.normalize("NFKC", message).casefold()
    normalized = re.sub(r"(.)\1{2,}", r"\1\1", normalized)
    normalized = re.sub(r"[^a-z0-9\s]", " ", normalized)
    normalized = " ".join(normalized.split())
    spelling_variants = {
        "hii": "hi",
        "hiii": "hi",
        "hellow": "hello",
        "helloo": "hello",
        "helo": "hello",
        "thnks": "thanks",
        "pls": "please",
        "plz": "please",
    }
    return " ".join(spelling_variants.get(word, word) for word in normalized.split())


def find_faq(message):
    normalized = normalize_question(message)
    greeting_words = {"hi", "hello", "hey", "namaskar", "there", "and"}
    words = normalized.split()
    greeted = False
    while words and words[0] in greeting_words:
        greeted = True
        words.pop(0)
    normalized = " ".join(words)

    matches = []
    for faq in cached_faqs():
        if normalized == normalize_question(faq.question):
            return faq
        if faq.exact:
            if normalized in faq.triggers:
                return faq
            continue
        matching_triggers = [
            trigger for trigger in faq.triggers
            if re.search(rf"(?<!\w){re.escape(trigger)}(?!\w)", normalized)
        ]
        if matching_triggers:
            matches.append((max(map(len, matching_triggers)), faq))
    if greeted and not normalized:
        return cached_faqs()[0]
    return max(matches, key=lambda match: match[0])[1] if matches else None
