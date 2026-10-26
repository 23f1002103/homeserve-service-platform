import io
import unittest
from datetime import datetime
from unittest.mock import patch

from flask_jwt_extended import create_access_token
from werkzeug.security import generate_password_hash

from app import create_app
from app.database import db
from app.models import Customer, Payment, Professional, ServiceArea, ServiceRequest, ServiceType, User


class ProfessionalDashboardTestCase(unittest.TestCase):
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
                username="test-pro",
                email="pro@example.com",
                phone_number="9876543210",
                password_hash="not-used-in-this-test",
                role="professional",
            )
            service_type = ServiceType(name="Plumbing")
            db.session.add_all([user, service_type])
            db.session.flush()
            db.session.add(
                Professional(
                    user_id=user.id,
                    address="12 Test Street",
                    city="Bengaluru",
                    state="Karnataka",
                    pin_code="560001",
                    service_type_id=service_type.id,
                    experience_years=5,
                )
            )
            db.session.commit()

            self.professional_token = create_access_token(
                identity=str(user.id),
                additional_claims={"role": "professional"},
            )
            self.customer_token = create_access_token(
                identity="999",
                additional_claims={"role": "customer"},
            )

        self.client = self.app.test_client()

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def test_professional_can_view_dashboard(self):
        response = self.client.get(
            "/api/professional/dashboard",
            headers={"Authorization": f"Bearer {self.professional_token}"},
        )
        body = response.get_json()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(body["service"], "Plumbing")
        self.assertEqual(body["approval_status"], "pending")
        self.assertEqual(body["available_jobs"], [])
        self.assertEqual(body["available_job_count"], 0)

    def test_professional_pages_return_separate_data(self):
        headers = {"Authorization": f"Bearer {self.professional_token}"}

        jobs = self.client.get("/api/professional/jobs", headers=headers)
        profile = self.client.get("/api/professional/profile", headers=headers)

        self.assertEqual(jobs.status_code, 200)
        self.assertIn("jobs", jobs.get_json())
        self.assertEqual(profile.status_code, 200)
        self.assertIn("profile", profile.get_json())

    def test_professional_can_update_profile_fields(self):
        response = self.client.patch(
            "/api/professional/profile",
            headers={"Authorization": f"Bearer {self.professional_token}"},
            json={
                "phone_number": "9876543210",
                "experience_years": 5,
                "address": "50 Work Road",
                "city": "Mysuru",
                "state": "Karnataka",
                "pin_code": "570001",
            },
        )

        self.assertEqual(response.status_code, 200)
        with self.app.app_context():
            professional = db.session.scalar(db.select(Professional))
            self.assertEqual(professional.experience_years, 5)
            self.assertEqual(professional.city, "Mysuru")

    def test_login_requires_a_fresh_gps_location(self):
        with self.app.app_context():
            professional = db.session.scalar(db.select(Professional))
            professional.approval_status = "approved"
            professional.user.password_hash = generate_password_hash("password123")
            area = ServiceArea(
                city="Bengaluru", state="Karnataka", pin_code="560001"
            )
            professional.active_service_area = area
            professional.location_verified_at = datetime.now()
            db.session.add(area)
            db.session.commit()

        response = self.client.post(
            "/api/auth/login",
            json={"email": "pro@example.com", "password": "password123"},
        )

        self.assertEqual(response.status_code, 200)
        with self.app.app_context():
            professional = db.session.scalar(db.select(Professional))
            self.assertIsNone(professional.active_service_area_id)
            self.assertIsNone(professional.location_verified_at)

    def test_professional_photo_rejects_non_image_content(self):
        response = self.client.put(
            "/api/professional/profile/photo",
            headers={"Authorization": f"Bearer {self.professional_token}"},
            data={"photo": (io.BytesIO(b"not really an image"), "profile.png")},
            content_type="multipart/form-data",
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.get_json()["message"],
            "The selected file is not a valid image",
        )

    def test_customer_cannot_view_professional_dashboard(self):
        response = self.client.get(
            "/api/professional/dashboard",
            headers={"Authorization": f"Bearer {self.customer_token}"},
        )

        self.assertEqual(response.status_code, 403)

    @patch("app.professional.routes.get_address_from_coordinates")
    def test_gps_sets_one_active_city_even_when_pin_differs(self, reverse_lookup):
        with self.app.app_context():
            professional = db.session.scalar(db.select(Professional))
            professional.approval_status = "approved"
            area = ServiceArea(
                city="Bengaluru", state="Karnataka", pin_code="560001"
            )
            db.session.add(area)
            db.session.commit()
            area_id = area.id

        reverse_lookup.return_value = {
            "city": "Bangalore",
            "state": "Karnataka",
            "pin_code": "560099",
            "full_address": "Test Road, Bangalore, Karnataka 560099",
        }
        headers = {"Authorization": f"Bearer {self.professional_token}"}
        detected = self.client.post(
            "/api/professional/detect-service-area",
            headers=headers,
            json={"latitude": 12.9, "longitude": 77.6},
        )

        self.assertEqual(detected.status_code, 200)
        self.assertEqual(detected.get_json()["matched_area"]["id"], area_id)
        with self.app.app_context():
            professional = db.session.scalar(db.select(Professional))
            self.assertEqual(professional.active_service_area_id, area_id)
            self.assertIsNotNone(professional.location_verified_at)

    def test_approved_professional_can_see_and_accept_matching_job(self):
        with self.app.app_context():
            professional = db.session.scalar(db.select(Professional))
            first_professional_id = professional.id
            professional.approval_status = "approved"
            area = ServiceArea(
                city="Bengaluru", state="Karnataka", pin_code="560001"
            )
            customer_user = User(
                username="booking-customer",
                email="booking@example.com",
                password_hash="not-used",
                role="customer",
            )
            second_professional_user = User(
                username="second-pro",
                email="second-pro@example.com",
                password_hash="not-used",
                role="professional",
            )
            db.session.add_all([area, customer_user, second_professional_user])
            db.session.flush()
            professional.active_service_area = area
            professional.location_verified_at = datetime.now()
            second_professional = Professional(
                user_id=second_professional_user.id,
                address="Second professional road",
                city="Bengaluru",
                state="Karnataka",
                pin_code="560001",
                service_type_id=professional.service_type_id,
                approval_status="approved",
            )
            second_professional.active_service_area = area
            second_professional.location_verified_at = datetime.now()
            db.session.add(second_professional)
            customer = Customer(
                user_id=customer_user.id,
                address="Customer road",
                city="Bengaluru",
                state="Karnataka",
                pinCode="560001",
            )
            db.session.add(customer)
            db.session.flush()
            job = ServiceRequest(
                customer_id=customer.id,
                service_type_id=professional.service_type_id,
                service_area_id=area.id,
                service_address="Customer road, Bengaluru",
                description="A leaking kitchen tap",
                status="pending",
                latitude=12.9716,
                longitude=77.5946,
                booking_for="other",
                recipient_name="Customer Parent",
                recipient_phone="9988776655",
            )
            second_job = ServiceRequest(
                customer_id=customer.id,
                service_type_id=professional.service_type_id,
                service_area_id=area.id,
                service_address="Another customer address",
                description="A second plumbing request",
                status="pending",
            )
            db.session.add_all([job, second_job])
            db.session.flush()
            db.session.add(
                Payment(
                    service_request_id=job.id,
                    amount="100.00",
                    commission_rate="15.00",
                    platform_fee="15.00",
                    professional_earning="85.00",
                    payment_method="demo_upi",
                    status="completed",
                )
            )
            db.session.commit()
            job_id = job.id
            second_job_id = second_job.id
            customer_token = create_access_token(
                identity=str(customer_user.id),
                additional_claims={"role": "customer"},
            )
            second_professional_token = create_access_token(
                identity=str(second_professional_user.id),
                additional_claims={"role": "professional"},
            )
            admin_token = create_access_token(
                identity="9999",
                additional_claims={"role": "admin"},
            )

        headers = {"Authorization": f"Bearer {self.professional_token}"}
        uploaded_photo = self.client.put(
            "/api/professional/profile/photo",
            headers=headers,
            data={
                "photo": (
                    io.BytesIO(b"\xff\xd8\xff\xe0HomeServe test image"),
                    "profile.jpg",
                )
            },
            content_type="multipart/form-data",
        )
        available = self.client.get("/api/professional/jobs", headers=headers)
        dashboard_available = self.client.get(
            "/api/professional/dashboard", headers=headers
        )
        accepted = self.client.patch(
            f"/api/professional/jobs/{job_id}/accept", headers=headers
        )
        customer_bookings = self.client.get(
            "/api/customer/bookings",
            headers={"Authorization": f"Bearer {customer_token}"},
        )
        notification_response = self.client.get(
            "/api/customer/notifications/unread",
            headers={"Authorization": f"Bearer {customer_token}"},
        )
        notification_id = notification_response.get_json()["notification"]["id"]
        notification_read = self.client.patch(
            f"/api/customer/notifications/{notification_id}/read",
            headers={"Authorization": f"Bearer {customer_token}"},
        )
        notification_after_read = self.client.get(
            "/api/customer/notifications/unread",
            headers={"Authorization": f"Bearer {customer_token}"},
        )
        assigned = self.client.get("/api/professional/jobs", headers=headers)
        cancellation_after_assignment = self.client.patch(
            f"/api/customer/bookings/{job_id}/cancel",
            headers={"Authorization": f"Bearer {customer_token}"},
        )
        second_acceptance = self.client.patch(
            f"/api/professional/jobs/{second_job_id}/accept", headers=headers
        )
        taken_job = self.client.patch(
            f"/api/professional/jobs/{job_id}/accept",
            headers={"Authorization": f"Bearer {second_professional_token}"},
        )
        completed = self.client.patch(
            f"/api/professional/jobs/{job_id}/complete", headers=headers
        )
        review_prompt = self.client.get(
            "/api/customer/review-prompt",
            headers={"Authorization": f"Bearer {customer_token}"},
        )
        review_prompt_again = self.client.get(
            "/api/customer/review-prompt",
            headers={"Authorization": f"Bearer {customer_token}"},
        )
        accepted_after_completion = self.client.patch(
            f"/api/professional/jobs/{second_job_id}/accept", headers=headers
        )
        reviewed = self.client.post(
            f"/api/customer/bookings/{job_id}/review",
            headers={"Authorization": f"Bearer {customer_token}"},
            json={"rating": 5, "comment": "Excellent and tidy work."},
        )
        profile_response = self.client.get(
            "/api/professional/profile", headers=headers
        )
        dashboard_response = self.client.get(
            "/api/professional/dashboard", headers=headers
        )
        customer_dashboard_response = self.client.get(
            "/api/customer/dashboard",
            headers={"Authorization": f"Bearer {customer_token}"},
        )
        earnings_response = self.client.get(
            "/api/professional/earnings", headers=headers
        )
        admin_professionals = self.client.get(
            "/api/admin/professionals",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        admin_dashboard = self.client.get(
            "/api/admin/dashboard",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        admin_revenue = self.client.get(
            "/api/admin/revenue",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        admin_revenue_export = self.client.get(
            "/api/admin/revenue/export?start_date=2000-01-01&end_date=2099-12-31",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        admin_headers = {"Authorization": f"Bearer {admin_token}"}
        blocked_during_active_job = self.client.patch(
            f"/api/admin/professionals/{first_professional_id}/status",
            headers=admin_headers,
            json={"status": "blocked", "reason": "Low customer ratings"},
        )
        completed_second_job = self.client.patch(
            f"/api/professional/jobs/{second_job_id}/complete", headers=headers
        )
        blocked_after_completion = self.client.patch(
            f"/api/admin/professionals/{first_professional_id}/status",
            headers=admin_headers,
            json={"status": "blocked", "reason": "Low customer ratings"},
        )

        self.assertEqual(available.status_code, 200)
        self.assertEqual(uploaded_photo.status_code, 200)
        self.assertEqual(len(available.get_json()["available_jobs"]), 2)
        self.assertEqual(dashboard_available.get_json()["available_job_count"], 2)
        self.assertEqual(len(dashboard_available.get_json()["available_jobs"]), 2)
        self.assertTrue(dashboard_available.get_json()["location_verified"])
        self.assertEqual(
            dashboard_available.get_json()["current_area"]["city"], "Bengaluru"
        )
        self.assertNotIn("directions_url", available.get_json()["available_jobs"][0])
        self.assertEqual(accepted.status_code, 200)
        self.assertEqual(customer_bookings.status_code, 200)
        assigned_professional = next(
            booking["professional_details"]
            for booking in customer_bookings.get_json()["bookings"]
            if booking["id"] == job_id
        )
        self.assertEqual(assigned_professional["name"], "test-pro")
        self.assertEqual(assigned_professional["phone_number"], "9876543210")
        self.assertEqual(assigned_professional["experience_years"], 5)
        self.assertEqual(assigned_professional["review_count"], 0)
        self.assertEqual(
            assigned_professional["profile_image_url"],
            f"/api/professional/profiles/{first_professional_id}/photo",
        )
        public_photo = self.client.get(assigned_professional["profile_image_url"])
        self.assertEqual(public_photo.status_code, 200)
        self.assertEqual(public_photo.mimetype, "image/jpeg")
        self.assertTrue(public_photo.data.startswith(b"\xff\xd8\xff"))
        self.assertNotIn("email", assigned_professional)
        self.assertNotIn("address", assigned_professional)
        self.assertEqual(notification_response.status_code, 200)
        self.assertIn(
            "accepted your Plumbing booking",
            notification_response.get_json()["notification"]["message"],
        )
        self.assertEqual(notification_read.status_code, 200)
        self.assertIsNone(notification_after_read.get_json()["notification"])
        self.assertEqual(cancellation_after_assignment.status_code, 409)
        self.assertTrue(assigned.get_json()["has_active_job"])
        self.assertEqual(assigned.get_json()["available_jobs"], [])
        self.assertEqual(assigned.get_json()["jobs"][0]["customer"], "Customer Parent")
        self.assertEqual(assigned.get_json()["jobs"][0]["customer_phone"], "9988776655")
        self.assertEqual(assigned.get_json()["jobs"][0]["booking_for"], "other")
        self.assertEqual(second_acceptance.status_code, 409)
        self.assertEqual(taken_job.status_code, 409)
        self.assertIn(
            "destination=12.9716,77.5946",
            assigned.get_json()["jobs"][0]["directions_url"],
        )
        self.assertEqual(completed.status_code, 200)
        self.assertEqual(review_prompt.status_code, 200)
        self.assertEqual(
            review_prompt.get_json()["review_prompt"]["booking_id"], job_id
        )
        self.assertEqual(
            review_prompt.get_json()["review_prompt"]["professional"], "test-pro"
        )
        self.assertIsNone(review_prompt_again.get_json()["review_prompt"])
        self.assertEqual(reviewed.status_code, 201)
        self.assertEqual(accepted_after_completion.status_code, 200)
        self.assertEqual(profile_response.status_code, 200)
        self.assertEqual(profile_response.get_json()["profile"]["average_rating"], 5.0)
        self.assertEqual(profile_response.get_json()["profile"]["review_count"], 1)
        self.assertEqual(
            profile_response.get_json()["profile"]["profile_image_url"],
            f"/api/professional/profiles/{first_professional_id}/photo",
        )
        self.assertEqual(dashboard_response.get_json()["today_earning"], "85.00")
        self.assertEqual(
            customer_dashboard_response.get_json()["active_booking"]["id"],
            second_job_id,
        )
        self.assertEqual(
            customer_dashboard_response.get_json()["active_booking"]["status"],
            "accepted",
        )
        self.assertEqual(
            customer_dashboard_response.get_json()["active_booking"]["professional"][
                "profile_image_url"
            ],
            f"/api/professional/profiles/{first_professional_id}/photo",
        )
        self.assertEqual(earnings_response.get_json()["total_earning"], "85.00")
        self.assertEqual(len(earnings_response.get_json()["completed_jobs"]), 1)
        self.assertEqual(admin_dashboard.get_json()["revenue"]["total"], "15.00")
        self.assertEqual(admin_revenue.status_code, 200)
        self.assertEqual(admin_revenue_export.status_code, 200)
        self.assertEqual(admin_revenue_export.mimetype, "text/csv")
        self.assertIn(b"HomeServe Revenue (INR)", admin_revenue_export.data)
        self.assertEqual(admin_revenue.get_json()["all_time"]["platform_revenue"], "15.00")
        self.assertEqual(admin_revenue.get_json()["all_time"]["gross_payments"], "100.00")
        self.assertEqual(len(admin_revenue.get_json()["transactions"]), 1)
        rated_professional = next(
            item
            for item in admin_professionals.get_json()["professionals"]
            if item["email"] == "pro@example.com"
        )
        self.assertEqual(rated_professional["average_rating"], 5.0)
        self.assertEqual(rated_professional["review_count"], 1)
        self.assertEqual(blocked_during_active_job.status_code, 409)
        self.assertEqual(completed_second_job.status_code, 200)
        self.assertEqual(blocked_after_completion.status_code, 200)
        with self.app.app_context():
            job = db.session.get(ServiceRequest, job_id)
            self.assertEqual(job.professional_id, first_professional_id)
            self.assertEqual(job.status, "completed")


if __name__ == "__main__":
    unittest.main()
