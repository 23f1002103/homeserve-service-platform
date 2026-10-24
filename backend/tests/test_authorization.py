import unittest

from flask_jwt_extended import create_access_token

from app import create_app
from app.database import db


class RoleAuthorizationTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app(
            {
                "TESTING": True,
                "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
                "JWT_SECRET_KEY": "test-jwt-secret-not-for-production",
            }
        )

        with self.app.app_context():
            db.create_all()
            self.admin_token = create_access_token(
                identity="1",
                additional_claims={"role": "admin"},
            )
            self.customer_token = create_access_token(
                identity="2",
                additional_claims={"role": "customer"},
            )

        self.client = self.app.test_client()

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def test_admin_role_is_allowed(self):
        response = self.client.get(
            "/api/admin/dashboard",
            headers={"Authorization": f"Bearer {self.admin_token}"},
        )

        self.assertEqual(response.status_code, 200)

    def test_customer_role_is_forbidden(self):
        response = self.client.get(
            "/api/admin/dashboard",
            headers={"Authorization": f"Bearer {self.customer_token}"},
        )

        self.assertEqual(response.status_code, 403)

    def test_missing_token_is_unauthorized(self):
        response = self.client.get("/api/admin/dashboard")

        self.assertEqual(response.status_code, 401)


if __name__ == "__main__":
    unittest.main()
