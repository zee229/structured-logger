"""
Example of using structured-logger with Gunicorn server.

This example demonstrates how to configure structured logging for both
your Flask application and Gunicorn server logs.

To run this example with Gunicorn:
    gunicorn --workers 4 --bind 0.0.0.0:8000 --log-level info gunicorn_integration:app

Or with the logging configuration:
    gunicorn --workers 4 --bind 0.0.0.0:8000 --log-level info --logger-class structured_logger.GunicornLogger gunicorn_integration:app
"""

import time
import uuid

from flask import Flask, g, request

from structured_logger import LoggerConfig, get_logger, setup_gunicorn_logging

# Setup gunicorn logging with structured formatting
# This should be called before creating your Flask app
setup_gunicorn_logging(force_json=True)

app = Flask(__name__)

# Setup application logger
config = LoggerConfig(
    custom_fields=["request_id", "user_id"],
    include_extra_attrs=True,
)
logger = get_logger(__name__, config=config, force_json=True)


@app.before_request
def before_request():
    """Setup request context."""
    g.request_id = str(uuid.uuid4())
    g.start_time = time.time()

    logger.info(
        "Request started",
        extra={
            "request_id": g.request_id,
            "method": request.method,
            "path": request.path,
            "remote_addr": request.remote_addr,
        },
    )


@app.after_request
def after_request(response):
    """Log request completion."""
    duration = time.time() - g.start_time

    logger.info(
        "Request completed",
        extra={
            "request_id": g.request_id,
            "method": request.method,
            "path": request.path,
            "status_code": response.status_code,
            "duration_ms": round(duration * 1000, 2),
        },
    )

    return response


@app.route("/")
def hello():
    """Simple hello endpoint."""
    logger.info("Hello endpoint accessed", extra={"request_id": g.request_id})
    return {"message": "Hello, World!", "request_id": g.request_id}


@app.route("/user/<user_id>")
def get_user(user_id):
    """User endpoint."""
    logger.info(
        "User data requested",
        extra={
            "request_id": g.request_id,
            "user_id": user_id,
        },
    )

    return {
        "user_id": user_id,
        "name": f"User {user_id}",
        "request_id": g.request_id,
    }


@app.route("/error")
def trigger_error():
    """Endpoint that triggers an error."""
    logger.warning("Error endpoint accessed", extra={"request_id": g.request_id})
    raise ValueError("Test error for logging demonstration")


@app.errorhandler(Exception)
def handle_exception(e):
    """Handle and log exceptions."""
    logger.error(
        "Unhandled exception",
        extra={
            "request_id": getattr(g, "request_id", None),
            "exception_type": type(e).__name__,
            "exception_message": str(e),
        },
        exc_info=True,
    )
    return {"error": "Internal server error", "request_id": g.request_id}, 500


if __name__ == "__main__":
    # For development, you can run with Flask's built-in server
    logger.info("Flask application starting (development mode)")
    app.run(debug=True, port=8000)
