"""
Example showing Railway.app compatibility.
This demonstrates that the library maintains full backward compatibility
with the original Railway logger implementation.
"""

import os
from structured_logger import get_railway_logger, setup_root_logger


def main():
    # Set Railway environment for demonstration
    os.environ["RAILWAY_ENVIRONMENT"] = "production"

    # Use the Railway-compatible function
    logger = get_railway_logger(__name__)

    logger.info("Application deployed to Railway")

    # Log with Railway-style context
    logger.info(
        "Processing user request",
        extra={
            "user_id": "user_12345",
            "company_id": "company_67890",
            "request_id": "req_abcdef",
        },
    )

    # Error logging with context
    try:
        # Simulate some error
        result = int("not_a_number")
    except ValueError:
        logger.exception(
            "Failed to process user data",
            extra={"user_id": "user_12345", "operation": "data_conversion"},
        )

    # Setup root logger Railway-style
    setup_root_logger()

    import logging

    root_logger = logging.getLogger("railway_app")
    root_logger.info("Root logger configured for Railway deployment")

    # Demonstrate that it works with different log levels
    logger.debug("Debug message (may not appear depending on LOG_LEVEL)")
    logger.info("Info message")
    logger.warning("Warning message")
    logger.error("Error message")
    logger.critical("Critical message")


if __name__ == "__main__":
    main()
