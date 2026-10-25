from datetime import datetime
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from uuid import uuid4

from flask import Blueprint, current_app, request, send_file
from flask_jwt_extended import get_jwt_identity

from ..auth.decorators import roles_required
from ..database import db
from ..location import get_address_from_coordinates, normalize_city_name
from ..models import Customer, Notification, Payment, Review, ServiceArea, ServiceRequest, ServiceType
from ..reports import create_invoice_pdf
from ..tasks import enqueue_task, send_booking_confirmation


customer = Blueprint("customer", __name__)


def find_service_area(location):
    """Prefer an exact PIN match, then allow an admin-approved city match."""
    areas = db.session.scalars(db.select(ServiceArea)).all()
    if location["pin_code"]:
        for area in areas:
            if area.pin_code == location["pin_code"]:
                return area, "pin_code"

    detected_city = normalize_city_name(location["city"])
    if detected_city:
        for area in areas:
            if normalize_city_name(area.city) == detected_city:
                return area, "city"

    return None, None


@customer.get("/dashboard")
@roles_required("customer")
def dashboard():
    user_id = int(get_jwt_identity())
    profile = db.session.scalar(
        db.select(Customer).where(Customer.user_id == user_id)
    )
    if profile is None:
        return {"message": "Customer profile not found"}, 404

    open_bookings = db.session.scalar(
        db.select(db.func.count(ServiceRequest.id)).where(
            ServiceRequest.customer_id == profile.id,
            ServiceRequest.status.in_(["pending", "accepted"]),
        )
    )
    completed_bookings = db.session.scalar(
        db.select(db.func.count(ServiceRequest.id)).where(
            ServiceRequest.customer_id == profile.id,
            ServiceRequest.status == "completed",
        )
    )
    active_booking = db.session.scalar(
        db.select(ServiceRequest)
        .where(
            ServiceRequest.customer_id == profile.id,
            ServiceRequest.status.in_(["pending", "accepted"]),
        )
        .order_by(
            db.case((ServiceRequest.status == "accepted", 0), else_=1),
            ServiceRequest.created_at.desc(),
        )
    )

    return {
        "city": profile.city,
        "open_bookings": open_bookings,
        "completed_bookings": completed_bookings,
        "active_booking": (
            {
                "id": active_booking.id,
                "service": active_booking.service_type.name,
                "status": active_booking.status,
                "scheduled_for": (
                    active_booking.scheduled_for.isoformat()
                    if active_booking.scheduled_for
                    else None
                ),
                "professional": (
                    {
                        "name": active_booking.professional.user.username,
                        "profile_image_url": (
                            f"/api/professional/profiles/"
                            f"{active_booking.professional.id}/photo"
                            if active_booking.professional.photo
                            else None
                        ),
                    }
                    if active_booking.professional
                    else None
                ),
            }
            if active_booking
            else None
        ),
    }, 200


@customer.get("/notifications/unread")
@roles_required("customer")
def unread_notification():
    user_id = int(get_jwt_identity())
    notification = db.session.scalar(
        db.select(Notification)
        .where(
            Notification.user_id == user_id,
            Notification.is_read.is_(False),
        )
        .order_by(Notification.created_at.asc(), Notification.id.asc())
    )

    if notification is None:
        return {"notification": None}, 200

    return {
        "notification": {
            "id": notification.id,
            "message": notification.message,
            "created_at": (
                notification.created_at.isoformat()
                if notification.created_at
                else None
            ),
        }
    }, 200


@customer.patch("/notifications/<int:notification_id>/read")
@roles_required("customer")
def mark_notification_read(notification_id):
    user_id = int(get_jwt_identity())
    notification = db.session.scalar(
        db.select(Notification).where(
            Notification.id == notification_id,
            Notification.user_id == user_id,
        )
    )
    if notification is None:
        return {"message": "Notification not found"}, 404

    notification.is_read = True
    db.session.commit()
    return {"message": "Notification marked as read"}, 200


@customer.get("/services")
@roles_required("customer")
def services():
    user_id = int(get_jwt_identity())
    profile = db.session.scalar(
        db.select(Customer).where(Customer.user_id == user_id)
    )
    if profile is None:
        return {"message": "Customer profile not found"}, 404

    customer_area = db.session.scalar(
        db.select(ServiceArea).where(ServiceArea.pin_code == profile.pinCode)
    )
    service_list = db.session.scalars(
        db.select(ServiceType).order_by(ServiceType.name)
    ).all()

    return {
        "service_area_available": customer_area is not None,
        "customer_area": {
            "city": profile.city,
            "state": profile.state,
            "pin_code": profile.pinCode,
        },
        "services": [
            {
                "id": service.id,
                "name": service.name,
                "description": service.description,
                "price": (
                    str(service.pricing[0].price) if service.pricing else None
                ),
            }
            for service in service_list
        ]
    }, 200


@customer.post("/detect-service-area")
@roles_required("customer")
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

    matched_area, match_method = find_service_area(location)
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
        "match_method": match_method,
    }, 200


@customer.post("/bookings")
@roles_required("customer")
def create_booking():
    user_id = int(get_jwt_identity())
    profile = db.session.scalar(
        db.select(Customer).where(Customer.user_id == user_id)
    )
    if profile is None:
        return {"message": "Customer profile not found"}, 404
    if not profile.is_complete():
        return {
            "message": "Complete your phone number and address before booking",
            "profile_incomplete": True,
        }, 409

    data = request.get_json(silent=True) or {}
    service_type_id = data.get("service_type_id")
    service_pin_code = (data.get("service_pin_code") or "").strip()
    address = (data.get("service_address") or "").strip()
    description = (data.get("description") or "").strip()
    scheduled_for_text = (data.get("scheduled_for") or "").strip()
    service_area_id = data.get("service_area_id")
    latitude = data.get("latitude")
    longitude = data.get("longitude")

    if not isinstance(service_type_id, int):
        return {"message": "Choose a valid service"}, 400
    service_type = db.session.get(ServiceType, service_type_id)
    if service_type is None:
        return {"message": "Service type not found"}, 404
    if not address or not description or not scheduled_for_text or not service_pin_code:
        return {"message": "Schedule, address, PIN code, and problem details are required"}, 400
    if len(address) > 200 or len(description) > 1000:
        return {"message": "Address or problem details are too long"}, 400

    try:
        scheduled_for = datetime.fromisoformat(scheduled_for_text)
    except ValueError:
        return {"message": "Choose a valid schedule"}, 400
    if scheduled_for <= datetime.now():
        return {"message": "Schedule must be in the future"}, 400

    service_area = None
    if isinstance(service_area_id, int):
        service_area = db.session.get(ServiceArea, service_area_id)
    if service_area is None:
        service_area = db.session.scalar(
            db.select(ServiceArea).where(ServiceArea.pin_code == service_pin_code)
        )
    if service_area is None:
        return {"message": "HomeServe is not available at this location"}, 400
    if latitude is not None and (
        not isinstance(latitude, (int, float)) or not -90 <= latitude <= 90
    ):
        return {"message": "A valid latitude is required"}, 400
    if longitude is not None and (
        not isinstance(longitude, (int, float)) or not -180 <= longitude <= 180
    ):
        return {"message": "A valid longitude is required"}, 400
    if not service_type.pricing:
        return {"message": "This service does not have a price yet"}, 400

    booking = ServiceRequest(
        customer_id=profile.id,
        service_type_id=service_type.id,
        service_area_id=service_area.id,
        service_address=address,
        description=description,
        scheduled_for=scheduled_for,
        latitude=latitude,
        longitude=longitude,
        status="payment_pending",
    )
    db.session.add(booking)
    db.session.flush()
    amount = service_type.pricing[0].price
    try:
        commission_rate = Decimal(
            str(current_app.config["PLATFORM_COMMISSION_PERCENT"])
        )
    except (InvalidOperation, ValueError):
        db.session.rollback()
        return {"message": "Platform commission configuration is invalid"}, 500
    if commission_rate < 0 or commission_rate > 100:
        db.session.rollback()
        return {"message": "Platform commission must be between 0 and 100"}, 500
    platform_fee = (amount * commission_rate / 100).quantize(
        Decimal("0.01"),
        rounding=ROUND_HALF_UP,
    )
    payment = Payment(
        service_request_id=booking.id,
        amount=amount,
        commission_rate=commission_rate,
        platform_fee=platform_fee,
        professional_earning=amount - platform_fee,
        payment_method="demo_upi",
        status="pending",
    )
    db.session.add(payment)
    payment.provider_order_id = f"demo_order_{uuid4().hex[:20]}"
    db.session.commit()

    return {
        "message": "Demo payment order created",
        "booking_id": booking.id,
        "demo_payment": {
            "order_id": payment.provider_order_id,
            "amount": str(payment.amount),
            "currency": "INR",
            "payee": "HomeServe Demo",
            "demo_upi_id": "homeserve.demo@upi",
        },
    }, 201


@customer.post("/bookings/<int:booking_id>/complete-demo-payment")
@roles_required("customer")
def complete_demo_payment(booking_id):
    user_id = int(get_jwt_identity())
    profile = db.session.scalar(
        db.select(Customer).where(Customer.user_id == user_id)
    )
    booking = db.session.scalar(
        db.select(ServiceRequest).where(
            ServiceRequest.id == booking_id,
            ServiceRequest.customer_id == profile.id,
        )
    ) if profile else None
    if booking is None or not booking.payments:
        return {"message": "Booking payment not found"}, 404
    if booking.status == "cancelled":
        return {"message": "This booking was cancelled"}, 409

    payment = booking.payments[0]
    if payment.status == "completed":
        return {"message": "Payment was already verified"}, 200

    data = request.get_json(silent=True) or {}
    order_id = data.get("order_id")
    result = data.get("result")
    if order_id != payment.provider_order_id:
        return {"message": "Demo order does not match this booking"}, 400
    if result not in {"success", "failed"}:
        return {"message": "Choose a valid demo payment result"}, 400

    if result == "failed":
        payment.status = "failed"
        db.session.commit()
        return {"message": "Demo payment failed", "payment_status": "failed"}, 200

    payment.provider_payment_id = f"demo_pay_{uuid4().hex[:20]}"
    payment.status = "completed"
    booking.status = "pending"
    db.session.commit()
    enqueue_task(send_booking_confirmation, booking.id)

    return {
        "message": "Demo payment completed and booking confirmed",
        "payment_status": "completed",
    }, 200


@customer.get("/bookings/<int:booking_id>/invoice")
@roles_required("customer")
def download_invoice(booking_id):
    user_id = int(get_jwt_identity())
    profile = db.session.scalar(
        db.select(Customer).where(Customer.user_id == user_id)
    )
    booking = db.session.scalar(
        db.select(ServiceRequest).where(
            ServiceRequest.id == booking_id,
            ServiceRequest.customer_id == profile.id,
        )
    ) if profile else None
    if booking is None:
        return {"message": "Booking not found"}, 404
    if not booking.payments or booking.payments[0].status != "completed":
        return {"message": "Invoice is available only for a completed payment"}, 409

    return send_file(
        create_invoice_pdf(booking),
        mimetype="application/pdf",
        as_attachment=True,
        download_name=f"homeserve-invoice-{booking.id}.pdf",
    )


@customer.patch("/bookings/<int:booking_id>/cancel")
@roles_required("customer")
def cancel_booking(booking_id):
    user_id = int(get_jwt_identity())
    profile = db.session.scalar(
        db.select(Customer).where(Customer.user_id == user_id)
    )
    if profile is None:
        return {"message": "Customer profile not found"}, 404

    booking = db.session.scalar(
        db.select(ServiceRequest)
        .where(
            ServiceRequest.id == booking_id,
            ServiceRequest.customer_id == profile.id,
        )
        .with_for_update()
    )
    if booking is None:
        return {"message": "Booking not found"}, 404
    if booking.professional_id is not None or booking.status not in {
        "payment_pending",
        "pending",
    }:
        return {
            "message": "A booking can be cancelled only before a professional accepts it"
        }, 409

    payment_status = None
    if booking.payments:
        payment = booking.payments[0]
        payment.status = "refunded" if payment.status == "completed" else "cancelled"
        payment_status = payment.status

    booking.status = "cancelled"
    db.session.commit()
    return {
        "message": "Booking cancelled successfully",
        "payment_status": payment_status,
    }, 200


@customer.get("/bookings")
@roles_required("customer")
def bookings():
    user_id = int(get_jwt_identity())
    profile = db.session.scalar(
        db.select(Customer).where(Customer.user_id == user_id)
    )
    if profile is None:
        return {"message": "Customer profile not found"}, 404

    booking_list = db.session.scalars(
        db.select(ServiceRequest)
        .where(ServiceRequest.customer_id == profile.id)
        .order_by(ServiceRequest.created_at.desc())
    ).all()

    professional_ids = {
        booking.professional_id
        for booking in booking_list
        if booking.professional_id is not None
    }
    rating_by_professional = {}
    if professional_ids:
        rating_rows = db.session.execute(
            db.select(
                ServiceRequest.professional_id,
                db.func.avg(Review.rating),
                db.func.count(Review.id),
            )
            .join(Review, Review.service_request_id == ServiceRequest.id)
            .where(ServiceRequest.professional_id.in_(professional_ids))
            .group_by(ServiceRequest.professional_id)
        ).all()
        rating_by_professional = {
            professional_id: (round(float(average_rating), 1), review_count)
            for professional_id, average_rating, review_count in rating_rows
        }

    def assigned_professional(booking):
        if booking.professional is None:
            return None

        average_rating, review_count = rating_by_professional.get(
            booking.professional_id,
            (None, 0),
        )
        return {
            "name": booking.professional.user.username,
            "phone_number": booking.professional.user.phone_number,
            "experience_years": booking.professional.experience_years,
            "average_rating": average_rating,
            "review_count": review_count,
            "profile_image_url": (
                f"/api/professional/profiles/{booking.professional.id}/photo"
                if booking.professional.photo
                else None
            ),
        }

    return {
        "bookings": [
            {
                "id": booking.id,
                "service": booking.service_type.name,
                "professional": (
                    booking.professional.user.username
                    if booking.professional
                    else None
                ),
                "professional_details": assigned_professional(booking),
                "status": booking.status,
                "scheduled_for": (
                    booking.scheduled_for.isoformat()
                    if booking.scheduled_for
                    else None
                ),
                "address": booking.service_address,
                "description": booking.description,
                "service_area": (
                    f"{booking.service_area.city} - {booking.service_area.pin_code}"
                    if booking.service_area
                    else None
                ),
                "latitude": booking.latitude,
                "longitude": booking.longitude,
                "price": (
                    str(booking.payments[0].amount) if booking.payments else None
                ),
                "payment_method": (
                    booking.payments[0].payment_method
                    if booking.payments
                    else None
                ),
                "payment_status": (
                    booking.payments[0].status if booking.payments else None
                ),
                "review": (
                    {
                        "rating": booking.reviews[0].rating,
                        "comment": booking.reviews[0].comment,
                    }
                    if booking.reviews
                    else None
                ),
            }
            for booking in booking_list
        ]
    }, 200


@customer.post("/bookings/<int:booking_id>/review")
@roles_required("customer")
def create_review(booking_id):
    user_id = int(get_jwt_identity())
    profile = db.session.scalar(
        db.select(Customer).where(Customer.user_id == user_id)
    )
    booking = db.session.scalar(
        db.select(ServiceRequest).where(
            ServiceRequest.id == booking_id,
            ServiceRequest.customer_id == profile.id,
        )
    ) if profile else None
    if booking is None:
        return {"message": "Booking not found"}, 404
    if booking.status != "completed" or booking.professional_id is None:
        return {"message": "You can review only a completed booking"}, 409
    if booking.reviews:
        return {"message": "You already reviewed this booking"}, 409

    data = request.get_json(silent=True) or {}
    rating = data.get("rating")
    comment = (data.get("comment") or "").strip()
    if not isinstance(rating, int) or rating < 1 or rating > 5:
        return {"message": "Rating must be between 1 and 5"}, 400
    if len(comment) > 500:
        return {"message": "Review must be 500 characters or fewer"}, 400

    review = Review(
        service_request_id=booking.id,
        rating=rating,
        comment=comment or None,
    )
    db.session.add(review)
    db.session.commit()
    return {"message": "Thank you for your review"}, 201


@customer.get("/profile")
@roles_required("customer")
def profile():
    user_id = int(get_jwt_identity())
    customer_profile = db.session.scalar(
        db.select(Customer).where(Customer.user_id == user_id)
    )
    if customer_profile is None:
        return {"message": "Customer profile not found"}, 404

    return {
        "profile": {
            "username": customer_profile.user.username,
            "email": customer_profile.user.email,
            "phone_number": customer_profile.user.phone_number,
            "address": customer_profile.address,
            "city": customer_profile.city,
            "state": customer_profile.state,
            "pin_code": customer_profile.pinCode,
            "profile_complete": customer_profile.is_complete(),
        }
    }, 200


@customer.patch("/profile")
@roles_required("customer")
def update_profile():
    user_id = int(get_jwt_identity())
    customer_profile = db.session.scalar(
        db.select(Customer).where(Customer.user_id == user_id)
    )
    if customer_profile is None:
        return {"message": "Customer profile not found"}, 404

    data = request.get_json(silent=True) or {}
    address = (data.get("address") or "").strip()
    city = (data.get("city") or "").strip()
    state = (data.get("state") or "").strip()
    pin_code = (data.get("pin_code") or "").strip()
    phone_number = (data.get("phone_number") or "").strip()

    if not phone_number or not address or not city or not state or not pin_code:
        return {
            "message": "Phone number, address, city, state, and PIN code are required"
        }, 400
    if not 7 <= len(phone_number) <= 20:
        return {"message": "Enter a valid phone number"}, 400
    if len(address) > 200 or len(city) > 100 or len(state) > 100 or len(pin_code) > 20:
        return {"message": "One or more profile fields are too long"}, 400

    customer_profile.user.phone_number = phone_number
    customer_profile.address = address
    customer_profile.city = city
    customer_profile.state = state
    customer_profile.pinCode = pin_code
    db.session.commit()

    return {
        "message": "Profile updated successfully",
        "profile_complete": customer_profile.is_complete(),
    }, 200
