import os
import unittest
from unittest.mock import patch

from app.config import Config, database_url


class DatabaseUrlTestCase(unittest.TestCase):
    def test_database_connections_are_checked_before_reuse(self):
        self.assertTrue(Config.SQLALCHEMY_ENGINE_OPTIONS["pool_pre_ping"])
        self.assertEqual(Config.SQLALCHEMY_ENGINE_OPTIONS["pool_recycle"], 300)

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
