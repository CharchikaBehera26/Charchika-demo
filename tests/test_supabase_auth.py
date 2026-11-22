import base64
import hashlib
import unittest
from urllib.parse import parse_qs, urlsplit
from unittest.mock import patch

from srujansetu import create_app
from srujansetu.extensions import db
from srujansetu.models import AdminAccount, ArtisanAccount, CustomerAccount
from werkzeug.security import generate_password_hash


class SupabaseGoogleAuthTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = create_app({
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite://",
            "SECRET_KEY": "test-secret",
            "SUPABASE_URL": "https://project.supabase.co",
            "SUPABASE_ANON_KEY": "sb_publishable_test",
            "PUBLIC_BASE_URL": "https://shop.example",
            "GOOGLE_ADMIN_EMAILS": "admin@example.com",
        })

    def setUp(self):
        with self.app.app_context():
            db.drop_all()
            db.create_all()
        self.client = self.app.test_client()

    def test_pkce_flow_creates_customer_and_preserves_return_path(self):
        start = self.client.get("/shop/google/login?next=/shop/checkout")
        self.assertEqual(start.status_code, 302)
        authorization = urlsplit(start.location)
        query = parse_qs(authorization.query)
        self.assertEqual(authorization.netloc, "project.supabase.co")
        self.assertEqual(query["provider"], ["google"])
        self.assertEqual(query["redirect_to"], [
            "https://shop.example/shop/google/callback"
        ])
        self.assertEqual(query["code_challenge_method"], ["s256"])

        with self.client.session_transaction() as browser_session:
            verifier = browser_session["supabase_oauth_verifier"]
            browser_session["cart"] = {"1": 2}
        expected_challenge = base64.urlsafe_b64encode(
            hashlib.sha256(verifier.encode("ascii")).digest()
        ).rstrip(b"=").decode("ascii")
        self.assertEqual(query["code_challenge"], [expected_challenge])

        auth_result = {
            "access_token": "temporary-access-token",
            "user": {
                "id": "google-user-id",
                "email": "buyer@example.com",
                "email_confirmed_at": "2026-11-22T00:00:00Z",
                "user_metadata": {"full_name": "Google Buyer"},
            },
        }
        with (
            patch(
                "srujansetu.blueprints.shop.exchange_google_code",
                return_value=auth_result,
            ) as exchange,
            patch("srujansetu.blueprints.shop.revoke_auth_session") as revoke,
        ):
            callback = self.client.get("/shop/google/callback?code=one-time-code")

        self.assertEqual(callback.status_code, 302)
        self.assertEqual(callback.location, "/shop/checkout")
        exchange.assert_called_once_with("one-time-code", verifier)
        revoke.assert_called_once_with("temporary-access-token")
        with self.client.session_transaction() as browser_session:
            self.assertEqual(browser_session["role"], "customer")
            self.assertEqual(browser_session["cart"], {"1": 2})
            self.assertNotIn("supabase_oauth_verifier", browser_session)
        with self.app.app_context():
            customer = db.session.query(CustomerAccount).one()
            self.assertEqual(customer.email, "buyer@example.com")
            self.assertEqual(customer.supabase_user_id, "google-user-id")
            self.assertIsNone(customer.password_hash)

    def test_google_sign_in_links_verified_email_to_existing_account(self):
        with self.app.app_context():
            existing = CustomerAccount(
                id="existing-account",
                name="Existing Buyer",
                email="buyer@example.com",
                password_hash=generate_password_hash("a-strong-password"),
            )
            db.session.add(existing)
            db.session.commit()
        with self.client.session_transaction() as browser_session:
            browser_session["supabase_oauth_verifier"] = "test-verifier"

        with (
            patch(
                "srujansetu.blueprints.shop.exchange_google_code",
                return_value={
                    "access_token": "temporary-access-token",
                    "user": {
                        "id": "google-user-id",
                        "email": "buyer@example.com",
                        "email_confirmed_at": "2026-11-22T00:00:00Z",
                    },
                },
            ),
            patch("srujansetu.blueprints.shop.revoke_auth_session"),
        ):
            response = self.client.get("/shop/google/callback?code=one-time-code")

        self.assertEqual(response.status_code, 302)
        with self.app.app_context():
            account = db.session.get(CustomerAccount, "existing-account")
            self.assertEqual(account.supabase_user_id, "google-user-id")
            self.assertTrue(account.password_hash)

    def test_unverified_google_email_does_not_create_account(self):
        with self.client.session_transaction() as browser_session:
            browser_session["supabase_oauth_verifier"] = "test-verifier"
        with (
            patch(
                "srujansetu.blueprints.shop.exchange_google_code",
                return_value={
                    "access_token": "temporary-access-token",
                    "user": {
                        "id": "google-user-id",
                        "email": "buyer@example.com",
                    },
                },
            ),
            patch("srujansetu.blueprints.shop.revoke_auth_session"),
        ):
            response = self.client.get("/shop/google/callback?code=one-time-code")

        self.assertEqual(response.status_code, 302)
        with self.app.app_context():
            self.assertEqual(db.session.query(CustomerAccount).count(), 0)

    def test_google_sign_in_links_existing_artisan_account(self):
        with self.app.app_context():
            db.session.add(ArtisanAccount(
                id="artisan-account",
                name="Existing Maker",
                email="maker@example.com",
                password_hash="existing-hash",
            ))
            db.session.commit()

        start = self.client.get("/shop/google/login?role=artisan")
        self.assertEqual(start.status_code, 302)
        with self.client.session_transaction() as browser_session:
            verifier = browser_session["supabase_oauth_verifier"]
            self.assertEqual(browser_session["supabase_oauth_role"], "artisan")

        with (
            patch(
                "srujansetu.blueprints.shop.exchange_google_code",
                return_value={
                    "access_token": "temporary-access-token",
                    "user": {
                        "id": "google-maker-id",
                        "email": "maker@example.com",
                        "email_confirmed_at": "2026-11-22T00:00:00Z",
                    },
                },
            ),
            patch("srujansetu.blueprints.shop.revoke_auth_session"),
        ):
            response = self.client.get("/shop/google/callback?code=one-time-code")

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.location, "/artisan/dashboard")
        with self.client.session_transaction() as browser_session:
            self.assertEqual(browser_session["role"], "artisan")
            self.assertEqual(browser_session["artisan_user_id"], "artisan-account")
        with self.app.app_context():
            account = db.session.get(ArtisanAccount, "artisan-account")
            self.assertEqual(account.supabase_user_id, "google-maker-id")

    def test_artisan_and_admin_login_pages_offer_google_sign_in(self):
        artisan_page = self.client.get("/artisan/login")
        self.assertIn(b"role=artisan", artisan_page.data)
        self.assertIn(b"Continue with Google", artisan_page.data)

        with self.app.app_context():
            db.session.add(AdminAccount(
                id=1,
                username="site-admin",
                password_hash="existing-hash",
            ))
            db.session.commit()
        admin_page = self.client.get("/admin/login")
        self.assertIn(b"role=admin", admin_page.data)
        self.assertIn(b"Continue with Google", admin_page.data)

    def test_google_sign_in_does_not_create_an_artisan_account(self):
        self.client.get("/shop/google/login?role=artisan")
        with (
            patch(
                "srujansetu.blueprints.shop.exchange_google_code",
                return_value={
                    "access_token": "temporary-access-token",
                    "user": {
                        "id": "google-maker-id",
                        "email": "new-maker@example.com",
                        "email_confirmed_at": "2026-11-22T00:00:00Z",
                    },
                },
            ),
            patch("srujansetu.blueprints.shop.revoke_auth_session"),
        ):
            response = self.client.get("/shop/google/callback?code=one-time-code")

        self.assertEqual(response.location, "/artisan/login")
        with self.app.app_context():
            self.assertEqual(db.session.query(ArtisanAccount).count(), 0)

    def test_google_admin_sign_in_requires_allowlisted_email(self):
        with self.app.app_context():
            db.session.add(AdminAccount(
                id=1,
                username="site-admin",
                password_hash="existing-hash",
            ))
            db.session.commit()

        self.client.get("/shop/google/login?role=admin")
        with (
            patch(
                "srujansetu.blueprints.shop.exchange_google_code",
                return_value={
                    "access_token": "temporary-access-token",
                    "user": {
                        "id": "google-admin-id",
                        "email": "not-allowed@example.com",
                        "email_confirmed_at": "2026-11-22T00:00:00Z",
                    },
                },
            ),
            patch("srujansetu.blueprints.shop.revoke_auth_session"),
        ):
            response = self.client.get("/shop/google/callback?code=one-time-code")

        self.assertEqual(response.location, "/admin/login")
        with self.client.session_transaction() as browser_session:
            self.assertNotEqual(browser_session.get("role"), "admin")

    def test_allowlisted_google_admin_sign_in_requires_existing_admin_setup(self):
        self.client.get("/shop/google/login?role=admin")
        with (
            patch(
                "srujansetu.blueprints.shop.exchange_google_code",
                return_value={
                    "access_token": "temporary-access-token",
                    "user": {
                        "id": "google-admin-id",
                        "email": "admin@example.com",
                        "email_confirmed_at": "2026-11-22T00:00:00Z",
                    },
                },
            ),
            patch("srujansetu.blueprints.shop.revoke_auth_session"),
        ):
            response = self.client.get("/shop/google/callback?code=one-time-code")

        self.assertEqual(response.location, "/admin/login")
        with self.client.session_transaction() as browser_session:
            self.assertNotEqual(browser_session.get("role"), "admin")

    def test_allowlisted_google_admin_can_sign_in_after_setup(self):
        with self.app.app_context():
            db.session.add(AdminAccount(
                id=1,
                username="site-admin",
                password_hash="existing-hash",
            ))
            db.session.commit()

        self.client.get("/shop/google/login?role=admin")
        with (
            patch(
                "srujansetu.blueprints.shop.exchange_google_code",
                return_value={
                    "access_token": "temporary-access-token",
                    "user": {
                        "id": "google-admin-id",
                        "email": "admin@example.com",
                        "email_confirmed_at": "2026-11-22T00:00:00Z",
                    },
                },
            ),
            patch("srujansetu.blueprints.shop.revoke_auth_session"),
        ):
            response = self.client.get("/shop/google/callback?code=one-time-code")

        self.assertEqual(response.location, "/admin/dashboard")
        with self.client.session_transaction() as browser_session:
            self.assertEqual(browser_session["role"], "admin")
            self.assertEqual(browser_session["admin_user"], "admin@example.com")


if __name__ == "__main__":
    unittest.main()
