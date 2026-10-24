from functools import wraps

from flask_jwt_extended import get_jwt, jwt_required


def roles_required(*allowed_roles: str):
    """Allow access only to JWTs containing one of the permitted roles."""

    def decorator(view_function):
        @wraps(view_function)
        @jwt_required()
        def wrapped_view(*args, **kwargs):
            current_role = get_jwt().get("role")

            if current_role not in allowed_roles:
                return {"message": "You do not have permission to access this resource"}, 403

            return view_function(*args, **kwargs)

        return wrapped_view

    return decorator

