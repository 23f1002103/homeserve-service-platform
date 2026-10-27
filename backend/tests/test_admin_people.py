import unittest
from datetime import datetime

from flask_jwt_extended import create_access_token

from app import create_app
from app.database import db
from app.models import (
    Customer,
    Payment,
    Professional,
    Review,
    ServiceRequest,
    ServiceType,
    User,
)


class AdminPeopleTestCase(unittest.TestCase):
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
            customer_user = User(
                username="Home Owner",
                email="customer@example.com",
                phone_number="9000000001",
                password_hash="not-used",
                role="customer",
            )
            professional_user = User(
                username="Service Expert",
                email="professional@example.com",
                phone_number="9000000002",
                password_hash="not-used",
                role="professional",
            )
            service = ServiceType(name="Electrical")
            db.session.add_all([customer_user, professional_user, service])
            db.session.flush()

            customer = Customer(
                user_id=customer_user.id,
                address="12 Customer Road",
                city="Mysuru",
                state="Karnataka",
                pinCode="570001",
            )
            professional = Professional(
                user_id=professional_user.id,
                address="20 Professional Road",
                city="Mysuru",
                state="Karnataka",
                pin_code="570002",
                service_type_id=service.id,
                experience_years=4,
                approval_status="approved",
            )
            db.session.add_all([customer, professional])
            db.session.flush()

            booking = ServiceRequest(
                customer_id=customer.id,
                professional_id=professional.id,
                service_type_id=service.id,
                status="completed",
                service_address="12 Customer Road",
                scheduled_for=datetime(2026, 10, 20, 10, 0),
                completed_at=datetime(2026, 10, 20, 11, 0),
            )
            db.session.add(booking)
            db.session.flush()
            db.session.add_all(
                [
                    Payment(
                        service_request_id=booking.id,
                        amount="750.00",
                        commission_rate="15.00",
                        platform_fee="112.50",
                        professional_earning="637.50",
                        payment_method="test",
                        status="completed",
                    ),
                    Review(
                        service_request_id=booking.id,
                        rating=4,
                        comment="Good service",
                    ),
                ]
            )
            db.session.commit()

            self.customer_id = customer.id
            self.professional_id = professional.id
            self.admin_token = create_access_token(
                identity="999", additional_claims={"role": "admin"}
            )
            self.customer_token = create_access_token(
                identity=str(customer_user.id),
                additional_claims={"role": "customer"},
            )

        self.client = self.app.test_client()

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def headers(self, token=None):
        return {"Authorization": f"Bearer {token or self.admin_token}"}

    def test_admin_can_view_customer_profile_and_booking_history(self):
        response = self.client.get(
            f"/api/admin/customers/{self.customer_id}", headers=self.headers()
        )
        body = response.get_json()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(body["customer"]["address"], "12 Customer Road")
        self.assertEqual(body["summary"]["total_bookings"], 1)
        self.assertEqual(body["summary"]["completed_bookings"], 1)
        self.assertEqual(body["summary"]["total_spent"], "750.00")
        self.assertEqual(body["bookings"][0]["professional"], "Service Expert")
        self.assertEqual(body["bookings"][0]["payment"]["status"], "completed")

    def test_admin_can_view_professional_profile_jobs_and_earnings(self):
        response = self.client.get(
            f"/api/admin/professionals/{self.professional_id}",
            headers=self.headers(),
        )
        body = response.get_json()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(body["professional"]["service"], "Electrical")
        self.assertEqual(body["professional"]["average_rating"], 4.0)
        self.assertEqual(body["summary"]["completed_jobs"], 1)
        self.assertEqual(body["summary"]["total_earnings"], "637.50")
        self.assertEqual(body["jobs"][0]["customer"], "Home Owner")
        self.assertEqual(body["jobs"][0]["review"]["rating"], 4)

    def test_people_details_are_admin_only(self):
        response = self.client.get(
            f"/api/admin/customers/{self.customer_id}",
            headers=self.headers(self.customer_token),
        )

        self.assertEqual(response.status_code, 403)

    def test_missing_people_return_not_found(self):
        customer = self.client.get("/api/admin/customers/9999", headers=self.headers())
        professional = self.client.get(
            "/api/admin/professionals/9999", headers=self.headers()
        )

        self.assertEqual(customer.status_code, 404)
        self.assertEqual(professional.status_code, 404)


if __name__ == "__main__":
    unittest.main()
