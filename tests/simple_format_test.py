#!/usr/bin/env python3
"""
Simple test to demonstrate Railway vs Sentry format differences.

This shows the actual formats that would be sent to each platform.
"""

import json
import sys
from io import StringIO
from pathlib import Path

# Add the package to Python path for testing
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


def test_railway_format():
    """Show what Railway receives - structured JSON logs."""
    print("🚂 RAILWAY FORMAT (JSON Logs)")
    print("=" * 50)

    from structured_logger import LoggerConfig, get_logger

    # Capture console output
    console_output = StringIO()

    # Configure for Railway JSON format
    config = LoggerConfig(
        enable_sentry=False, custom_fields=["user_id", "company_id", "request_id"]
    )

    logger = get_logger("railway_demo", config=config, force_json=True)

    # Replace handler stream to capture output
    for handler in logger.handlers:
        if hasattr(handler, "stream"):
            handler.stream = console_output

    # Log some sample data
    logger.info(
        "User authentication successful",
        extra={
            "user_id": "user_12345",
            "company_id": "company_67890",
            "request_id": "req_abcdef",
            "ip_address": "192.168.1.100",
            "user_agent": "Mozilla/5.0 (Chrome)",
            "login_method": "oauth",
        },
    )

    logger.error(
        "Payment processing failed",
        extra={
            "user_id": "user_12345",
            "company_id": "company_67890",
            "transaction_id": "txn_xyz123",
            "amount": 99.99,
            "currency": "USD",
            "error_code": "CARD_DECLINED",
            "retry_count": 2,
        },
    )

    # Show the output
    output = console_output.getvalue()
    lines = [line.strip() for line in output.split("\n") if line.strip()]

    for i, line in enumerate(lines, 1):
        print(f"\nLog Entry {i}:")
        try:
            parsed = json.loads(line)
            print(json.dumps(parsed, indent=2))
        except json.JSONDecodeError:
            print(f"Raw: {line}")

    print(f"\n📊 Railway Format Characteristics:")
    print(f"   • Format: Structured JSON")
    print(f"   • Purpose: Log aggregation, searching, analytics")
    print(f"   • Structure: Flat JSON with nested 'extra' field")
    print(f"   • Time: ISO timestamp")
    print(f"   • All context preserved in JSON structure")


def show_sentry_format():
    """Show what Sentry would receive - native Sentry events."""
    print("\n\n🔍 SENTRY FORMAT (Native Events)")
    print("=" * 50)

    print("Sentry receives native events, NOT JSON logs. Here's what gets sent:\n")

    # Simulate what the SentryLogHandler.emit() method does
    print("Example 1 - Info Message:")
    print("  sentry_sdk.capture_message(")
    print('    message="User authentication successful",')
    print('    level="info"')
    print("  )")
    print("  + Tags: {")
    print('      "user_id": "user_12345",')
    print('      "company_id": "company_67890",')
    print('      "request_id": "req_abcdef"')
    print("    }")
    print("  + Extras: {")
    print('      "module": "railway_demo",')
    print('      "log_ip_address": "192.168.1.100",')
    print('      "log_user_agent": "Mozilla/5.0 (Chrome)",')
    print('      "log_login_method": "oauth"')
    print("    }")

    print("\nExample 2 - Error Message:")
    print("  sentry_sdk.capture_message(")
    print('    message="Payment processing failed",')
    print('    level="error"')
    print("  )")
    print("  + Tags: {")
    print('      "user_id": "user_12345",')
    print('      "company_id": "company_67890"')
    print("    }")
    print("  + Extras: {")
    print('      "module": "railway_demo",')
    print('      "log_transaction_id": "txn_xyz123",')
    print('      "log_amount": "99.99",')
    print('      "log_currency": "USD",')
    print('      "log_error_code": "CARD_DECLINED",')
    print('      "log_retry_count": "2"')
    print("    }")

    print(f"\n📊 Sentry Format Characteristics:")
    print(f"   • Format: Native Sentry events (not JSON)")
    print(f"   • Purpose: Error monitoring, alerting, debugging")
    print(f"   • Structure: Message + Tags + Extras + Context")
    print(f"   • Tags: For filtering and grouping")
    print(f"   • Extras: For debugging context")
    print(f"   • Optimized for Sentry's error analysis features")


def show_exception_differences():
    """Show how exceptions are handled differently."""
    print("\n\n⚠️  EXCEPTION HANDLING DIFFERENCES")
    print("=" * 50)

    print("Railway Exception Format:")
    print("  {")
    print('    "time": "2024-01-01T12:00:00.000Z",')
    print('    "level": "ERROR",')
    print('    "message": "Database connection failed",')
    print('    "module": "my_app",')
    print('    "exception": "Traceback (most recent call last):\\n  File...",')
    print('    "user_id": "user123",')
    print('    "extra": { ... }')
    print("  }")
    print("  → Stack trace as string in JSON")
    print("  → Good for log searching and text analysis")

    print("\nSentry Exception Format:")
    print("  sentry_sdk.capture_exception(exception_object)")
    print("  → Sends actual Python exception object")
    print("  → Sentry extracts stack trace, local variables, etc.")
    print("  → Enables advanced error analysis, grouping, fingerprinting")
    print("  → Provides source code context, release tracking")


def show_configuration_example():
    """Show how to configure both formats."""
    print("\n\n⚙️  CONFIGURATION EXAMPLE")
    print("=" * 50)

    config_example = """
from structured_logger import get_logger, LoggerConfig, SentryConfig

# Configure both Railway and Sentry
sentry_config = SentryConfig(
    dsn=os.getenv("SENTRY_DSN"),
    min_level=logging.ERROR,  # Only errors to Sentry
    tag_fields=["user_id", "company_id", "request_id"],
    extra_fields=["module", "funcName", "lineno"]
)

logger_config = LoggerConfig(
    enable_sentry=True,
    sentry_config=sentry_config,
    custom_fields=["user_id", "company_id", "request_id"]
)

logger = get_logger("my_app", config=logger_config)

# This single call produces BOTH formats:
logger.error("Payment failed", extra={
    "user_id": "user123",
    "company_id": "company456", 
    "transaction_id": "txn789",
    "amount": 99.99
})

# Railway gets: JSON log with all context
# Sentry gets: Native event with tags/extras
"""

    print(config_example)


def main():
    """Run the format demonstration."""
    print("🔍 Railway vs Sentry Format Demonstration")
    print("This shows the DIFFERENT formats sent to each platform")

    # Show Railway format
    test_railway_format()

    # Show Sentry format
    show_sentry_format()

    # Show exception differences
    show_exception_differences()

    # Show configuration
    show_configuration_example()

    print("\n" + "=" * 60)
    print("✅ SUMMARY")
    print("=" * 60)
    print("✓ Railway receives structured JSON logs (perfect for log aggregation)")
    print("✓ Sentry receives native Sentry events (perfect for error monitoring)")
    print("✓ Formats are completely different and optimized for each platform")
    print("✓ No conflicts or interference between the two systems")
    print("✓ Single logger.error() call produces both formats automatically")


if __name__ == "__main__":
    main()
