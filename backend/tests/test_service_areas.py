import unittest

from flask_jwt_extended import create_access_token

from app import create_app
from app.database import db
from app.models import Professional, ServiceArea, ServiceType, User


class ServiceAreaTestCase(unittest.TestCase):
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
                identity="1", additional_claims={"role": "admin"}
            )
        self.client = self.app.test_client()

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def test_admin_can_delete_unused_area(self):
        with self.app.app_context():
            area = ServiceArea(city="Mysuru", state="Karnataka", pin_code="570001")
            db.session.add(area)
            db.session.commit()
            area_id = area.id

        response = self.client.delete(
            f"/api/admin/service-areas/{area_id}",
            headers={"Authorization": f"Bearer {self.admin_token}"},
        )

        self.assertEqual(response.status_code, 200)

    def test_admin_cannot_delete_area_used_by_professional(self):
        with self.app.app_context():
            user = User(
                username="area-pro",
                email="area-pro@example.com",
                password_hash="not-used",
                role="professional",
            )
            service = ServiceType(name="Cleaning")
            area = ServiceArea(city="Mysuru", state="Karnataka", pin_code="570001")
            db.session.add_all([user, service, area])
            db.session.flush()
            profile = Professional(
                user_id=user.id,
                address="Test road",
                city="Mysuru",
                state="Karnataka",
                pin_code="570001",
                service_type_id=service.id,
            )
            profile.service_areas.append(area)
            db.session.add(profile)
            db.session.commit()
            area_id = area.id

        response = self.client.delete(
            f"/api/admin/service-areas/{area_id}",
            headers={"Authorization": f"Bearer {self.admin_token}"},
        )

        self.assertEqual(response.status_code, 409)


if __name__ == "__main__":
    unittest.main()
