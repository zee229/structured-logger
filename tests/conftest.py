"""
Pytest configuration and fixtures for structured-logger tests.
"""

import os
import pytest
from pathlib import Path
from dotenv import load_dotenv


def pytest_configure(config):
    """Configure pytest with environment variables."""
    # Load test environment variables
    test_env_path = Path(__file__).parent.parent / ".env.test"
    env_path = Path(__file__).parent.parent / ".env"

    # Load .env.test first (higher priority)
    if test_env_path.exists():
        load_dotenv(test_env_path, override=True)

    # Load .env as fallback
    if env_path.exists():
        load_dotenv(env_path, override=False)


@pytest.fixture(scope="session")
def test_env_vars():
    """Provide test environment variables."""
    return {
        "sentry_dsn": os.getenv("SENTRY_DSN"),
        "log_level": os.getenv("LOG_LEVEL", "INFO"),
        "test_user_id": os.getenv("TEST_USER_ID", "test_user_123"),
        "test_company_id": os.getenv("TEST_COMPANY_ID", "test_company_456"),
        "test_request_id": os.getenv("TEST_REQUEST_ID", "test_request_789"),
        "environment": os.getenv("ENVIRONMENT", "test"),
        "testing": os.getenv("TESTING", "true").lower() == "true",
    }


@pytest.fixture
def mock_sentry_dsn():
    """Provide a mock Sentry DSN for testing."""
    return "https://mock-dsn@sentry.io/123456"


@pytest.fixture
def real_sentry_available(test_env_vars):
    """Check if real Sentry DSN is available for integration tests."""
    dsn = test_env_vars["sentry_dsn"]
    return dsn and dsn.startswith("https://") and "sentry.io" in dsn


@pytest.fixture
def logger_test_config(test_env_vars):
    """Provide a standard logger configuration for tests."""
    from structured_logger import LoggerConfig

    return LoggerConfig(
        enable_sentry=False,  # Disabled by default for unit tests
        custom_fields=["user_id", "company_id", "request_id"],
    )


@pytest.fixture
def sentry_test_config(mock_sentry_dsn):
    """Provide a Sentry configuration for tests."""
    import logging
    from structured_logger import SentryConfig

    return SentryConfig(
        dsn=mock_sentry_dsn,
        min_level=logging.INFO,
        environment="test",
        tag_fields=["user_id", "company_id", "request_id"],
        extra_fields=["module", "funcName"],
    )


@pytest.fixture
def sample_log_data(test_env_vars):
    """Provide sample log data for tests."""
    return {
        "user_id": test_env_vars["test_user_id"],
        "company_id": test_env_vars["test_company_id"],
        "request_id": test_env_vars["test_request_id"],
        "ip_address": "192.168.1.100",
        "user_agent": "Mozilla/5.0 (Test)",
        "transaction_id": "txn_test_123",
        "amount": 99.99,
        "currency": "USD",
    }


# Pytest markers for different test categories
pytestmark = [
    pytest.mark.filterwarnings("ignore::DeprecationWarning"),
    pytest.mark.filterwarnings("ignore::PendingDeprecationWarning"),
]
