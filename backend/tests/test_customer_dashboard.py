import unittest
from unittest.mock import patch

from flask_jwt_extended import create_access_token

from app import create_app
from app.database import db
from app.models import (
    Customer,
    Payment,
    ServiceArea,
    ServicePricing,
    ServiceRequest,
    ServiceType,
    User,
)


class CustomerDashboardTestCase(unittest.TestCase):
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
            user = User(
                username="test-customer",
                email="customer@example.com",
                phone_number="9999999999",
                password_hash="not-used-in-this-test",
                role="customer",
            )
            db.session.add(user)
            db.session.flush()
            db.session.add(
                Customer(
                    user_id=user.id,
                    address="12 Main Road",
                    city="Bengaluru",
                    state="Karnataka",
                    pinCode="560001",
                )
            )
            service = ServiceType(name="Cleaning")
            db.session.add(service)
            db.session.flush()
            db.session.add(ServicePricing(service_type_id=service.id, price="499.00"))
            db.session.add(
                ServiceArea(city="Bengaluru", state="Karnataka", pin_code="560001")
            )
            db.session.commit()
            self.token = create_access_token(
                identity=str(user.id), additional_claims={"role": "customer"}
            )
        self.client = self.app.test_client()

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def test_customer_pages_return_separate_data(self):
        headers = {"Authorization": f"Bearer {self.token}"}
        paths_and_keys = [
            ("/api/customer/dashboard", "open_bookings"),
            ("/api/customer/services", "services"),
            ("/api/customer/bookings", "bookings"),
            ("/api/customer/profile", "profile"),
        ]

        for path, key in paths_and_keys:
            response = self.client.get(path, headers=headers)
            self.assertEqual(response.status_code, 200)
            self.assertIn(key, response.get_json())

        dashboard = self.client.get(
            "/api/customer/dashboard", headers=headers
        ).get_json()
        self.assertIsNone(dashboard["active_booking"])
        self.assertEqual(dashboard["active_bookings"], [])

    def test_dashboard_returns_every_active_booking_newest_first(self):
        with self.app.app_context():
            customer = db.session.scalar(db.select(Customer))
            service = db.session.scalar(db.select(ServiceType))
            area = db.session.scalar(db.select(ServiceArea))
            first = ServiceRequest(
                customer_id=customer.id,
                service_type_id=service.id,
                service_area_id=area.id,
                service_address="12 Main Road",
                status="accepted",
            )
            db.session.add(first)
            db.session.flush()
            second = ServiceRequest(
                customer_id=customer.id,
                service_type_id=service.id,
                service_area_id=area.id,
                service_address="45 Second Road",
                status="pending",
            )
            db.session.add(second)
            db.session.commit()
            first_id = first.id
            second_id = second.id

        response = self.client.get(
            "/api/customer/dashboard",
            headers={"Authorization": f"Bearer {self.token}"},
        )

        self.assertEqual(response.status_code, 200)
        dashboard = response.get_json()
        self.assertEqual(dashboard["open_bookings"], 2)
        self.assertEqual(
            [booking["id"] for booking in dashboard["active_bookings"]],
            [second_id, first_id],
        )
        self.assertEqual(dashboard["active_booking"]["id"], second_id)

    def test_customer_can_update_profile_fields(self):
        response = self.client.patch(
            "/api/customer/profile",
            headers={"Authorization": f"Bearer {self.token}"},
            json={
                "phone_number": "9876543210",
                "address": "45 New Road",
                "city": "Mysuru",
                "state": "Karnataka",
                "pin_code": "570001",
            },
        )

        self.assertEqual(response.status_code, 200)
        with self.app.app_context():
            customer = db.session.scalar(db.select(Customer))
            self.assertEqual(customer.city, "Mysuru")
            self.assertEqual(customer.user.phone_number, "9876543210")

    def test_customer_can_create_booking(self):
        with self.app.app_context():
            service = db.session.scalar(db.select(ServiceType))
            service_id = service.id
            area_id = db.session.scalar(db.select(ServiceArea.id))

        response = self.client.post(
            "/api/customer/bookings",
            headers={"Authorization": f"Bearer {self.token}"},
            json={
                "service_type_id": service_id,
                "scheduled_for": "2099-01-20T10:30",
                "service_address": (
                    "5th A Cross Road, Basappa Garden, Seshadripuram, "
                    "Bengaluru Central City Corporation - 560001"
                ),
                "service_pin_code": "560001",
                "service_city": "Bengaluru",
                "service_state": "Karnataka",
                "service_area_id": area_id,
                "latitude": 12.9716,
                "longitude": 77.5946,
                "description": "The kitchen needs a deep clean.",
            },
        )

        self.assertEqual(response.status_code, 201)
        response_data = response.get_json()
        booking_id = response_data["booking_id"]
        verify_response = self.client.post(
            f"/api/customer/bookings/{booking_id}/complete-demo-payment",
            headers={"Authorization": f"Bearer {self.token}"},
            json={
                "order_id": response_data["demo_payment"]["order_id"],
                "result": "success",
            },
        )

        self.assertEqual(verify_response.status_code, 200)
        invoice_response = self.client.get(
            f"/api/customer/bookings/{booking_id}/invoice",
            headers={"Authorization": f"Bearer {self.token}"},
        )
        self.assertEqual(invoice_response.status_code, 200)
        self.assertEqual(invoice_response.mimetype, "application/pdf")
        self.assertTrue(invoice_response.data.startswith(b"%PDF"))
        with self.app.app_context():
            booking = db.session.scalar(db.select(ServiceRequest))
            self.assertEqual(booking.status, "pending")
            self.assertEqual(booking.service_type_id, service_id)
            self.assertIsNotNone(booking.service_area_id)
            self.assertEqual(booking.latitude, 12.9716)
            self.assertEqual(booking.longitude, 77.5946)
            payment = db.session.scalar(db.select(Payment))
            self.assertEqual(payment.status, "completed")
            self.assertEqual(payment.payment_method, "demo_upi")
            self.assertEqual(str(payment.commission_rate), "15.00")
            self.assertEqual(str(payment.platform_fee), "74.85")
            self.assertEqual(str(payment.professional_earning), "424.15")
            self.assertTrue(payment.provider_payment_id.startswith("demo_pay_"))

        cancel_response = self.client.patch(
            f"/api/customer/bookings/{booking_id}/cancel",
            headers={"Authorization": f"Bearer {self.token}"},
        )
        self.assertEqual(cancel_response.status_code, 200)
        self.assertEqual(cancel_response.get_json()["payment_status"], "refunded")
        with self.app.app_context():
            booking = db.session.get(ServiceRequest, booking_id)
            payment = db.session.scalar(db.select(Payment))
            self.assertEqual(booking.status, "cancelled")
            self.assertEqual(payment.status, "refunded")

    def test_booking_is_rejected_outside_service_area(self):
        with self.app.app_context():
            customer = db.session.scalar(db.select(Customer))
            service = db.session.scalar(db.select(ServiceType))
            customer.pinCode = "999999"
            service_id = service.id
            db.session.commit()

        response = self.client.post(
            "/api/customer/bookings",
            headers={"Authorization": f"Bearer {self.token}"},
            json={
                "service_type_id": service_id,
                "scheduled_for": "2099-01-20T10:30",
                "service_address": "Outside service area",
                "service_pin_code": "999999",
                "service_city": "Mysuru",
                "service_state": "Karnataka",
                "description": "Test request",
            },
        )

        self.assertEqual(response.status_code, 400)

    def test_customer_can_verify_and_book_a_manual_service_address(self):
        headers = {"Authorization": f"Bearer {self.token}"}
        with self.app.app_context():
            service_id = db.session.scalar(db.select(ServiceType.id))
            area_id = db.session.scalar(db.select(ServiceArea.id))

        verification = self.client.post(
            "/api/customer/verify-service-area",
            headers=headers,
            json={
                "city": "Bangalore",
                "state": "Karnataka",
                "pin_code": "560099",
            },
        )
        response = self.client.post(
            "/api/customer/bookings",
            headers=headers,
            json={
                "service_type_id": service_id,
                "scheduled_for": "2099-01-20T10:30",
                "service_address": "88 Manual Address, Bengaluru",
                "service_pin_code": "560099",
                "service_city": "Bangalore",
                "service_state": "Karnataka",
                "service_area_id": area_id,
                "description": "Manual-address booking test",
            },
        )

        self.assertEqual(verification.status_code, 200)
        self.assertEqual(verification.get_json()["matched_area"]["id"], area_id)
        self.assertEqual(response.status_code, 201)
        with self.app.app_context():
            booking = db.session.get(ServiceRequest, response.get_json()["booking_id"])
            self.assertIsNone(booking.latitude)
            self.assertIsNone(booking.longitude)
            self.assertEqual(booking.service_area_id, area_id)

    def test_manual_service_area_verification_rejects_unavailable_city(self):
        response = self.client.post(
            "/api/customer/verify-service-area",
            headers={"Authorization": f"Bearer {self.token}"},
            json={
                "city": "Mysuru",
                "state": "Karnataka",
                "pin_code": "570001",
            },
        )

        self.assertEqual(response.status_code, 404)
        self.assertIsNone(response.get_json()["matched_area"])

    def test_manual_booking_cannot_use_an_area_id_with_a_different_city(self):
        with self.app.app_context():
            service_id = db.session.scalar(db.select(ServiceType.id))
            area_id = db.session.scalar(db.select(ServiceArea.id))

        response = self.client.post(
            "/api/customer/bookings",
            headers={"Authorization": f"Bearer {self.token}"},
            json={
                "service_type_id": service_id,
                "scheduled_for": "2099-01-20T10:30",
                "service_address": "Outside service area",
                "service_pin_code": "999999",
                "service_city": "Mysuru",
                "service_state": "Karnataka",
                "service_area_id": area_id,
                "description": "Forged service-area ID test",
            },
        )

        self.assertEqual(response.status_code, 400)

    def test_booking_requires_complete_customer_profile(self):
        with self.app.app_context():
            customer = db.session.scalar(db.select(Customer))
            customer.user.phone_number = None
            service_id = db.session.scalar(db.select(ServiceType.id))
            db.session.commit()

        response = self.client.post(
            "/api/customer/bookings",
            headers={"Authorization": f"Bearer {self.token}"},
            json={"service_type_id": service_id},
        )

        self.assertEqual(response.status_code, 409)
        self.assertTrue(response.get_json()["profile_incomplete"])

    @patch("app.customer.routes.get_address_from_coordinates")
    def test_detected_bangalore_matches_admin_bengaluru_area(self, reverse_lookup):
        reverse_lookup.return_value = {
            "city": "Bangalore",
            "state": "Karnataka",
            "pin_code": "560099",
            "full_address": "Test Road, Bangalore, Karnataka 560099",
        }

        response = self.client.post(
            "/api/customer/detect-service-area",
            headers={"Authorization": f"Bearer {self.token}"},
            json={"latitude": 12.9, "longitude": 77.6},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["match_method"], "city_state")
        self.assertEqual(response.get_json()["matched_area"]["city"], "Bengaluru")


if __name__ == "__main__":
    unittest.main()
