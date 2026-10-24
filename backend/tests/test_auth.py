import unittest

from werkzeug.security import check_password_hash

from app import create_app
from app.database import db
from app.models import Customer, Professional, ServiceType, User


class RegistrationTestCase(unittest.TestCase):
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
            plumbing = ServiceType(name="Plumbing")
            db.session.add(plumbing)
            db.session.commit()
            self.plumbing_id = plumbing.id

        self.client = self.app.test_client()

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def test_customer_registration_creates_user_and_profile(self):
        response = self.client.post(
            "/api/auth/register",
            json={
                "username": "test_customer",
                "email": "CUSTOMER@example.com",
                "password": "Password123",
                "role": "customer",
                "phone_number": "9999999999",
                "address": "12 Main Road",
                "city": "Bengaluru",
                "state": "Karnataka",
                "pin_code": "560001",
            },
        )

        self.assertEqual(response.status_code, 201)
        self.assertNotIn("password", response.get_json()["user"])

        with self.app.app_context():
            user = db.session.scalar(
                db.select(User).where(User.email == "customer@example.com")
            )
            self.assertIsNotNone(user)
            self.assertTrue(check_password_hash(user.password_hash, "Password123"))
            self.assertIsNotNone(user.customer)

    def test_professional_registration_starts_unapproved(self):
        response = self.client.post(
            "/api/auth/register",
            json={
                "username": "test_professional",
                "email": "professional@example.com",
                "password": "Password123",
                "role": "professional",
                "address": "34 Service Road",
                "city": "Bengaluru",
                "state": "Karnataka",
                "pin_code": "560002",
                "service_type_id": self.plumbing_id,
                "experience_years": 3,
            },
        )

        self.assertEqual(response.status_code, 201)
        self.assertIn("access_token", response.get_json())
        self.assertEqual(
            response.get_json()["user"]["approval_status"],
            "pending",
        )
        with self.app.app_context():
            professional = db.session.scalar(db.select(Professional))
            self.assertIsNotNone(professional)
            self.assertEqual(professional.approval_status, "pending")

    def test_duplicate_user_is_rejected(self):
        payload = {
            "username": "duplicate",
            "email": "duplicate@example.com",
            "password": "Password123",
            "role": "customer",
            "address": "12 Main Road",
            "city": "Bengaluru",
            "state": "Karnataka",
            "pin_code": "560001",
        }

        self.assertEqual(self.client.post("/api/auth/register", json=payload).status_code, 201)
        self.assertEqual(self.client.post("/api/auth/register", json=payload).status_code, 409)

    def test_admin_public_registration_is_rejected(self):
        response = self.client.post(
            "/api/auth/register",
            json={
                "username": "not_admin",
                "email": "not-admin@example.com",
                "password": "Password123",
                "role": "admin",
            },
        )

        self.assertEqual(response.status_code, 400)

    def test_login_returns_access_token(self):
        self.client.post(
            "/api/auth/register",
            json={
                "username": "login_customer",
                "email": "login@example.com",
                "password": "Password123",
                "role": "customer",
                "address": "12 Main Road",
                "city": "Bengaluru",
                "state": "Karnataka",
                "pin_code": "560001",
            },
        )

        response = self.client.post(
            "/api/auth/login",
            json={"email": "login@example.com", "password": "Password123"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("access_token", response.get_json())

    def test_login_rejects_wrong_password(self):
        response = self.client.post(
            "/api/auth/login",
            json={"email": "missing@example.com", "password": "wrong-password"},
        )

        self.assertEqual(response.status_code, 401)

    def test_me_requires_and_accepts_access_token(self):
        self.client.post(
            "/api/auth/register",
            json={
                "username": "current_customer",
                "email": "current@example.com",
                "password": "Password123",
                "role": "customer",
                "address": "12 Main Road",
                "city": "Bengaluru",
                "state": "Karnataka",
                "pin_code": "560001",
            },
        )
        login_response = self.client.post(
            "/api/auth/login",
            json={"email": "current@example.com", "password": "Password123"},
        )
        token = login_response.get_json()["access_token"]

        missing_token = self.client.get("/api/auth/me")
        authenticated = self.client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )

        self.assertEqual(missing_token.status_code, 401)
        self.assertEqual(authenticated.status_code, 200)
        self.assertEqual(authenticated.get_json()["user"]["email"], "current@example.com")

    def test_logout_requires_access_token(self):
        response = self.client.post("/api/auth/logout")

        self.assertEqual(response.status_code, 401)


if __name__ == "__main__":
    unittest.main()
