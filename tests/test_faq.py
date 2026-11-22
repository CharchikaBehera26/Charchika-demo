import unittest

from srujansetu import create_app
from srujansetu.extensions import db
from srujansetu.services.faq import cached_faqs, find_faq


class FAQTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = create_app({
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite://",
        })
        with cls.app.app_context():
            db.create_all()

    @classmethod
    def tearDownClass(cls):
        with cls.app.app_context():
            db.drop_all()

    def setUp(self):
        self.client = self.app.test_client()

    def test_common_greeting_typos_and_variants(self):
        for message in ("hii", "hellow", "hii hellow", "hi there"):
            with self.subTest(message=message):
                self.assertEqual(find_faq(message).question, "Hi / hello")

    def test_every_visible_faq_question_has_an_answer(self):
        for faq in cached_faqs():
            with self.subTest(question=faq.question):
                self.assertIs(find_faq(faq.question), faq)

    def test_map_pin_question_uses_the_specific_answer(self):
        faq = find_faq("Why are there no pins on the map?")
        self.assertEqual(faq.question, "Why are there no pins on the map?")

    def test_assistant_shows_faqs_and_navigation_actions(self):
        page = self.client.get("/assistant")
        self.assertEqual(page.status_code, 200)
        self.assertIn(b"Frequently asked questions", page.data)

        response = self.client.post(
            "/assistant",
            data={"message": "hii, find artisans near me"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Exact pins appear only", response.data)
        self.assertIn(b'href="/artisans"', response.data)
        self.assertIn(b'href="/planner"', response.data)

    def test_unknown_question_has_clear_fallback(self):
        response = self.client.post(
            "/assistant",
            data={"message": "How do I build a spaceship?"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"I couldn&#39;t find that in the site&#39;s information yet.", response.data)

    def test_buying_question_explains_demo_order_and_customer_actions(self):
        response = self.client.post(
            "/assistant",
            data={"message": "Can I buy products on this site?"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"submit a demo order request", response.data)
        self.assertIn(b'href="/shop/cart"', response.data)
        self.assertIn(b'href="/shop/register"', response.data)
        self.assertIn(b'href="/shop/login"', response.data)


if __name__ == "__main__":
    unittest.main()
