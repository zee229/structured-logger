"""
Sentry integration for structured logger.

This module provides Sentry integration that works alongside Railway-compatible
JSON logging without interfering with the structured log output.
"""

import logging
import os
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from uuid import UUID

try:
    import sentry_sdk
    from sentry_sdk.integrations.logging import LoggingIntegration

    SENTRY_AVAILABLE = True
except ImportError:
    SENTRY_AVAILABLE = False


@dataclass
class SentryConfig:
    """Configuration for Sentry integration."""

    # Sentry DSN - can be set via environment variable or directly
    dsn: Optional[str] = None
    dsn_env_var: str = "SENTRY_DSN"

    # Minimum log level to send to Sentry
    min_level: int = logging.ERROR

    # Whether to send default PII (personally identifiable information)
    send_default_pii: bool = True

    # Sample rate for performance monitoring (0.0 to 1.0)
    traces_sample_rate: float = 0.1

    # Environment name for Sentry
    environment: Optional[str] = None
    environment_env_var: str = "SENTRY_ENVIRONMENT"

    # Release version
    release: Optional[str] = None
    release_env_var: str = "SENTRY_RELEASE"

    # Whether to enable automatic logging integration (not recommended with structured logging)
    enable_logging_integration: bool = False

    # Additional Sentry integrations to enable
    additional_integrations: List[Any] = field(default_factory=list)

    # Custom tags to add to all Sentry events
    default_tags: Dict[str, str] = field(default_factory=dict)

    # Fields from log records to include as Sentry tags
    tag_fields: List[str] = field(
        default_factory=lambda: [
            "user_id",
            "company_id",
            "request_id",
            "correlation_id",
            "trace_id",
        ]
    )

    # Fields from log records to include as Sentry extra context
    extra_fields: List[str] = field(
        default_factory=lambda: ["module", "funcName", "lineno", "pathname"]
    )


class SentryLogHandler(logging.Handler):
    """
    Custom Sentry handler that sends logs to Sentry without interfering
    with Railway formatting or other log handlers.
    """

    def __init__(self, config: SentryConfig):
        super().__init__(level=config.min_level)
        self.config = config
        self._initialized = False

        if SENTRY_AVAILABLE:
            self._initialize_sentry()

    def _initialize_sentry(self):
        """Initialize Sentry SDK if not already initialized."""
        if self._initialized:
            return

        # Get DSN from config or environment
        dsn = self.config.dsn or os.getenv(self.config.dsn_env_var)
        if not dsn:
            return

        # Get environment and release
        environment = self.config.environment or os.getenv(
            self.config.environment_env_var
        )
        release = self.config.release or os.getenv(self.config.release_env_var)

        # Setup integrations
        integrations = list(self.config.additional_integrations)

        # Only add logging integration if explicitly enabled
        if self.config.enable_logging_integration:
            integrations.append(
                LoggingIntegration(
                    level=logging.INFO, event_level=self.config.min_level
                )
            )

        # Initialize Sentry
        sentry_sdk.init(
            dsn=dsn,
            environment=environment,
            release=release,
            send_default_pii=self.config.send_default_pii,
            traces_sample_rate=self.config.traces_sample_rate,
            integrations=integrations,
            # Disable automatic log capture to avoid conflicts
            enable_logs=False if not self.config.enable_logging_integration else True,
        )

        # Set default tags
        for key, value in self.config.default_tags.items():
            sentry_sdk.set_tag(key, value)

        self._initialized = True

    def _serialize_value(self, value: Any) -> str:
        """Convert values to string for Sentry tags/context."""
        if isinstance(value, UUID):
            return str(value)
        elif hasattr(value, "__dict__"):
            return str(value)
        return str(value)

    def emit(self, record: logging.LogRecord):
        """Send log record to Sentry."""
        if not SENTRY_AVAILABLE or not self._initialized:
            return

        try:
            # Only send logs at or above the configured level
            if record.levelno < self.config.min_level:
                return

            # Create a clean message for Sentry
            message = record.getMessage()

            # Prepare tags and extra context
            tags = {}
            extra_context = {}

            # Add configured tag fields
            for field in self.config.tag_fields:
                if hasattr(record, field):
                    value = getattr(record, field)
                    if value is not None:
                        tags[field] = self._serialize_value(value)

            # Add configured extra fields
            for field in self.config.extra_fields:
                if hasattr(record, field):
                    value = getattr(record, field)
                    if value is not None:
                        extra_context[field] = self._serialize_value(value)

            # Add any extra attributes from the log record
            for key, value in record.__dict__.items():
                if (
                    key
                    not in [
                        "name",
                        "msg",
                        "args",
                        "levelname",
                        "levelno",
                        "pathname",
                        "filename",
                        "module",
                        "lineno",
                        "funcName",
                        "created",
                        "msecs",
                        "relativeCreated",
                        "thread",
                        "threadName",
                        "processName",
                        "process",
                        "getMessage",
                        "exc_info",
                        "exc_text",
                        "stack_info",
                    ]
                    and key not in self.config.tag_fields
                    and key not in self.config.extra_fields
                ):
                    extra_context[f"log_{key}"] = self._serialize_value(value)

            # Send to Sentry with context
            with sentry_sdk.push_scope() as scope:
                # Set tags
                for key, value in tags.items():
                    scope.set_tag(key, value)

                # Set extra context
                for key, value in extra_context.items():
                    scope.set_extra(key, value)

                # Set log level context
                scope.set_level(record.levelname.lower())

                # Send exception or message
                if record.exc_info:
                    sentry_sdk.capture_exception(record.exc_info[1])
                else:
                    sentry_sdk.capture_message(message, level=record.levelname.lower())

        except Exception:
            # Don't let Sentry errors break the application
            # Could optionally log this error to a fallback logger
            pass


def initialize_sentry(config: Optional[SentryConfig] = None) -> bool:
    """
    Initialize Sentry SDK independently of logging handlers.

    Args:
        config: Sentry configuration. If None, uses default config.

    Returns:
        True if Sentry was successfully initialized, False otherwise.
    """
    if not SENTRY_AVAILABLE:
        return False

    config = config or SentryConfig()

    # Get DSN from config or environment
    dsn = config.dsn or os.getenv(config.dsn_env_var)
    if not dsn:
        return False

    # Get environment and release
    environment = config.environment or os.getenv(config.environment_env_var)
    release = config.release or os.getenv(config.release_env_var)

    # Setup integrations
    integrations = list(config.additional_integrations)

    # Only add logging integration if explicitly enabled
    if config.enable_logging_integration:
        integrations.append(
            LoggingIntegration(level=logging.INFO, event_level=config.min_level)
        )

    try:
        # Initialize Sentry
        sentry_sdk.init(
            dsn=dsn,
            environment=environment,
            release=release,
            send_default_pii=config.send_default_pii,
            traces_sample_rate=config.traces_sample_rate,
            integrations=integrations,
            # Disable automatic log capture to avoid conflicts
            enable_logs=False if not config.enable_logging_integration else True,
        )

        # Set default tags
        for key, value in config.default_tags.items():
            sentry_sdk.set_tag(key, value)

        return True

    except Exception:
        return False


def capture_exception_with_context(
    exception: Exception,
    user_id: Optional[str] = None,
    company_id: Optional[str] = None,
    request_id: Optional[str] = None,
    correlation_id: Optional[str] = None,
    **extra_context,
) -> Optional[str]:
    """
    Capture an exception to Sentry with additional context.

    Args:
        exception: The exception to capture
        user_id: Optional user ID for context
        company_id: Optional company ID for context
        request_id: Optional request ID for context
        correlation_id: Optional correlation ID for context
        **extra_context: Additional context to include

    Returns:
        Sentry event ID if successful, None otherwise
    """
    if not SENTRY_AVAILABLE:
        return None

    try:
        with sentry_sdk.push_scope() as scope:
            # Set standard tags
            if user_id:
                scope.set_tag("user_id", str(user_id))
            if company_id:
                scope.set_tag("company_id", str(company_id))
            if request_id:
                scope.set_tag("request_id", str(request_id))
            if correlation_id:
                scope.set_tag("correlation_id", str(correlation_id))

            # Set extra context
            for key, value in extra_context.items():
                scope.set_extra(key, str(value))

            return sentry_sdk.capture_exception(exception)

    except Exception:
        return None


def capture_message_with_context(
    message: str,
    level: str = "info",
    user_id: Optional[str] = None,
    company_id: Optional[str] = None,
    request_id: Optional[str] = None,
    correlation_id: Optional[str] = None,
    **extra_context,
) -> Optional[str]:
    """
    Capture a message to Sentry with additional context.

    Args:
        message: The message to capture
        level: Log level (debug, info, warning, error, fatal)
        user_id: Optional user ID for context
        company_id: Optional company ID for context
        request_id: Optional request ID for context
        correlation_id: Optional correlation ID for context
        **extra_context: Additional context to include

    Returns:
        Sentry event ID if successful, None otherwise
    """
    if not SENTRY_AVAILABLE:
        return None

    try:
        with sentry_sdk.push_scope() as scope:
            # Set standard tags
            if user_id:
                scope.set_tag("user_id", str(user_id))
            if company_id:
                scope.set_tag("company_id", str(company_id))
            if request_id:
                scope.set_tag("request_id", str(request_id))
            if correlation_id:
                scope.set_tag("correlation_id", str(correlation_id))

            # Set extra context
            for key, value in extra_context.items():
                scope.set_extra(key, str(value))

            return sentry_sdk.capture_message(message, level=level)

    except Exception:
        return None


def add_sentry_breadcrumb(
    message: str,
    category: str = "custom",
    level: str = "info",
    data: Optional[Dict[str, Any]] = None,
):
    """
    Add a breadcrumb to Sentry for debugging context.

    Args:
        message: Breadcrumb message
        category: Breadcrumb category
        level: Breadcrumb level
        data: Additional data for the breadcrumb
    """
    if not SENTRY_AVAILABLE:
        return

    try:
        sentry_sdk.add_breadcrumb(
            message=message, category=category, level=level, data=data or {}
        )
    except Exception:
        pass


def set_sentry_user(
    user_id: Optional[str] = None,
    email: Optional[str] = None,
    username: Optional[str] = None,
    **extra_data,
):
    """
    Set user context in Sentry.

    Args:
        user_id: User ID
        email: User email
        username: Username
        **extra_data: Additional user data
    """
    if not SENTRY_AVAILABLE:
        return

    try:
        user_data = {}
        if user_id:
            user_data["id"] = user_id
        if email:
            user_data["email"] = email
        if username:
            user_data["username"] = username

        user_data.update(extra_data)

        sentry_sdk.set_user(user_data)
    except Exception:
        pass


def set_sentry_context(name: str, context: Dict[str, Any]):
    """
    Set custom context in Sentry.

    Args:
        name: Context name
        context: Context data
    """
    if not SENTRY_AVAILABLE:
        return

    try:
        sentry_sdk.set_context(name, context)
    except Exception:
        pass


def is_sentry_available() -> bool:
    """Check if Sentry SDK is available."""
    return SENTRY_AVAILABLE


def is_sentry_initialized() -> bool:
    """Check if Sentry has been initialized."""
    if not SENTRY_AVAILABLE:
        return False

    try:
        return sentry_sdk.Hub.current.client is not None
    except Exception:
        return False
