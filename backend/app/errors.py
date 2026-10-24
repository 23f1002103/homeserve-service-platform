from flask import Flask, jsonify
from werkzeug.exceptions import HTTPException


def register_error_handlers(app: Flask) -> None:
    """Return JSON errors so API clients never receive an HTML error page."""

    @app.errorhandler(HTTPException)
    def handle_http_error(error: HTTPException):
        return (
            jsonify(
                {
                    "error": {
                        "code": error.code,
                        "message": error.description,
                    }
                }
            ),
            error.code,
        )

