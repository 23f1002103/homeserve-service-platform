from flask import current_app
from werkzeug.security import generate_password_hash

from .database import db
from .models import User


def ensure_admin_exists() -> bool:
    """Create the initial admin once, using credentials from configuration.

    Returns True when an admin was created and False when no change was needed.
    """
    existing_admin = db.session.scalar(
        db.select(User).where(User.role == "admin")
    )
    if existing_admin is not None:
        return False

    username = current_app.config.get("ADMIN_USERNAME")
    email = current_app.config.get("ADMIN_EMAIL")
    password = current_app.config.get("ADMIN_PASSWORD")
    if not all((username, email, password)):
        current_app.logger.warning(
            "Initial admin not created: set ADMIN_USERNAME, ADMIN_EMAIL, "
            "and ADMIN_PASSWORD in .env."
        )
        return False

    existing_user = db.session.scalar(
        db.select(User).where(
            (User.username == username) | (User.email == email.lower())
        )
    )

    if existing_user is not None:
        if existing_user.role != "admin":
            current_app.logger.warning(
                "Initial admin not created: its username or email is already in use."
            )
        return False

    admin = User(
        username=username,
        email=email.lower(),
        password_hash=generate_password_hash(password),
        role="admin",
    )
    db.session.add(admin)
    db.session.commit()
    current_app.logger.info("Initial admin account created.")
    return True

