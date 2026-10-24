import smtplib
from email.message import EmailMessage

from flask import current_app, render_template


def send_templated_email(recipient, subject, template_name, **context):
    """Render one email template and deliver it through the configured SMTP server."""
    if current_app.testing:
        return False

    username = current_app.config.get("MAIL_USERNAME")
    password = current_app.config.get("MAIL_PASSWORD")
    sender = current_app.config.get("MAIL_DEFAULT_SENDER") or username

    if not username or not password or not sender:
        current_app.logger.warning(
            "Email not sent to %s because SMTP credentials are not configured",
            recipient,
        )
        return False

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = sender
    message["To"] = recipient
    message.set_content(
        render_template(f"emails/{template_name}.txt", **context)
    )
    message.add_alternative(
        render_template(f"emails/{template_name}.html", **context),
        subtype="html",
    )

    with smtplib.SMTP(
        current_app.config["MAIL_SERVER"],
        current_app.config["MAIL_PORT"],
        timeout=20,
    ) as smtp:
        if current_app.config["MAIL_USE_TLS"]:
            smtp.starttls()
        smtp.login(username, password)
        smtp.send_message(message)
    return True
