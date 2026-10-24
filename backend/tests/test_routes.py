import unittest

from app import create_app
from app.database import db
from app.models import ServicePricing, ServiceType


class ApiRoutesTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app(
            {
                "TESTING": True,
                "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            }
        )
        with self.app.app_context():
            db.create_all()
            service = ServiceType(
                name="Plumbing",
                description="Leaks, fittings, and household plumbing repairs.",
            )
            db.session.add(service)
            db.session.flush()
            db.session.add(ServicePricing(service_type_id=service.id, price="599.00"))
            db.session.commit()
        self.client = self.app.test_client()

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def test_database_extensions_are_initialized(self):
        self.assertIn("sqlalchemy", self.app.extensions)
        self.assertIn("migrate", self.app.extensions)

    def test_api_home(self):
        response = self.client.get("/api")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["message"], "Welcome to the HomeServe API")

    def test_health_check(self):
        response = self.client.get("/api/health")
        body = response.get_json()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(body["status"], "ok")
        self.assertEqual(body["service"], "homeserve-api")
        self.assertIn("timestamp", body)

    def test_landing_page_content(self):
        response = self.client.get("/api/landing")
        body = response.get_json()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(body["hero"]["title"], "Your home deserves expert care.")
        self.assertEqual(len(body["services"]), 1)
        self.assertEqual(body["services"][0]["name"], "Plumbing")
        self.assertEqual(body["services"][0]["price"], "599.00")
        self.assertEqual(len(body["highlights"]), 3)

    def test_missing_route_returns_json(self):
        response = self.client.get("/api/does-not-exist")

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.content_type, "application/json")
        self.assertEqual(response.get_json()["error"]["code"], 404)


if __name__ == "__main__":
    unittest.main()
