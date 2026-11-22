import re
import unittest

from srujansetu import create_app
from srujansetu.extensions import db
from srujansetu.models import CustomerOrder, Product


class ShoppingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = create_app({
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite://",
            "SECRET_KEY": "test-secret",
        })

    def setUp(self):
        with self.app.app_context():
            db.drop_all()
            db.create_all()
            db.session.add(Product(
                id=1,
                name="Pattachitra Panel",
                craft="Pattachitra",
                price="₹1,800",
                artisan="Sasmita Das",
                district="Puri",
                description="Hand-painted artwork.",
                emoji="🖼️",
            ))
            db.session.commit()
        self.client = self.app.test_client()

    def csrf_token(self, response):
        match = re.search(rb'name="_csrf" value="([^"]+)"', response.data)
        self.assertIsNotNone(match)
        return match.group(1).decode()

    def test_guest_cart_survives_signup_and_checkout(self):
        marketplace = self.client.get("/marketplace")
        cart_add = self.client.post(
            "/shop/cart/add/1",
            data={"_csrf": self.csrf_token(marketplace), "quantity": "2"},
        )
        self.assertEqual(cart_add.status_code, 302)
        cart_page = self.client.get("/shop/cart")
        self.assertIn("₹3,600.00".encode(), cart_page.data)

        checkout = self.client.get("/shop/checkout")
        self.assertEqual(checkout.status_code, 302)
        login_page = self.client.get(checkout.location)
        self.assertIn(b"/shop/register?next=/shop/checkout", login_page.data)
        register_page = self.client.get(
            "/shop/register?next=%2Fshop%2Fcheckout"
        )
        registration = self.client.post(
            "/shop/register?next=/shop/checkout",
            data={
                "_csrf": self.csrf_token(register_page),
                "name": "Asha Buyer",
                "email": "asha@example.com",
                "password": "a-strong-password",
                "confirm": "a-strong-password",
            },
        )
        self.assertEqual(registration.status_code, 302)
        self.assertEqual(registration.location, "/shop/checkout")

        checkout_page = self.client.get("/shop/checkout")
        self.assertEqual(checkout_page.status_code, 200)
        order_response = self.client.post(
            "/shop/checkout",
            data={
                "_csrf": self.csrf_token(checkout_page),
                "name": "Asha Buyer",
                "phone": "9876543210",
                "address": "Puri, Odisha",
            },
        )
        self.assertEqual(order_response.status_code, 302)
        order_page = self.client.get(order_response.location)
        self.assertEqual(order_page.status_code, 200)
        self.assertIn(b"No payment or delivery has been arranged", order_page.data)
        self.assertIn(b"Pattachitra Panel", order_page.data)
        self.assertEqual(self.client.get("/shop/orders").status_code, 200)

        logout = self.client.post(
            "/shop/logout",
            data={"_csrf": self.csrf_token(order_page)},
        )
        self.assertEqual(logout.status_code, 302)
        login_page = self.client.get("/shop/login")
        login = self.client.post(
            "/shop/login",
            data={
                "_csrf": self.csrf_token(login_page),
                "email": "asha@example.com",
                "password": "a-strong-password",
            },
        )
        self.assertEqual(login.status_code, 302)
        self.assertEqual(self.client.get("/shop/orders").status_code, 200)

        with self.app.app_context():
            order = db.session.query(CustomerOrder).one()
            self.assertEqual(str(order.total_price), "3600.00")

    def test_invalid_credentials_and_csrf_are_rejected(self):
        login_page = self.client.get("/shop/login")
        token = self.csrf_token(login_page)
        self.assertEqual(
            self.client.post("/shop/login", data={"email": "x@example.com"}).status_code,
            400,
        )
        response = self.client.post(
            "/shop/login",
            data={
                "_csrf": token,
                "email": "nobody@example.com",
                "password": "incorrect",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Incorrect email or password.", response.data)

    def test_cart_quantity_can_be_updated_or_removed(self):
        marketplace = self.client.get("/marketplace")
        token = self.csrf_token(marketplace)
        self.client.post(
            "/shop/cart/add/1",
            data={"_csrf": token, "quantity": "1"},
        )
        cart_page = self.client.get("/shop/cart")
        self.client.post(
            "/shop/cart/update",
            data={
                "_csrf": self.csrf_token(cart_page),
                "product_id": "1",
                "quantity": "3",
            },
        )
        self.assertIn("₹5,400.00".encode(), self.client.get("/shop/cart").data)
        cart_page = self.client.get("/shop/cart")
        self.client.post(
            "/shop/cart/update",
            data={
                "_csrf": self.csrf_token(cart_page),
                "product_id": "1",
                "quantity": "0",
            },
        )
        self.assertIn(b"Your cart is empty", self.client.get("/shop/cart").data)

    def test_invalid_product_price_cannot_be_submitted_as_an_order(self):
        registration_page = self.client.get("/shop/register")
        self.client.post(
            "/shop/register",
            data={
                "_csrf": self.csrf_token(registration_page),
                "name": "Asha Buyer",
                "email": "asha@example.com",
                "password": "a-strong-password",
                "confirm": "a-strong-password",
            },
        )
        marketplace = self.client.get("/marketplace")
        self.client.post(
            "/shop/cart/add/1",
            data={"_csrf": self.csrf_token(marketplace), "quantity": "1"},
        )
        with self.app.app_context():
            product = db.session.get(Product, 1)
            product.price = "Price on request"
            db.session.commit()

        checkout_page = self.client.get("/shop/checkout")
        response = self.client.post(
            "/shop/checkout",
            data={
                "_csrf": self.csrf_token(checkout_page),
                "name": "Asha Buyer",
                "phone": "9876543210",
                "address": "Puri, Odisha",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"invalid price and cannot be ordered", response.data)
        with self.app.app_context():
            self.assertEqual(db.session.query(CustomerOrder).count(), 0)


if __name__ == "__main__":
    unittest.main()
