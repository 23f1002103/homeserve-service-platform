from datetime import datetime, timedelta

from celery import shared_task
from flask import current_app

from .database import db
from .mailer import send_templated_email
from .models import ServiceRequest


def booking_email_details(booking):
    payment = booking.payments[0] if booking.payments else None
    return {
        "booking": booking,
        "customer_name": booking.customer.user.username,
        "professional_name": (
            booking.professional.user.username if booking.professional else None
        ),
        "service_name": booking.service_type.name,
        "amount": str(payment.amount) if payment else None,
    }


def enqueue_task(task, *args):
    """Queue work without making a Redis outage break the main API action."""
    try:
        task.delay(*args)
    except Exception:
        current_app.logger.exception("Could not queue Celery task %s", task.name)


@shared_task(
    autoretry_for=(OSError,),
    retry_backoff=True,
    retry_kwargs={"max_retries": 3},
)
def send_booking_confirmation(booking_id):
    booking = db.session.get(ServiceRequest, booking_id)
    if booking is None or booking.status == "cancelled":
        return False
    return send_templated_email(
        booking.customer.user.email,
        f"HomeServe booking #{booking.id} confirmed",
        "booking_confirmed",
        **booking_email_details(booking),
    )


@shared_task(
    autoretry_for=(OSError,),
    retry_backoff=True,
    retry_kwargs={"max_retries": 3},
)
def send_booking_completed(booking_id):
    booking = db.session.get(ServiceRequest, booking_id)
    if booking is None or booking.status != "completed":
        return False
    return send_templated_email(
        booking.customer.user.email,
        f"HomeServe job #{booking.id} is complete",
        "booking_completed",
        **booking_email_details(booking),
    )


@shared_task(
    autoretry_for=(OSError,),
    retry_backoff=True,
    retry_kwargs={"max_retries": 3},
)
def send_upcoming_job_reminders():
    """Email professionals once when an accepted job is one hour or less away."""
    now = datetime.now()
    one_hour_from_now = now + timedelta(hours=1)
    jobs = db.session.scalars(
        db.select(ServiceRequest).where(
            ServiceRequest.status == "accepted",
            ServiceRequest.professional_id.is_not(None),
            ServiceRequest.scheduled_for > now,
            ServiceRequest.scheduled_for <= one_hour_from_now,
            ServiceRequest.reminder_sent_at.is_(None),
        )
    ).all()

    sent_count = 0
    for booking in jobs:
        sent = send_templated_email(
            booking.professional.user.email,
            f"Upcoming HomeServe job #{booking.id}",
            "professional_reminder",
            **booking_email_details(booking),
        )
        if sent:
            booking.reminder_sent_at = datetime.now()
            db.session.commit()
            sent_count += 1
    return sent_count
