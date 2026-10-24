from collections.abc import Mapping
from pathlib import Path
from typing import Any

from flask import Flask

from .admin import admin
from .auth import auth
from .celery_app import init_celery
from .config import Config
from .customer import customer
from .database import init_database
from .errors import register_error_handlers
from .extensions import jwt
from .professional import professional
from .routes import api


def register_frontend(app: Flask) -> None:
    """Serve the built Vue application when it is included in production."""
    static_folder = Path(app.static_folder or "")
    if not (static_folder / "index.html").is_file():
        return

    @app.get("/")
    @app.get("/<path:path>")
    def frontend(path: str = ""):
        # Unknown API URLs must remain JSON 404 responses, not Vue pages.
        if path == "api" or path.startswith("api/"):
            return {"message": "Resource not found"}, 404

        requested_file = static_folder / path
        if path and requested_file.is_file():
            return app.send_static_file(path)
        return app.send_static_file("index.html")


def create_app(test_config: Mapping[str, Any] | None = None) -> Flask:
    """Create the Flask application and connect its components."""
    app = Flask(__name__)
    app.config.from_object(Config)
    app.config.from_mapping(
        JSON_SORT_KEYS=False,
    )

    if test_config is not None:
        app.config.from_mapping(test_config)

    init_database(app)
    jwt.init_app(app)
    init_celery(app)

    # Import models so SQLAlchemy and Flask-Migrate can discover their tables.
    from . import models  # noqa: F401
    from . import tasks  # noqa: F401

    app.register_blueprint(api, url_prefix="/api")
    app.register_blueprint(auth, url_prefix="/api/auth")
    app.register_blueprint(admin, url_prefix="/api/admin")
    app.register_blueprint(professional, url_prefix="/api/professional")
    app.register_blueprint(customer, url_prefix="/api/customer")
    register_error_handlers(app)
    register_frontend(app)
    return app

