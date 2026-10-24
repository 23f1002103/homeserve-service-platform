from flask import Flask
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Base class that future database models will inherit from."""


db = SQLAlchemy(model_class=Base)
migrate = Migrate()


def init_database(app: Flask) -> None:
    """Attach SQLAlchemy and Flask-Migrate to a Flask application."""
    db.init_app(app)
    migrate.init_app(app, db)

