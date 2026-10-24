import unittest

from flask_jwt_extended import create_access_token

from app import create_app
from app.database import db
from app.models import Professional, ServicePricing, ServiceType, User


class ServiceTypeTestCase(unittest.TestCase):
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
        self.client = self.app.test_client()

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def test_admin_creates_service_visible_in_public_list(self):
        create_response = self.client.post(
            "/api/admin/service-types",
            json={
                "name": "Plumbing",
                "description": "Leaks and pipe repairs",
                "base_price": "499.00",
            },
            headers={"Authorization": f"Bearer {self.admin_token}"},
        )
        list_response = self.client.get("/api/service-types")

        self.assertEqual(create_response.status_code, 201)
        self.assertEqual(list_response.status_code, 200)
        self.assertEqual(list_response.get_json()["service_types"][0]["name"], "Plumbing")
        self.assertEqual(list_response.get_json()["service_types"][0]["base_price"], "499.00")

    def test_admin_can_update_service_price(self):
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        created = self.client.post(
            "/api/admin/service-types",
            json={"name": "Electrical", "base_price": "300"},
            headers=headers,
        ).get_json()

        response = self.client.patch(
            f"/api/admin/service-types/{created['service_type']['id']}/price",
            json={"base_price": "650"},
            headers=headers,
        )
        services = self.client.get(
            "/api/admin/service-types", headers=headers
        ).get_json()["service_types"]

        self.assertEqual(response.status_code, 200)
        self.assertEqual(services[0]["base_price"], "650.00")

    def test_duplicate_service_name_is_rejected(self):
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        self.client.post("/api/admin/service-types", json={"name": "Cleaning"}, headers=headers)
        response = self.client.post("/api/admin/service-types", json={"name": "cleaning"}, headers=headers)

        self.assertEqual(response.status_code, 409)

    def test_admin_can_delete_an_unused_service(self):
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        created = self.client.post(
            "/api/admin/service-types",
            json={"name": "Painting", "base_price": "750"},
            headers=headers,
        ).get_json()

        response = self.client.delete(
            f"/api/admin/service-types/{created['service_type']['id']}",
            headers=headers,
        )

        self.assertEqual(response.status_code, 200)
        with self.app.app_context():
            self.assertIsNone(db.session.scalar(db.select(ServiceType)))
            self.assertIsNone(db.session.scalar(db.select(ServicePricing)))

    def test_admin_cannot_delete_a_service_used_by_a_professional(self):
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        created = self.client.post(
            "/api/admin/service-types",
            json={"name": "Carpentry", "base_price": "800"},
            headers=headers,
        ).get_json()
        service_id = created["service_type"]["id"]

        with self.app.app_context():
            user = User(
                username="carpenter",
                email="carpenter@example.com",
                password_hash="unused",
                role="professional",
            )
            db.session.add(user)
            db.session.flush()
            db.session.add(
                Professional(
                    user_id=user.id,
                    address="Workshop Road",
                    city="Bengaluru",
                    state="Karnataka",
                    pin_code="560001",
                    service_type_id=service_id,
                )
            )
            db.session.commit()

        response = self.client.delete(
            f"/api/admin/service-types/{service_id}",
            headers=headers,
        )

        self.assertEqual(response.status_code, 409)
        self.assertIn("professionals or bookings", response.get_json()["message"])


if __name__ == "__main__":
    unittest.main()
