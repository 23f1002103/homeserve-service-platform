import re
import secrets

from flask import Blueprint, current_app, request
from flask_jwt_extended import create_access_token, get_jwt_identity, jwt_required
from google.auth.exceptions import GoogleAuthError
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token as google_id_token
from sqlalchemy.exc import IntegrityError
from werkzeug.security import check_password_hash, generate_password_hash

from ..database import db
from ..models import Customer, Professional, ServiceType, User

auth = Blueprint("auth", __name__)


def user_data(user):
    """Return the safe account fields needed by the Vue application."""
    data = {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "role": user.role,
    }
    if user.role == "customer" and user.customer is not None:
        data["profile_complete"] = user.customer.is_complete()
    if user.role == "professional" and user.professional is not None:
        data["approval_status"] = user.professional.approval_status
        data["block_reason"] = user.professional.block_reason
    return data


def create_session_response(user, message="Login successful"):
    if user.role == "professional" and user.professional is not None:
        user.professional.active_service_area = None
        user.professional.location_verified_at = None
        db.session.commit()

    return {
        "message": message,
        "access_token": create_access_token(
            identity=str(user.id),
            additional_claims={"role": user.role},
        ),
        "user": user_data(user),
    }


def verify_google_token(credential, client_id):
    """Verify a Google ID credential using Google's maintained library."""
    return google_id_token.verify_oauth2_token(
        credential,
        google_requests.Request(),
        client_id,
    )


def available_google_username(name, email):
    raw_name = name or email.split("@", 1)[0]
    base = re.sub(r"[^A-Za-z0-9_.-]+", "", raw_name).strip("._-")
    base = (base or "google_customer")[:70]
    candidate = base
    number = 2
    while db.session.scalar(db.select(User.id).where(User.username == candidate)):
        candidate = f"{base[:70]}-{number}"
        number += 1
    return candidate

@auth.get("/health")
def auth_health():
    return {"status": "ok"}


@auth.post("/register")
def register():
    data = request.get_json(silent=True) or {}

    username = (data.get("username") or "").strip()
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""
    role = (data.get("role") or "").strip().lower()
    phone_number = (data.get("phone_number") or "").strip()

    if not username or not email or not password or not role:
        return {
            "message": "Username, email, password, and role are required"
        }, 400

    if role not in {"customer", "professional"}:
        return {
            "message": "Role must be either customer or professional"
        }, 400

    if role == "customer" and not phone_number:
        return {"message": "Phone number is required for customer bookings"}, 400
    if phone_number and not 7 <= len(phone_number) <= 20:
        return {"message": "Enter a valid phone number"}, 400

    existing_user=db.session.scalar(db.select(User).where((User.username==username) | (User.email==email)))
    
    if existing_user is not None:
        return {
            "message": "Username or email already exists"
        }, 409

    if len(password) < 8:
        return {
            "message": "Password must contain at least 8 characters"
        }, 400

    address = (data.get("address") or "").strip()
    city = (data.get("city") or "").strip()
    state = (data.get("state") or "").strip()
    pin_code = (data.get("pin_code") or "").strip()

    if not address or not city or not state or not pin_code:
        return {
            "message": "Address, city, state, and pin_code are required"
        }, 400

    service_type = None
    if role == "professional":
        service_type_id = data.get("service_type_id")
        if not isinstance(service_type_id, int):
            return {"message": "A valid service_type_id is required"}, 400

        service_type = db.session.get(ServiceType, service_type_id)
        if service_type is None:
            return {"message": "Service type does not exist"}, 400

    user = User(
        username=username,
        email=email,
        phone_number=phone_number or None,
        password_hash=generate_password_hash(password),
        role=role,
    )

    try:
        db.session.add(user)
        db.session.flush()

        if role == "customer":
            profile = Customer(
                user_id=user.id,
                address=address,
                city=city,
                state=state,
                pinCode=pin_code,
            )
        else:
            experience_years = data.get("experience_years")
            if experience_years is not None and not isinstance(experience_years, int):
                db.session.rollback()
                return {"message": "experience_years must be an integer"}, 400

            profile = Professional(
                user_id=user.id,
                address=address,
                city=city,
                state=state,
                pin_code=pin_code,
                service_type_id=service_type.id,
                experience_years=experience_years,
            )

        db.session.add(profile)
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return {"message": "Username or email already exists"}, 409

    response_body = {
        "message": "User registered successfully",
        "user": user_data(user),
    }

    if role == "professional":
        response_body["user"]["approval_status"] = profile.approval_status
        response_body["access_token"] = create_access_token(
            identity=str(user.id),
            additional_claims={"role": user.role},
        )

    return response_body, 201


@auth.post("/login")
def login():
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    if not email or not password:
        return {"message": "Email and password are required"}, 400

    user = db.session.scalar(db.select(User).where(User.email == email))
    if user is None or not check_password_hash(user.password_hash, password):
        return {"message": "Invalid email or password"}, 401

    return create_session_response(user), 200


@auth.get("/google/config")
def google_config():
    """Expose the public client ID only when Google login is configured."""
    client_id = current_app.config.get("GOOGLE_CLIENT_ID")
    return {
        "enabled": bool(client_id),
        "client_id": client_id if client_id else None,
    }, 200


@auth.post("/google")
def google_login():
    """Create or sign in a customer after verifying a Google ID token."""
    client_id = current_app.config.get("GOOGLE_CLIENT_ID")
    if not client_id:
        return {"message": "Google sign-in is not configured"}, 503

    data = request.get_json(silent=True) or {}
    credential = data.get("credential")
    if not isinstance(credential, str) or not credential:
        return {"message": "Google credential is required"}, 400

    try:
        identity = verify_google_token(credential, client_id)
    except (ValueError, GoogleAuthError):
        return {"message": "Google sign-in could not be verified"}, 401

    google_subject = identity.get("sub")
    email = (identity.get("email") or "").strip().lower()
    if not google_subject or not email or identity.get("email_verified") is not True:
        return {"message": "Google did not provide a verified email address"}, 401

    user = db.session.scalar(
        db.select(User).where(User.google_subject == google_subject)
    )
    is_new_user = False

    if user is None:
        user = db.session.scalar(db.select(User).where(User.email == email))
        if user is not None:
            if user.role != "customer":
                return {
                    "message": "Google sign-in is available only for customer accounts"
                }, 409
            return {
                "message": (
                    "An account with this email already exists. "
                    "Sign in with its password."
                )
            }, 409
        else:
            user = User(
                username=available_google_username(identity.get("name"), email),
                email=email,
                google_subject=google_subject,
                password_hash=generate_password_hash(secrets.token_urlsafe(32)),
                role="customer",
            )
            db.session.add(user)
            db.session.flush()
            db.session.add(
                Customer(
                    user_id=user.id,
                    address="",
                    city="",
                    state="",
                    pinCode="",
                )
            )
            is_new_user = True

    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return {"message": "This Google account is already connected"}, 409

    response_body = create_session_response(user, "Google sign-in successful")
    response_body["is_new_user"] = is_new_user
    return response_body, 201 if is_new_user else 200


@auth.get("/me")
@jwt_required()
def current_user():
    user_id = int(get_jwt_identity())
    user = db.session.get(User, user_id)

    if user is None:
        return {"message": "User no longer exists"}, 404

    return {"user": user_data(user)}, 200


@auth.post("/logout")
@jwt_required()
def logout():
    return {
        "message": "Logout successful",
        "action": "Remove the access token from the client",
    }, 200







