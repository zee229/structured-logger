"""
Quick start example for Gunicorn integration.

Run with:
    gunicorn --workers 2 --bind 0.0.0.0:8000 gunicorn_quick_start:app
"""

from flask import Flask

from structured_logger import get_logger, setup_gunicorn_logging

# Setup Gunicorn logging - call this BEFORE creating your app
setup_gunicorn_logging(force_json=True)

app = Flask(__name__)
logger = get_logger(__name__, force_json=True)


@app.route("/")
def hello():
    logger.info("Hello endpoint called")
    return {"message": "Hello, World!"}


@app.route("/health")
def health():
    logger.info("Health check")
    return {"status": "healthy"}


if __name__ == "__main__":
    logger.info("Starting Flask app")
    app.run(debug=True, port=8000)
