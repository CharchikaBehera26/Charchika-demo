import os
import unittest
from unittest.mock import patch

from srujansetu.config import PROJECT_ROOT, get_database_uri


class DatabaseConfigTests(unittest.TestCase):
    def test_template_database_url_uses_local_sqlite(self):
        template_url = (
            "postgresql://postgres:<database-password>"
            "@db.<project-ref>.supabase.co:5432/postgres"
        )
        with patch.dict(os.environ, {"DATABASE_URL": template_url}):
            self.assertEqual(
                get_database_uri(),
                f"sqlite:///{(PROJECT_ROOT / 'instance' / 'srujansetu.sqlite').as_posix()}",
            )

    def test_configured_postgresql_url_is_preserved(self):
        database_url = "postgresql+psycopg://user:password@db.example.com/postgres"
        with patch.dict(os.environ, {"DATABASE_URL": database_url}):
            self.assertEqual(get_database_uri(), database_url)

    def test_required_database_rejects_missing_url(self):
        with patch.dict(
            os.environ,
            {"DATABASE_URL": "", "REQUIRE_DATABASE_URL": "true"},
        ):
            with self.assertRaisesRegex(RuntimeError, "DATABASE_URL is required"):
                get_database_uri()

    def test_required_database_rejects_sqlite_url(self):
        with patch.dict(
            os.environ,
            {
                "DATABASE_URL": "sqlite:///local.db",
                "REQUIRE_DATABASE_URL": "true",
            },
        ):
            with self.assertRaisesRegex(RuntimeError, "must point to PostgreSQL"):
                get_database_uri()


if __name__ == "__main__":
    unittest.main()
