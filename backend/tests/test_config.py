import os
import unittest
from unittest.mock import patch

from app.config import database_url


class DatabaseUrlTestCase(unittest.TestCase):
    def test_railway_postgres_url_uses_psycopg_driver(self):
        with patch.dict(
            os.environ,
            {"DATABASE_URL": "postgres://user:password@postgres:5432/homeserve"},
        ):
            self.assertEqual(
                database_url(),
                "postgresql+psycopg://user:password@postgres:5432/homeserve",
            )

    def test_standard_postgresql_url_uses_psycopg_driver(self):
        with patch.dict(
            os.environ,
            {"DATABASE_URL": "postgresql://user:password@postgres:5432/homeserve"},
        ):
            self.assertEqual(
                database_url(),
                "postgresql+psycopg://user:password@postgres:5432/homeserve",
            )


if __name__ == "__main__":
    unittest.main()
