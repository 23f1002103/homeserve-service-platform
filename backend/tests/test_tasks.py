import unittest
from datetime import datetime, timedelta
from unittest.mock import patch

from app import create_app
from app.database import db
from app.models import Customer, Professional, ServiceRequest, ServiceType, User
from app.tasks import send_upcoming_job_reminders


class BackgroundTaskTestCase(unittest.TestCase):
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
                username="reminder-customer",
                email="customer@example.com",
                password_hash="unused",
                role="customer",
            )
            professional_user = User(
                username="reminder-professional",
                email="professional@example.com",
                password_hash="unused",
                role="professional",
            )
            service = ServiceType(name="Electrical")
            db.session.add_all([customer_user, professional_user, service])
            db.session.flush()
            customer = Customer(
                user_id=customer_user.id,
                address="Customer Road",
                city="Bengaluru",
                state="Karnataka",
                pinCode="560001",
            )
            professional = Professional(
                user_id=professional_user.id,
                address="Professional Road",
                city="Bengaluru",
                state="Karnataka",
                pin_code="560001",
                service_type_id=service.id,
                approval_status="approved",
            )
            db.session.add_all([customer, professional])
            db.session.flush()
            booking = ServiceRequest(
                customer_id=customer.id,
                professional_id=professional.id,
                service_type_id=service.id,
                service_address="12 Reminder Street",
                status="accepted",
                scheduled_for=datetime.now() + timedelta(minutes=30),
            )
            db.session.add(booking)
            db.session.commit()
            self.booking_id = booking.id

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    @patch("app.tasks.send_templated_email", return_value=True)
    def test_upcoming_job_reminder_is_sent_only_once(self, send_email):
        with self.app.app_context():
            first_count = send_upcoming_job_reminders()
            second_count = send_upcoming_job_reminders()
            booking = db.session.get(ServiceRequest, self.booking_id)

            self.assertEqual(first_count, 1)
            self.assertEqual(second_count, 0)
            self.assertIsNotNone(booking.reminder_sent_at)
            send_email.assert_called_once()


if __name__ == "__main__":
    unittest.main()
