"""
Basic usage examples for structured-logger.
"""
from structured_logger import get_logger

def main():
    # Get a logger instance
    logger = get_logger(__name__)
    
    # Basic logging
    logger.info("Application started")
    logger.warning("This is a warning message")
    logger.error("An error occurred")
    
    # Logging with extra context
    logger.info(
        "User action performed",
        extra={
            "user_id": "12345",
            "action": "login",
            "ip_address": "192.168.1.1"
        }
    )
    
    # Logging with complex objects
    user_data = {
        "id": "67890",
        "name": "John Doe",
        "email": "john@example.com"
    }
    
    logger.info("User data processed", extra={"user": user_data})
    
    # Exception logging
    try:
        result = 10 / 0
    except ZeroDivisionError:
        logger.exception(
            "Division by zero error",
            extra={"operation": "calculate_ratio"}
        )

if __name__ == "__main__":
    main()