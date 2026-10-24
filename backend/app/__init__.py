from collections.abc import Mapping
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
    return app

