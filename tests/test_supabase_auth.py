import base64
import hashlib
import unittest
from urllib.parse import parse_qs, urlsplit
from unittest.mock import patch

from srujansetu import create_app
from srujansetu.extensions import db
from srujansetu.models import CustomerAccount
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


if __name__ == "__main__":
    unittest.main()
