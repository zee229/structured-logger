"""
Example showing custom configuration options.
"""

from datetime import datetime
from uuid import UUID, uuid4

from structured_logger import LoggerConfig, get_logger


def serialize_datetime(dt):
    """Custom datetime serializer."""
    return dt.isoformat()


def main():
    # Create custom configuration
    config = LoggerConfig(
        # Custom fields to extract from log records
        custom_fields=["user_id", "request_id", "trace_id", "session_id"],
        # Custom environment detection
        production_env_vars=["APP_ENV", "DEPLOYMENT"],
        production_env_values=["prod", "production"],
        # Custom serializers
        custom_serializers={
            datetime: serialize_datetime,
            UUID: str,  # Convert UUIDs to strings
        },
        # Custom development format
        dev_format="[%(levelname)s] %(name)s | %(message)s",
        # Custom log level environment variable
        log_level_env_var="APP_LOG_LEVEL",
        default_log_level="DEBUG",
    )

    # Get logger with custom config
    logger = get_logger(__name__, config=config)

    # Test logging with various data types
    logger.info("Application initialized with custom config")

    # Log with datetime
    logger.info(
        "Processing started",
        extra={
            "start_time": datetime.now(),
            "user_id": str(uuid4()),
            "request_id": "req_123456",
        },
    )

    # Log with UUID
    user_uuid = uuid4()
    logger.info(
        "User session created", extra={"session_id": user_uuid, "user_id": "user_123"}
    )

    # Log with complex nested data
    complex_data = {
        "metadata": {"version": "1.0.0", "timestamp": datetime.now(), "uuid": uuid4()},
        "stats": {"requests": 100, "errors": 2},
    }

    logger.info("Complex data logged", extra={"data": complex_data})


if __name__ == "__main__":
    main()
