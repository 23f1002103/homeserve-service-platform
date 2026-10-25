from datetime import UTC, datetime

from flask import Blueprint, jsonify

from .database import db
from .models import ServiceType


api = Blueprint("api", __name__)


@api.get("")
def api_home():
    """Describe the API and point clients to its health endpoint."""
    return jsonify(
        {
            "message": "Welcome to the HomeServe API",
            "endpoints": {
                "health": "/api/health",
                "landing": "/api/landing",
            },
        }
    )


@api.get("/landing")
def landing_page():
    """Return the public content needed to render the landing page."""
    services = db.session.scalars(
        db.select(ServiceType).order_by(ServiceType.name)
    ).all()

    return jsonify(
        {
            "hero": {
                "eyebrow": "Trusted help for every home",
                "title": "Your home deserves expert care.",
                "description": (
                    "Book verified professionals for repairs, cleaning, and "
                    "everyday home maintenance—without the usual hassle."
                ),
            },
            "services": [
                {
                    "id": service.id,
                    "name": service.name,
                    "description": service.description,
                    "price": (
                        str(service.pricing[0].price)
                        if service.pricing
                        else None
                    ),
                }
                for service in services
            ],
            "highlights": [
                {
                    "value": "Verified",
                    "label": "Professionals you can identify",
                    "description": (
                        "Every professional profile is reviewed by the "
                        "administrator before they can accept work."
                    ),
                },
                {
                    "value": "Upfront",
                    "label": "A price before you continue",
                    "description": (
                        "See the base service price before creating your "
                        "request or entering the payment demo."
                    ),
                },
                {
                    "value": "Simple",
                    "label": "One clear booking journey",
                    "description": (
                        "Book, follow job updates, download your invoice, "
                        "and leave a review from one account."
                    ),
                },
            ],
        }
    )


@api.get("/health")
def health_check():
    """Return a small response proving that the API is available."""
    return jsonify(
        {
            "message": "HomeServe API is connected",
            "service": "homeserve-api",
            "status": "ok",
            "timestamp": datetime.now(UTC).isoformat(),
        }
    )


@api.get("/service-types")
def service_types():
    """Return service choices for public forms such as registration."""
    services = db.session.scalars(
        db.select(ServiceType).order_by(ServiceType.name)
    ).all()

    return {
        "service_types": [
            {
                "id": service.id,
                "name": service.name,
                "description": service.description,
                "base_price": (
                    str(service.pricing[0].price) if service.pricing else None
                ),
            }
            for service in services
        ]
    }, 200


