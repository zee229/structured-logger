"""
Example Flask integration with structured logging.
"""

import time
import uuid

from flask import Flask, g, jsonify, request

from structured_logger import get_logger, setup_root_logger

# Setup structured logging for the entire app
setup_root_logger()

app = Flask(__name__)
logger = get_logger(__name__)


@app.before_request
def before_request():
    """Add request ID and start time to each request."""
    g.request_id = str(uuid.uuid4())
    g.start_time = time.time()


@app.after_request
def after_request(response):
    """Log request completion."""
    duration = time.time() - getattr(g, "start_time", time.time())

    logger.info(
        "Request completed",
        extra={
            "request_id": getattr(g, "request_id", None),
            "method": request.method,
            "path": request.path,
            "status_code": response.status_code,
            "duration_ms": round(duration * 1000, 2),
            "user_agent": request.headers.get("User-Agent", "Unknown"),
        },
    )
    return response


@app.route("/")
def home():
    """Home endpoint."""
    logger.info(
        "Home page accessed", extra={"request_id": getattr(g, "request_id", None)}
    )
    return jsonify({"message": "Hello from structured logger!"})


@app.route("/user/<user_id>")
def user_profile(user_id):
    """User profile endpoint."""
    logger.info(
        "User profile accessed",
        extra={"request_id": getattr(g, "request_id", None), "user_id": user_id},
    )

    # Simulate some processing
    user_data = {"id": user_id, "name": f"User {user_id}", "status": "active"}

    logger.debug(
        "User data retrieved",
        extra={
            "request_id": getattr(g, "request_id", None),
            "user_id": user_id,
            "user_data": user_data,
        },
    )

    return jsonify(user_data)


@app.route("/error")
def error_endpoint():
    """Endpoint that demonstrates error logging."""
    try:
        # Simulate an error
        raise ValueError("Simulated error for demonstration")
    except Exception as e:
        logger.exception(
            "Error occurred in error endpoint",
            extra={
                "request_id": getattr(g, "request_id", None),
                "error_type": type(e).__name__,
            },
        )
        return jsonify({"error": "Internal server error"}), 500


if __name__ == "__main__":
    logger.info("Starting Flask application")
    app.run(debug=True, port=5000)
