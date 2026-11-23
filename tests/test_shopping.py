import re
import unittest
from decimal import Decimal
import json

from srujansetu import create_app
from srujansetu.extensions import db
from srujansetu.models import (
    AppMetadata,
    Artisan,
    ArtisanAccount,
    CustomerAccount,
    CustomerOrder,
    Product,
)
from srujansetu.services.data_store import seed_demo_data


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

    def test_ajax_add_to_cart_returns_cart_count_without_redirecting(self):
        marketplace = self.client.get("/marketplace")
        response = self.client.post(
            "/shop/cart/add/1",
            data={"_csrf": self.csrf_token(marketplace), "quantity": "2"},
            headers={"X-Requested-With": "XMLHttpRequest"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["cart_count"], 2)
        self.assertIn(b"added to your cart", response.get_json()["message"].encode())

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

    def test_navigation_exposes_maker_admin_and_customer_logout(self):
        response = self.client.get("/marketplace")
        home_page = self.client.get("/")
        self.assertNotIn(b'id="backTab"', home_page.data)
        self.assertIn(b'id="backTab"', response.data)
        self.assertIn(b'>\xe2\x86\x90</button>', response.data)
        self.assertIn(b'href="/artisan/register"', response.data)
        self.assertIn(b'href="/artisan/login"', response.data)
        self.assertIn(b'href="/admin"', response.data)

        with self.app.app_context():
            db.session.add(CustomerAccount(
                id="customer-1",
                name="Asha Buyer",
                email="asha@example.com",
                password_hash=None,
            ))
            db.session.commit()
        with self.client.session_transaction() as browser_session:
            browser_session["role"] = "customer"
            browser_session["customer_user_id"] = "customer-1"
        response = self.client.get("/marketplace")
        self.assertIn(b'action="/shop/logout"', response.data)
        self.assertIn(b"Sign out", response.data)

    def test_map_has_current_location_control_and_published_artisan_pins(self):
        with self.app.app_context():
            db.session.add(Artisan(
                id=1,
                name="Sasmita Das",
                craft="Pattachitra",
                district="Puri",
                latitude=19.8,
                longitude=85.8,
            ))
            db.session.commit()
        response = self.client.get("/planner")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'id="locateMe"', response.data)
        self.assertIn(b'data-lat="19.8"', response.data)
        self.assertIn(b"Your location is used only in this browser", response.data)

    def test_seeded_shg_map_markers_are_labeled_as_approximate(self):
        with self.app.app_context():
            seed_demo_data()

        response = self.client.get("/planner")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Sample Pipili Appliqu", response.data)
        self.assertIn(b"Approximate sample area", response.data)
        self.assertIn(b'"maker_type": "SHG"', response.data)
        self.assertIn(b'"approximate_location": true', response.data)

    def test_admin_can_monitor_customer_order_requests(self):
        with self.app.app_context():
            db.session.add(CustomerOrder(
                id="order-12345678",
                customer_id="buyer-1",
                customer_name="Asha Buyer",
                phone="9876543210",
                address="Puri, Odisha",
                items_json=json.dumps([{
                    "name": "Pattachitra Panel",
                    "artisan": "Sasmita Das",
                    "quantity": 1,
                    "unit_price": "₹1,800.00",
                    "line_total": "₹1,800.00",
                }]),
                total_price=Decimal("1800.00"),
            ))
            db.session.commit()
        with self.client.session_transaction() as browser_session:
            browser_session["role"] = "admin"
            browser_session["admin_user"] = "test-admin"

        response = self.client.get("/admin/orders")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Customer order requests", response.data)
        self.assertIn(b"Pattachitra Panel", response.data)
        self.assertIn(b"9876543210", response.data)
        dashboard = self.client.get("/admin/dashboard")
        self.assertEqual(dashboard.status_code, 200)
        self.assertIn(b"Seller analytics", dashboard.data)
        self.assertIn(b"Most requested products", dashboard.data)
        self.assertIn(b'id="adminAnalyticsData"', dashboard.data)

    def test_maker_dashboard_shows_only_its_demo_order_analytics(self):
        with self.app.app_context():
            db.session.add(ArtisanAccount(
                id="maker-1",
                name="Sasmita Das",
                email="maker@example.com",
                password_hash="unused",
            ))
            db.session.add(Artisan(
                id=1,
                account_id="maker-1",
                name="Sasmita Das",
                craft="Pattachitra",
                district="Puri",
            ))
            db.session.add(Product(
                id=2,
                owner_id="maker-1",
                name="Painted Bookmark",
                craft="Pattachitra",
                price="₹500",
                artisan="Sasmita Das",
                district="Puri",
            ))
            db.session.add(CustomerOrder(
                id="maker-order-1",
                customer_id="buyer-1",
                customer_name="Asha Buyer",
                phone="9876543210",
                address="Puri, Odisha",
                items_json=json.dumps([{
                    "product_id": 2,
                    "owner_id": "maker-1",
                    "name": "Painted Bookmark",
                    "artisan": "Sasmita Das",
                    "quantity": 2,
                    "unit_price": "₹500.00",
                    "line_total": "₹1,000.00",
                }]),
                total_price=Decimal("1000.00"),
            ))
            db.session.commit()
        with self.client.session_transaction() as browser_session:
            browser_session["role"] = "artisan"
            browser_session["artisan_user_id"] = "maker-1"

        response = self.client.get("/artisan/dashboard")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Marketplace activity", response.data)
        self.assertIn(b"Painted Bookmark", response.data)
        self.assertIn(b"2</strong>", response.data)
        self.assertIn(b"1,000.00", response.data)
        self.assertIn(b'id="sellerAnalyticsData"', response.data)

    def test_ajax_add_to_cart_returns_json_without_redirect(self):
        marketplace = self.client.get("/marketplace")
        cart_response = self.client.post(
            "/shop/cart/add/1",
            data={"_csrf": self.csrf_token(marketplace), "quantity": "3"},
            headers={"X-Requested-With": "XMLHttpRequest"},
        )
        self.assertEqual(cart_response.status_code, 200)
        data = cart_response.get_json()
        self.assertEqual(data["status"], "success")
        self.assertEqual(data["cart_count"], 3)
        self.assertIn("added to your cart", data["message"])

    def test_admin_dashboard_includes_chart_data(self):
        with self.client.session_transaction() as browser_session:
            browser_session["role"] = "admin"
            browser_session["admin_user"] = "admin@example.com"

        response = self.client.get("/admin/dashboard")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'id="adminAnalyticsData"', response.data)
        self.assertIn(b'sellerOverviewChart', response.data)
        self.assertIn(b'sellerTypeChart', response.data)
        self.assertIn(b'sellerDistrictChart', response.data)

    def test_selected_language_is_used_across_public_customer_and_portal_pages(self):
        with self.client.session_transaction() as browser_session:
            browser_session["lang"] = "hi"

        expected_text = {
            "/marketplace": "बाज़ार",
            "/shop/login": "साइन इन",
            "/artisan/login": "कारीगर कार्यक्षेत्र",
            "/admin/setup": "पहली बार सेटअप",
        }
        for path, phrase in expected_text.items():
            with self.subTest(path=path):
                response = self.client.get(path)
                self.assertEqual(response.status_code, 200)
                self.assertIn(b'<html lang="hi">', response.data)
                self.assertIn(phrase.encode(), response.data)

    def test_seed_adds_photo_to_matching_legacy_sample_without_overwriting_fields(self):
        with self.app.app_context():
            product = db.session.get(Product, 1)
            product.name = "Jagannath Pattachitra Panel"
            product.description = "Keep this existing description."
            db.session.add(AppMetadata(key="demo_data_seeded", value="true"))
            db.session.commit()

            seed_demo_data()

            product = db.session.get(Product, 1)
            self.assertTrue(product.image.startswith("https://images.unsplash.com/"))
            self.assertEqual(product.description, "Keep this existing description.")


if __name__ == "__main__":
    unittest.main()
