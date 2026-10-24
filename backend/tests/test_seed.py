import unittest

from werkzeug.security import check_password_hash

from app import create_app
from app.database import db
from app.models import User
from app.seed import ensure_admin_exists


class AdminSeedTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app(
            {
                "TESTING": True,
                "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
                "ADMIN_USERNAME": "test_admin",
                "ADMIN_EMAIL": "admin@test.local",
                "ADMIN_PASSWORD": "test-password-not-for-production",
            }
        )

        with self.app.app_context():
            db.create_all()

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def test_admin_is_created_with_a_hashed_password(self):
        with self.app.app_context():
            self.assertTrue(ensure_admin_exists())

            admin = db.session.scalar(
                db.select(User).where(User.email == "admin@test.local")
            )
            self.assertIsNotNone(admin)
            self.assertEqual(admin.role, "admin")
            self.assertNotEqual(
                admin.password_hash,
                "test-password-not-for-production",
            )
            self.assertTrue(
                check_password_hash(
                    admin.password_hash,
                    "test-password-not-for-production",
                )
            )

    def test_repeated_startup_does_not_duplicate_admin(self):
        with self.app.app_context():
            self.assertTrue(ensure_admin_exists())
            self.assertFalse(ensure_admin_exists())
            self.assertEqual(db.session.scalar(db.select(db.func.count(User.id))), 1)


if __name__ == "__main__":
    unittest.main()
