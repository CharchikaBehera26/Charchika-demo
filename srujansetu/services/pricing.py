from decimal import Decimal, InvalidOperation


def product_price(value):
    cleaned = str(value).replace("₹", "").replace("INR", "").replace(",", "").strip()
    try:
        amount = Decimal(cleaned)
    except InvalidOperation:
        return None
    if (
        not amount.is_finite()
        or amount <= 0
        or amount > Decimal("9999999999.99")
        or amount.as_tuple().exponent < -2
    ):
        return None
    return amount.quantize(Decimal("0.01"))


def effective_product_price(product):
    regular_price = product_price(product.get("price", ""))
    deal_value = str(product.get("deal_price", "")).strip()
    if not deal_value:
        return regular_price
    deal_price = product_price(deal_value)
    if regular_price is None or deal_price is None or deal_price >= regular_price:
        return None
    return deal_price


def has_valid_deal(product):
    deal_value = str(product.get("deal_price", "")).strip()
    if not deal_value:
        return True
    regular_price = product_price(product.get("price", ""))
    deal_price = product_price(deal_value)
    return (
        regular_price is not None
        and deal_price is not None
        and deal_price < regular_price
    )
