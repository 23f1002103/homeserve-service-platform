import csv
from datetime import date, datetime, time, timedelta
from decimal import Decimal, InvalidOperation
from io import StringIO

from flask import Blueprint, Response, request

from ..auth.decorators import roles_required
from ..database import db
from ..models import (
    Customer,
    Professional,
    Review,
    ServiceArea,
    ServicePricing,
    ServiceRequest,
    ServiceType,
    User,
)


admin = Blueprint("admin", __name__)


def professional_rating(professional_id):
    job_ids = db.session.scalars(
        db.select(ServiceRequest.id).where(
            ServiceRequest.professional_id == professional_id
        )
    ).all()
    if not job_ids:
        return None, 0

    ratings = db.session.scalars(
        db.select(Review.rating).where(Review.service_request_id.in_(job_ids))
    ).all()
    if not ratings:
        return None, 0
    return round(sum(ratings) / len(ratings), 1), len(ratings)


def platform_revenue(start_at=None, end_at=None):
    query = db.select(ServiceRequest).where(ServiceRequest.status == "completed")
    if start_at is not None:
        query = query.where(ServiceRequest.completed_at >= start_at)
    if end_at is not None:
        query = query.where(ServiceRequest.completed_at < end_at)

    jobs = db.session.scalars(query).all()
    return sum(
        (
            job.payments[0].platform_fee
            for job in jobs
            if job.payments and job.payments[0].status == "completed"
        ),
        Decimal("0.00"),
    )


def revenue_jobs(start_at=None, end_at=None):
    query = db.select(ServiceRequest).where(ServiceRequest.status == "completed")
    if start_at is not None:
        query = query.where(ServiceRequest.completed_at >= start_at)
    if end_at is not None:
        query = query.where(ServiceRequest.completed_at < end_at)
    jobs = db.session.scalars(
        query.order_by(ServiceRequest.completed_at.desc())
    ).all()
    return [
        job
        for job in jobs
        if job.payments and job.payments[0].status == "completed"
    ]


def revenue_totals(jobs):
    return {
        "completed_jobs": len(jobs),
        "gross_payments": str(
            sum((job.payments[0].amount for job in jobs), Decimal("0.00"))
        ),
        "platform_revenue": str(
            sum((job.payments[0].platform_fee for job in jobs), Decimal("0.00"))
        ),
        "professional_payouts": str(
            sum(
                (job.payments[0].professional_earning for job in jobs),
                Decimal("0.00"),
            )
        ),
    }


@admin.get("/dashboard")
@roles_required("admin")
def dashboard():
    customer_count = db.session.scalar(
        db.select(db.func.count(User.id)).where(User.role == "customer")
    )
    professional_count = db.session.scalar(
        db.select(db.func.count(User.id)).where(User.role == "professional")
    )
    pending_professional_count = db.session.scalar(
        db.select(db.func.count(Professional.id)).where(
            Professional.approval_status == "pending"
        )
    )
    open_request_count = db.session.scalar(
        db.select(db.func.count(ServiceRequest.id)).where(
            ServiceRequest.status.in_(["pending", "accepted"])
        )
    )
    pending_request_count = db.session.scalar(
        db.select(db.func.count(ServiceRequest.id)).where(
            ServiceRequest.status == "pending"
        )
    )
    accepted_request_count = db.session.scalar(
        db.select(db.func.count(ServiceRequest.id)).where(
            ServiceRequest.status == "accepted"
        )
    )
    completed_request_count = db.session.scalar(
        db.select(db.func.count(ServiceRequest.id)).where(
            ServiceRequest.status == "completed"
        )
    )
    today_start = datetime.combine(date.today(), time.min)
    tomorrow_start = today_start + timedelta(days=1)

    return {
        "counts": {
            "customers": customer_count,
            "professionals": professional_count,
            "pending_professionals": pending_professional_count,
            "open_requests": open_request_count,
        },
        "requests": {
            "pending": pending_request_count,
            "accepted": accepted_request_count,
            "completed": completed_request_count,
        },
        "revenue": {
            "today": str(platform_revenue(today_start, tomorrow_start)),
            "total": str(platform_revenue()),
        },
    }, 200


@admin.get("/professionals")
@roles_required("admin")
def professionals():
    professional_list = db.session.scalars(
        db.select(Professional).order_by(Professional.id.desc())
    ).all()

    results = []
    for professional in professional_list:
        average_rating, review_count = professional_rating(professional.id)
        results.append(
            {
                "id": professional.id,
                "username": professional.user.username,
                "email": professional.user.email,
                "phone_number": professional.user.phone_number,
                "service": professional.service_type.name,
                "city": professional.city,
                "experience_years": professional.experience_years,
                "approval_status": professional.approval_status,
                "block_reason": professional.block_reason,
                "average_rating": average_rating,
                "review_count": review_count,
            }
        )

    return {"professionals": results}, 200


@admin.get("/revenue")
@roles_required("admin")
def revenue():
    today = date.today()
    default_start = today.replace(day=1)
    start_text = (request.args.get("start_date") or default_start.isoformat()).strip()
    end_text = (request.args.get("end_date") or today.isoformat()).strip()

    try:
        start_date = date.fromisoformat(start_text)
        end_date = date.fromisoformat(end_text)
    except ValueError:
        return {"message": "Choose valid start and end dates"}, 400
    if start_date > end_date:
        return {"message": "Start date cannot be after end date"}, 400

    start_at = datetime.combine(start_date, time.min)
    end_at = datetime.combine(end_date + timedelta(days=1), time.min)
    selected_jobs = revenue_jobs(start_at, end_at)
    all_jobs = revenue_jobs()

    return {
        "range": {
            "start": start_date.isoformat(),
            "end": end_date.isoformat(),
        },
        "selected": revenue_totals(selected_jobs),
        "all_time": revenue_totals(all_jobs),
        "transactions": [
            {
                "booking_id": job.id,
                "service": job.service_type.name,
                "customer": job.customer.user.username,
                "professional": job.professional.user.username,
                "completed_at": job.completed_at.isoformat(),
                "gross_amount": str(job.payments[0].amount),
                "commission_rate": str(job.payments[0].commission_rate),
                "platform_fee": str(job.payments[0].platform_fee),
                "professional_payout": str(job.payments[0].professional_earning),
            }
            for job in selected_jobs
        ],
    }, 200


@admin.get("/revenue/export")
@roles_required("admin")
def export_revenue():
    start_text = (request.args.get("start_date") or "").strip()
    end_text = (request.args.get("end_date") or "").strip()
    try:
        start_date = date.fromisoformat(start_text)
        end_date = date.fromisoformat(end_text)
    except ValueError:
        return {"message": "Choose valid start and end dates"}, 400
    if start_date > end_date:
        return {"message": "Start date cannot be after end date"}, 400

    start_at = datetime.combine(start_date, time.min)
    end_at = datetime.combine(end_date + timedelta(days=1), time.min)
    jobs = revenue_jobs(start_at, end_at)

    output = StringIO(newline="")
    writer = csv.writer(output)
    writer.writerow([
        "Booking ID",
        "Completed At",
        "Service",
        "Customer",
        "Professional",
        "Customer Paid (INR)",
        "Commission Rate (%)",
        "HomeServe Revenue (INR)",
        "Professional Payout (INR)",
    ])
    for job in jobs:
        payment = job.payments[0]
        writer.writerow([
            job.id,
            job.completed_at.isoformat(),
            job.service_type.name,
            job.customer.user.username,
            job.professional.user.username,
            payment.amount,
            payment.commission_rate,
            payment.platform_fee,
            payment.professional_earning,
        ])

    filename = f"homeserve-revenue-{start_date}-to-{end_date}.csv"
    return Response(
        output.getvalue().encode("utf-8-sig"),
        mimetype="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@admin.get("/customers")
@roles_required("admin")
def customers():
    customer_list = db.session.scalars(
        db.select(Customer).order_by(Customer.id.desc())
    ).all()

    return {
        "customers": [
            {
                "id": customer.id,
                "username": customer.user.username,
                "email": customer.user.email,
                "phone_number": customer.user.phone_number,
                "city": customer.city,
                "state": customer.state,
                "pin_code": customer.pinCode,
            }
            for customer in customer_list
        ]
    }, 200


@admin.get("/service-types")
@roles_required("admin")
def service_types():
    service_type_list = db.session.scalars(
        db.select(ServiceType).order_by(ServiceType.name)
    ).all()

    return {
        "service_types": [
            {
                "id": service_type.id,
                "name": service_type.name,
                "description": service_type.description,
                "base_price": (
                    str(service_type.pricing[0].price)
                    if service_type.pricing
                    else None
                ),
            }
            for service_type in service_type_list
        ]
    }, 200


@admin.get("/requests")
@roles_required("admin")
def service_requests():
    request_list = db.session.scalars(
        db.select(ServiceRequest).order_by(ServiceRequest.created_at.desc())
    ).all()

    return {
        "requests": [
            {
                "id": service_request.id,
                "service": service_request.service_type.name,
                "customer": service_request.customer.user.username,
                "professional": (
                    service_request.professional.user.username
                    if service_request.professional
                    else None
                ),
                "status": service_request.status,
                "scheduled_for": (
                    service_request.scheduled_for.isoformat()
                    if service_request.scheduled_for
                    else None
                ),
                "address": service_request.service_address,
            }
            for service_request in request_list
        ]
    }, 200


@admin.post("/service-types")
@roles_required("admin")
def create_service_type():
    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()
    description = (data.get("description") or "").strip()
    price_input = data.get("base_price")

    if not name:
        return {"message": "Service name is required"}, 400
    if len(description) > 180:
        return {"message": "Description must be 180 characters or fewer"}, 400

    price = None
    if price_input not in (None, ""):
        try:
            price = Decimal(str(price_input))
        except (InvalidOperation, ValueError):
            return {"message": "Enter a valid base price"}, 400
        if price <= 0:
            return {"message": "Base price must be greater than zero"}, 400

    existing_service = db.session.scalar(
        db.select(ServiceType).where(db.func.lower(ServiceType.name) == name.lower())
    )
    if existing_service is not None:
        return {"message": "This service type already exists"}, 409

    service_type = ServiceType(name=name, description=description or None)
    db.session.add(service_type)
    db.session.flush()
    if price is not None:
        db.session.add(ServicePricing(service_type_id=service_type.id, price=price))
    db.session.commit()

    return {
        "message": "Service type created successfully",
        "service_type": {
            "id": service_type.id,
            "name": service_type.name,
            "description": service_type.description,
            "base_price": str(price) if price is not None else None,
        },
    }, 201


@admin.patch("/service-types/<int:service_type_id>/price")
@roles_required("admin")
def update_service_price(service_type_id):
    service_type = db.session.get(ServiceType, service_type_id)
    if service_type is None:
        return {"message": "Service type not found"}, 404

    data = request.get_json(silent=True) or {}
    try:
        price = Decimal(str(data.get("base_price")))
    except (InvalidOperation, ValueError):
        return {"message": "Enter a valid base price"}, 400

    if price <= 0:
        return {"message": "Base price must be greater than zero"}, 400

    service_price = db.session.scalar(
        db.select(ServicePricing).where(
            ServicePricing.service_type_id == service_type_id
        )
    )
    if service_price is None:
        service_price = ServicePricing(service_type_id=service_type_id, price=price)
        db.session.add(service_price)
    else:
        service_price.price = price

    db.session.commit()
    return {"message": "Service price updated successfully"}, 200


@admin.delete("/service-types/<int:service_type_id>")
@roles_required("admin")
def delete_service_type(service_type_id):
    service_type = db.session.get(ServiceType, service_type_id)
    if service_type is None:
        return {"message": "Service type not found"}, 404

    professional_count = db.session.scalar(
        db.select(db.func.count(Professional.id)).where(
            Professional.service_type_id == service_type_id
        )
    )
    booking_count = db.session.scalar(
        db.select(db.func.count(ServiceRequest.id)).where(
            ServiceRequest.service_type_id == service_type_id
        )
    )
    if professional_count or booking_count:
        return {
            "message": (
                "This service cannot be deleted because professionals or "
                "bookings already use it"
            )
        }, 409

    prices = db.session.scalars(
        db.select(ServicePricing).where(
            ServicePricing.service_type_id == service_type_id
        )
    ).all()
    for price in prices:
        db.session.delete(price)
    db.session.delete(service_type)
    db.session.commit()
    return {"message": "Service deleted successfully"}, 200


@admin.get("/service-areas")
@roles_required("admin")
def service_areas():
    area_list = db.session.scalars(
        db.select(ServiceArea).order_by(ServiceArea.state, ServiceArea.city)
    ).all()

    return {
        "service_areas": [
            {
                "id": area.id,
                "city": area.city,
                "state": area.state,
                "pin_code": area.pin_code,
                "professional_count": len(area.professionals),
                "demand_count": len(area.service_requests),
            }
            for area in area_list
        ]
    }, 200


@admin.post("/service-areas")
@roles_required("admin")
def create_service_area():
    data = request.get_json(silent=True) or {}
    city = (data.get("city") or "").strip()
    state = (data.get("state") or "").strip()
    pin_code = (data.get("pin_code") or "").strip()

    if not city or not state or not pin_code:
        return {"message": "City, state, and PIN code are required"}, 400

    existing_area = db.session.scalar(
        db.select(ServiceArea).where(ServiceArea.pin_code == pin_code)
    )
    if existing_area is not None:
        return {"message": "This PIN code is already a service area"}, 409

    area = ServiceArea(city=city, state=state, pin_code=pin_code)
    db.session.add(area)
    db.session.commit()

    return {
        "message": "Service area created successfully",
        "service_area": {
            "id": area.id,
            "city": area.city,
            "state": area.state,
            "pin_code": area.pin_code,
        },
    }, 201


@admin.delete("/service-areas/<int:area_id>")
@roles_required("admin")
def delete_service_area(area_id):
    area = db.session.get(ServiceArea, area_id)
    if area is None:
        return {"message": "Service area not found"}, 404

    if area.professionals:
        return {
            "message": "This area cannot be deleted because professionals are using it"
        }, 409

    db.session.delete(area)
    db.session.commit()
    return {"message": "Service area deleted successfully"}, 200


@admin.patch("/professionals/<int:professional_id>/status")
@roles_required("admin")
def update_professional_status(professional_id):
    professional = db.session.get(Professional, professional_id)
    if professional is None:
        return {"message": "Professional not found"}, 404

    data = request.get_json(silent=True) or {}
    status = (data.get("status") or "").strip().lower()
    reason = (data.get("reason") or "").strip()

    if status not in {"pending", "approved", "blocked"}:
        return {"message": "Status must be pending, approved, or blocked"}, 400
    if status == "blocked" and not reason:
        return {"message": "A reason is required when blocking an application"}, 400
    if status == "blocked":
        active_job = db.session.scalar(
            db.select(ServiceRequest).where(
                ServiceRequest.professional_id == professional.id,
                ServiceRequest.status == "accepted",
            )
        )
        if active_job is not None:
            return {
                "message": "This professional has an active job and cannot be blocked until it is completed"
            }, 409

    professional.approval_status = status
    professional.block_reason = reason if status == "blocked" else None
    db.session.commit()

    return {"message": f"Professional marked as {status}", "status": status}, 200

