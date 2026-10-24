from flask import Blueprint, request
from flask_jwt_extended import create_access_token, get_jwt_identity, jwt_required
from sqlalchemy.exc import IntegrityError
from werkzeug.security import check_password_hash, generate_password_hash

from ..database import db
from ..models import Customer, Professional, ServiceType, User

auth = Blueprint("auth", __name__)

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

    if not username or not email or not password or not role:
        return {
            "message": "Username, email, password, and role are required"
        }, 400

    if role not in {"customer", "professional"}:
        return {
            "message": "Role must be either customer or professional"
        }, 400

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
        phone_number=(data.get("phone_number") or "").strip() or None,
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
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "role": user.role,
        },
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

    access_token = create_access_token(
        identity=str(user.id),
        additional_claims={"role": user.role},
    )

    user_data = {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "role": user.role,
    }
    if user.role == "professional" and user.professional is not None:
        user_data["approval_status"] = user.professional.approval_status
        user_data["block_reason"] = user.professional.block_reason

    return {
        "message": "Login successful",
        "access_token": access_token,
        "user": user_data,
    }, 200


@auth.get("/me")
@jwt_required()
def current_user():
    user_id = int(get_jwt_identity())
    user = db.session.get(User, user_id)

    if user is None:
        return {"message": "User no longer exists"}, 404

    return {
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "role": user.role,
        }
    }, 200


@auth.post("/logout")
@jwt_required()
def logout():
    return {
        "message": "Logout successful",
        "action": "Remove the access token from the client",
    }, 200







