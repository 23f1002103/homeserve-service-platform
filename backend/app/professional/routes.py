from datetime import date, datetime, time, timedelta
from decimal import Decimal

from flask import Blueprint, request
from flask_jwt_extended import get_jwt_identity

from ..auth.decorators import roles_required
from ..database import db
from ..location import get_address_from_coordinates
from ..models import Notification, Professional, Review, ServiceArea, ServiceRequest
from ..tasks import enqueue_task, send_booking_completed


professional = Blueprint("professional", __name__)


def directions_url(job):
    if job.latitude is None or job.longitude is None:
        return None
    return (
        "https://www.google.com/maps/dir/?api=1&destination="
        f"{job.latitude},{job.longitude}"
    )


def earning_jobs(professional_id, start_at, end_at):
    jobs = db.session.scalars(
        db.select(ServiceRequest)
        .where(
            ServiceRequest.professional_id == professional_id,
            ServiceRequest.status == "completed",
            ServiceRequest.completed_at >= start_at,
            ServiceRequest.completed_at < end_at,
        )
        .order_by(ServiceRequest.completed_at.desc())
    ).all()
    return [
        job
        for job in jobs
        if job.payments and job.payments[0].status == "completed"
    ]


def total_professional_earnings(jobs):
    return sum(
        (job.payments[0].professional_earning for job in jobs),
        Decimal("0.00"),
    )


@professional.get("/dashboard")
@roles_required("professional")
def dashboard():
    user_id = int(get_jwt_identity())
    profile = db.session.scalar(
        db.select(Professional).where(Professional.user_id == user_id)
    )
    if profile is None:
        return {"message": "Professional profile not found"}, 404

    accepted_jobs = db.session.scalar(
        db.select(db.func.count(ServiceRequest.id)).where(
            ServiceRequest.professional_id == profile.id,
            ServiceRequest.status == "accepted",
        )
    )
    completed_jobs = db.session.scalar(
        db.select(db.func.count(ServiceRequest.id)).where(
            ServiceRequest.professional_id == profile.id,
            ServiceRequest.status == "completed",
        )
    )
    today = date.today()
    today_start = datetime.combine(today, time.min)
    tomorrow_start = today_start + timedelta(days=1)
    today_earning = total_professional_earnings(
        earning_jobs(profile.id, today_start, tomorrow_start)
    )

    return {
        "approval_status": profile.approval_status,
        "block_reason": profile.block_reason,
        "service": profile.service_type.name,
        "city": profile.city,
        "experience_years": profile.experience_years,
        "accepted_jobs": accepted_jobs,
        "completed_jobs": completed_jobs,
        "today_earning": str(today_earning),
        "service_area_count": len(profile.service_areas),
    }, 200


@professional.get("/jobs")
@roles_required("professional")
def jobs():
    user_id = int(get_jwt_identity())
    profile = db.session.scalar(
        db.select(Professional).where(Professional.user_id == user_id)
    )
    if profile is None:
        return {"message": "Professional profile not found"}, 404

    assigned_jobs = db.session.scalars(
        db.select(ServiceRequest)
        .where(ServiceRequest.professional_id == profile.id)
        .order_by(ServiceRequest.created_at.desc())
    ).all()
    has_active_job = any(job.status == "accepted" for job in assigned_jobs)

    available_jobs = []
    area_ids = [area.id for area in profile.service_areas]
    if profile.approval_status == "approved" and area_ids and not has_active_job:
        available_jobs = db.session.scalars(
            db.select(ServiceRequest)
            .where(
                ServiceRequest.professional_id.is_(None),
                ServiceRequest.status == "pending",
                ServiceRequest.service_type_id == profile.service_type_id,
                ServiceRequest.service_area_id.in_(area_ids),
            )
            .order_by(ServiceRequest.created_at.desc())
        ).all()

    return {
        "jobs": [
            {
                "id": job.id,
                "service": job.service_type.name,
                "customer": job.customer.user.username,
                "customer_phone": job.customer.user.phone_number,
                "status": job.status,
                "scheduled_for": (
                    job.scheduled_for.isoformat() if job.scheduled_for else None
                ),
                "address": job.service_address,
                "description": job.description,
                "directions_url": directions_url(job),
            }
            for job in assigned_jobs
        ],
        "available_jobs": [
            {
                "id": job.id,
                "service": job.service_type.name,
                "area": (
                    f"{job.service_area.city} - {job.service_area.pin_code}"
                    if job.service_area
                    else "Area unavailable"
                ),
                "status": "available",
                "scheduled_for": (
                    job.scheduled_for.isoformat() if job.scheduled_for else None
                ),
                "description": job.description,
                "price": (
                    str(job.payments[0].amount) if job.payments else None
                ),
            }
            for job in available_jobs
        ],
        "can_accept_jobs": profile.approval_status == "approved",
        "has_active_job": has_active_job,
    }, 200


@professional.patch("/jobs/<int:job_id>/accept")
@roles_required("professional")
def accept_job(job_id):
    user_id = int(get_jwt_identity())
    profile = db.session.scalar(
        db.select(Professional)
        .where(Professional.user_id == user_id)
        .with_for_update()
    )
    if profile is None:
        return {"message": "Professional profile not found"}, 404
    if profile.approval_status != "approved":
        return {"message": "Admin approval is required before accepting jobs"}, 403

    active_job = db.session.scalar(
        db.select(ServiceRequest).where(
            ServiceRequest.professional_id == profile.id,
            ServiceRequest.status == "accepted",
        )
    )
    if active_job is not None:
        return {
            "message": "Complete your current job before accepting another booking"
        }, 409

    job = db.session.scalar(
        db.select(ServiceRequest)
        .where(ServiceRequest.id == job_id)
        .with_for_update()
    )
    if job is None:
        return {"message": "Job not found"}, 404
    if job.professional_id is not None or job.status != "pending":
        return {"message": "This job is no longer available"}, 409
    if job.service_type_id != profile.service_type_id:
        return {"message": "This job does not match your service type"}, 403

    professional_area_ids = [area.id for area in profile.service_areas]
    if job.service_area_id not in professional_area_ids:
        return {"message": "This job is outside your selected service areas"}, 403

    job.professional_id = profile.id
    job.status = "accepted"
    db.session.add(
        Notification(
            user_id=job.customer.user_id,
            message=(
                f"{profile.user.username} accepted your "
                f"{job.service_type.name} booking #{job.id}."
            ),
        )
    )
    db.session.commit()

    return {"message": "Job accepted successfully"}, 200


@professional.patch("/jobs/<int:job_id>/complete")
@roles_required("professional")
def complete_job(job_id):
    user_id = int(get_jwt_identity())
    profile = db.session.scalar(
        db.select(Professional).where(Professional.user_id == user_id)
    )
    if profile is None:
        return {"message": "Professional profile not found"}, 404

    job = db.session.get(ServiceRequest, job_id)
    if job is None or job.professional_id != profile.id:
        return {"message": "Assigned job not found"}, 404
    if job.status != "accepted":
        return {"message": "Only an accepted job can be completed"}, 409

    job.status = "completed"
    job.completed_at = datetime.now()
    db.session.commit()
    enqueue_task(send_booking_completed, job.id)
    return {"message": "Job marked as completed"}, 200


@professional.get("/earnings")
@roles_required("professional")
def earnings():
    user_id = int(get_jwt_identity())
    profile = db.session.scalar(
        db.select(Professional).where(Professional.user_id == user_id)
    )
    if profile is None:
        return {"message": "Professional profile not found"}, 404

    week_value = (request.args.get("week") or "").strip()
    try:
        if week_value:
            year_text, week_text = week_value.split("-W")
            week_start = date.fromisocalendar(int(year_text), int(week_text), 1)
        else:
            today = date.today()
            week_start = today - timedelta(days=today.weekday())
    except (ValueError, TypeError):
        return {"message": "Choose a valid week"}, 400

    week_end = week_start + timedelta(days=6)
    start_at = datetime.combine(week_start, time.min)
    end_at = start_at + timedelta(days=7)
    jobs = earning_jobs(profile.id, start_at, end_at)

    return {
        "week": {
            "value": f"{week_start.isocalendar().year}-W{week_start.isocalendar().week:02d}",
            "start": week_start.isoformat(),
            "end": week_end.isoformat(),
        },
        "total_earning": str(total_professional_earnings(jobs)),
        "completed_jobs": [
            {
                "id": job.id,
                "service": job.service_type.name,
                "customer": job.customer.user.username,
                "completed_at": job.completed_at.isoformat(),
                "gross_amount": str(job.payments[0].amount),
                "commission_rate": str(job.payments[0].commission_rate),
                "platform_fee": str(job.payments[0].platform_fee),
                "earning": str(job.payments[0].professional_earning),
            }
            for job in jobs
        ],
    }, 200


@professional.get("/profile")
@roles_required("professional")
def profile():
    user_id = int(get_jwt_identity())
    professional_profile = db.session.scalar(
        db.select(Professional).where(Professional.user_id == user_id)
    )
    if professional_profile is None:
        return {"message": "Professional profile not found"}, 404

    job_ids = db.session.scalars(
        db.select(ServiceRequest.id).where(
            ServiceRequest.professional_id == professional_profile.id
        )
    ).all()
    reviews = []
    if job_ids:
        reviews = db.session.scalars(
            db.select(Review).where(Review.service_request_id.in_(job_ids))
        ).all()
    average_rating = (
        round(sum(review.rating for review in reviews) / len(reviews), 1)
        if reviews
        else None
    )

    return {
        "profile": {
            "username": professional_profile.user.username,
            "email": professional_profile.user.email,
            "phone_number": professional_profile.user.phone_number,
            "service": professional_profile.service_type.name,
            "experience_years": professional_profile.experience_years,
            "address": professional_profile.address,
            "city": professional_profile.city,
            "state": professional_profile.state,
            "pin_code": professional_profile.pin_code,
            "approval_status": professional_profile.approval_status,
            "average_rating": average_rating,
            "review_count": len(reviews),
        }
    }, 200


@professional.patch("/profile")
@roles_required("professional")
def update_profile():
    user_id = int(get_jwt_identity())
    professional_profile = db.session.scalar(
        db.select(Professional).where(Professional.user_id == user_id)
    )
    if professional_profile is None:
        return {"message": "Professional profile not found"}, 404

    data = request.get_json(silent=True) or {}
    address = (data.get("address") or "").strip()
    city = (data.get("city") or "").strip()
    state = (data.get("state") or "").strip()
    pin_code = (data.get("pin_code") or "").strip()
    experience_years = data.get("experience_years")

    if not address or not city or not state or not pin_code:
        return {"message": "Address, city, state, and PIN code are required"}, 400
    if experience_years is not None and not isinstance(experience_years, int):
        return {"message": "Experience must be a whole number"}, 400
    if experience_years is not None and experience_years < 0:
        return {"message": "Experience cannot be negative"}, 400

    professional_profile.user.phone_number = (
        (data.get("phone_number") or "").strip() or None
    )
    professional_profile.experience_years = experience_years
    professional_profile.address = address
    professional_profile.city = city
    professional_profile.state = state
    professional_profile.pin_code = pin_code
    db.session.commit()

    return {"message": "Profile updated successfully"}, 200


@professional.get("/service-areas")
@roles_required("professional")
def service_areas():
    user_id = int(get_jwt_identity())
    profile = db.session.scalar(
        db.select(Professional).where(Professional.user_id == user_id)
    )
    if profile is None:
        return {"message": "Professional profile not found"}, 404

    available_areas = db.session.scalars(
        db.select(ServiceArea).order_by(ServiceArea.state, ServiceArea.city)
    ).all()

    return {
        "available_areas": [
            {
                "id": area.id,
                "city": area.city,
                "state": area.state,
                "pin_code": area.pin_code,
            }
            for area in available_areas
        ],
        "selected_area_ids": [area.id for area in profile.service_areas],
    }, 200


@professional.patch("/service-areas")
@roles_required("professional")
def update_service_areas():
    user_id = int(get_jwt_identity())
    profile = db.session.scalar(
        db.select(Professional).where(Professional.user_id == user_id)
    )
    if profile is None:
        return {"message": "Professional profile not found"}, 404

    data = request.get_json(silent=True) or {}
    area_ids = data.get("area_ids")
    if not isinstance(area_ids, list) or any(
        not isinstance(area_id, int) for area_id in area_ids
    ):
        return {"message": "area_ids must be a list of numbers"}, 400

    if area_ids:
        selected_areas = db.session.scalars(
            db.select(ServiceArea).where(ServiceArea.id.in_(area_ids))
        ).all()
    else:
        selected_areas = []

    if len(selected_areas) != len(area_ids):
        return {"message": "One or more service areas do not exist"}, 400

    profile.service_areas = selected_areas
    db.session.commit()
    return {"message": "Service areas updated successfully"}, 200


@professional.post("/detect-service-area")
@roles_required("professional")
def detect_service_area():
    data = request.get_json(silent=True) or {}
    latitude = data.get("latitude")
    longitude = data.get("longitude")

    if not isinstance(latitude, (int, float)) or not -90 <= latitude <= 90:
        return {"message": "A valid latitude is required"}, 400
    if not isinstance(longitude, (int, float)) or not -180 <= longitude <= 180:
        return {"message": "A valid longitude is required"}, 400

    location = get_address_from_coordinates(latitude, longitude)
    if location is None:
        return {"message": "Location lookup is temporarily unavailable"}, 503

    matched_area = None
    if location["pin_code"]:
        matched_area = db.session.scalar(
            db.select(ServiceArea).where(
                ServiceArea.pin_code == location["pin_code"]
            )
        )

    return {
        "detected_location": location,
        "matched_area": (
            {
                "id": matched_area.id,
                "city": matched_area.city,
                "state": matched_area.state,
                "pin_code": matched_area.pin_code,
            }
            if matched_area
            else None
        ),
    }, 200
