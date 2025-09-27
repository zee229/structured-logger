"""
Example demonstrating Sentry integration with structured logger.

This example shows how to:
1. Configure Sentry integration
2. Use structured logging with automatic Sentry error reporting
3. Manually capture exceptions and messages to Sentry
4. Set user context and custom tags
"""

import logging
import os

from structured_logger import (LoggerConfig, SentryConfig,
                               add_sentry_breadcrumb,
                               capture_exception_with_context,
                               capture_message_with_context, get_logger,
                               is_sentry_available, is_sentry_initialized,
                               set_sentry_context, set_sentry_user)


def main():
    """Demonstrate Sentry integration features."""

    # Check if Sentry is available
    if not is_sentry_available():
        print("Sentry SDK is not installed. Install with: pip install sentry-sdk")
        return

    # Configure Sentry integration
    sentry_config = SentryConfig(
        # DSN can be set here or via SENTRY_DSN environment variable
        dsn=os.getenv("SENTRY_DSN"),  # Set your Sentry DSN here or in environment
        min_level=logging.ERROR,  # Only send ERROR and above to Sentry
        send_default_pii=True,
        environment="development",  # or get from SENTRY_ENVIRONMENT
        release="1.0.0",  # or get from SENTRY_RELEASE
        default_tags={"service": "structured-logger-example", "component": "demo"},
        tag_fields=["user_id", "company_id", "request_id", "correlation_id"],
        extra_fields=["module", "funcName", "lineno"],
    )

    # Configure logger with Sentry integration
    logger_config = LoggerConfig(
        enable_sentry=True,
        sentry_config=sentry_config,
        custom_fields=["user_id", "company_id", "request_id"],
    )

    # Get logger instance
    logger = get_logger("sentry_example", config=logger_config)

    print("=== Sentry Integration Example ===")
    print(f"Sentry available: {is_sentry_available()}")
    print(f"Sentry initialized: {is_sentry_initialized()}")
    print()

    # Set user context for Sentry
    set_sentry_user(user_id="user123", email="user@example.com", username="testuser")

    # Set custom context
    set_sentry_context(
        "business",
        {
            "company_id": "company456",
            "plan": "premium",
            "feature_flags": ["new_ui", "beta_feature"],
        },
    )

    # Add breadcrumb for debugging context
    add_sentry_breadcrumb(
        message="Starting example demonstration",
        category="demo",
        level="info",
        data={"step": 1},
    )

    # Example 1: Regular logging (INFO level - won't go to Sentry)
    print("1. Regular INFO logging (won't go to Sentry):")
    logger.info(
        "This is a regular info message",
        extra={
            "user_id": "user123",
            "company_id": "company456",
            "request_id": "req789",
        },
    )

    # Example 2: Warning logging (won't go to Sentry by default)
    print("2. Warning logging (won't go to Sentry by default):")
    logger.warning(
        "This is a warning message",
        extra={"user_id": "user123", "action": "data_validation"},
    )

    # Example 3: Error logging (will go to Sentry)
    print("3. Error logging (will go to Sentry):")
    logger.error(
        "This is an error message that will be sent to Sentry",
        extra={
            "user_id": "user123",
            "company_id": "company456",
            "error_code": "VALIDATION_FAILED",
        },
    )

    # Example 4: Exception logging (will go to Sentry with stack trace)
    print("4. Exception logging (will go to Sentry with stack trace):")
    try:
        # Simulate an error
        result = 10 / 0
    except ZeroDivisionError as e:
        logger.exception(
            "Division by zero error occurred",
            extra={
                "user_id": "user123",
                "operation": "calculate_ratio",
                "numerator": 10,
                "denominator": 0,
            },
        )

    # Example 5: Manual exception capture with context
    print("5. Manual exception capture with rich context:")
    try:
        # Simulate another error
        data = {"key": "value"}
        missing_key = data["missing_key"]
    except KeyError as e:
        event_id = capture_exception_with_context(
            exception=e,
            user_id="user123",
            company_id="company456",
            request_id="req790",
            operation="data_access",
            data_keys=list(data.keys()),
            attempted_key="missing_key",
        )
        print(f"Exception captured to Sentry with event ID: {event_id}")

    # Example 6: Manual message capture
    print("6. Manual message capture:")
    event_id = capture_message_with_context(
        message="Critical business logic failure detected",
        level="error",
        user_id="user123",
        company_id="company456",
        business_process="payment_processing",
        transaction_id="txn_12345",
        amount=99.99,
    )
    print(f"Message captured to Sentry with event ID: {event_id}")

    # Example 7: Adding breadcrumbs for debugging context
    print("7. Adding breadcrumbs and then logging an error:")
    add_sentry_breadcrumb(
        message="User initiated payment process",
        category="business",
        level="info",
        data={"amount": 99.99, "currency": "USD"},
    )

    add_sentry_breadcrumb(
        message="Payment validation started",
        category="business",
        level="info",
        data={"validation_rules": ["amount_check", "fraud_check"]},
    )

    add_sentry_breadcrumb(
        message="Fraud check failed",
        category="business",
        level="warning",
        data={"reason": "suspicious_pattern", "risk_score": 85},
    )

    logger.error(
        "Payment processing failed due to fraud detection",
        extra={
            "user_id": "user123",
            "company_id": "company456",
            "transaction_id": "txn_12345",
            "fraud_score": 85,
            "payment_method": "credit_card",
        },
    )

    print("\n=== Example Complete ===")
    print("Check your Sentry dashboard to see the captured events!")
    print(
        "Note: Make sure to set SENTRY_DSN environment variable with your actual Sentry DSN"
    )


if __name__ == "__main__":
    main()
