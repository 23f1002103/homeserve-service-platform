import os
from datetime import timedelta

from dotenv import load_dotenv


load_dotenv()


class Config:
    """Configuration shared by the HomeServe Flask application."""

    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        "postgresql+psycopg://postgres:postgres@localhost:5432/homeserve",
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)

    ADMIN_USERNAME = os.getenv("ADMIN_USERNAME")
    ADMIN_EMAIL = os.getenv("ADMIN_EMAIL")
    ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")

    # HomeServe keeps this percentage when a completed service is settled.
    PLATFORM_COMMISSION_PERCENT = os.getenv("PLATFORM_COMMISSION_PERCENT", "15")

    # Celery uses Redis as its job queue. Beat starts the reminder check once
    # per minute, while a Celery worker performs the actual work.
    CELERY = {
        "broker_url": os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0"),
        "result_backend": os.getenv(
            "CELERY_RESULT_BACKEND",
            "redis://localhost:6379/1",
        ),
        "task_ignore_result": True,
        "timezone": os.getenv("CELERY_TIMEZONE", "Asia/Kolkata"),
        "beat_schedule": {
            "check-upcoming-professional-jobs": {
                "task": "app.tasks.send_upcoming_job_reminders",
                "schedule": 60.0,
            }
        },
    }

    # SMTP values are read by the Celery email tasks. A Gmail App Password can
    # be used for MAIL_PASSWORD during local development.
    MAIL_SERVER = os.getenv("MAIL_SERVER", "smtp.gmail.com")
    MAIL_PORT = int(os.getenv("MAIL_PORT", "587"))
    MAIL_USE_TLS = os.getenv("MAIL_USE_TLS", "true").lower() == "true"
    MAIL_USERNAME = os.getenv("MAIL_USERNAME")
    MAIL_PASSWORD = os.getenv("MAIL_PASSWORD")
    MAIL_DEFAULT_SENDER = os.getenv("MAIL_DEFAULT_SENDER")



