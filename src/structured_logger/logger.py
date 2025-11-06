"""
Structured JSON logger with flexible configuration for Python applications.
"""

import json
import logging
import os
import sys
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Union
from uuid import UUID

# Import advanced features
try:
    from .advanced import (
        AdvancedStructuredFormatter,
        AsyncLogger,
        AsyncLogHandler,
        CorrelationIDManager,
        LogMetrics,
        LogSchema,
        LogValidator,
        MetricsConfig,
        RateLimiter,
        RotationConfig,
        SamplingConfig,
        StructuredRotatingFileHandler,
        StructuredTimedRotatingFileHandler,
    )

    ADVANCED_FEATURES_AVAILABLE = True
except ImportError:
    ADVANCED_FEATURES_AVAILABLE = False

# Import Sentry integration
try:
    from .sentry_integration import SentryConfig, SentryLogHandler

    SENTRY_INTEGRATION_AVAILABLE = True
except ImportError:
    SENTRY_INTEGRATION_AVAILABLE = False


@dataclass
class LoggerConfig:
    """Configuration class for structured logger."""

    # Environment detection - Only Railway-specific variables to avoid conflicts
    production_env_vars: List[str] = field(
        default_factory=lambda: [
            "RAILWAY_ENVIRONMENT_NAME",  # Railway environment name
            "RAILWAY_SERVICE_NAME",      # Railway service name (always set)
            "RAILWAY_PROJECT_ID",        # Railway project ID (always set)
        ]
    )
    production_env_values: List[str] = field(
        default_factory=lambda: ["prod", "production", "staging", "dev"]
    )

    # Log level configuration
    log_level_env_var: str = "LOG_LEVEL"
    default_log_level: str = "INFO"

    # Custom fields to extract from log records
    custom_fields: List[str] = field(
        default_factory=lambda: [
            "user_id",
            "company_id",
            "request_id",
            "trace_id",
            "span_id",
        ]
    )

    # Time format
    time_format: Optional[str] = None

    # Development formatter
    dev_format: str = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"

    # Custom serializers for specific types
    custom_serializers: Dict[type, Callable] = field(default_factory=dict)

    # Whether to include extra attributes in logs
    include_extra_attrs: bool = True

    # Fields to exclude from extra attributes
    excluded_attrs: List[str] = field(
        default_factory=lambda: [
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
            "error",  # Exclude 'error' to prevent conflicts with logging internals
        ]
    )

    # Advanced features configuration
    enable_async: bool = False
    enable_validation: bool = False
    enable_sampling: bool = False
    enable_metrics: bool = False
    enable_file_rotation: bool = False
    enable_correlation_ids: bool = False

    # Advanced feature configs
    log_schema: Optional["LogSchema"] = None
    sampling_config: Optional["SamplingConfig"] = None
    metrics_config: Optional["MetricsConfig"] = None
    rotation_config: Optional["RotationConfig"] = None
    log_file_path: Optional[str] = None

    # Sentry integration
    enable_sentry: bool = False
    sentry_config: Optional["SentryConfig"] = None

    # Uvicorn logger override (enabled by default for convenience)
    override_uvicorn_loggers: bool = True
    uvicorn_loggers: List[str] = field(
        default_factory=lambda: [
            "uvicorn",
            "uvicorn.access",
            "uvicorn.error",
            "uvicorn.asgi",
        ]
    )

    # Gunicorn logger override (enabled by default for convenience)
    override_gunicorn_loggers: bool = True
    gunicorn_loggers: List[str] = field(
        default_factory=lambda: [
            "gunicorn",
            "gunicorn.access",
            "gunicorn.error",
        ]
    )

    # Third-party library logger override (enabled by default for convenience)
    override_library_loggers: bool = True
    library_loggers: List[str] = field(
        default_factory=lambda: [
            "httpx",
            "httpcore",
            "starlette",
            "fastapi",
            "asyncio",
            "aiohttp",
            "urllib3",
            "requests",
        ]
    )
    enable_library_logging: bool = True  # Set to False to suppress library logs
    library_log_level: str = "WARNING"  # Higher level to reduce noise
    library_log_level_env_var: str = "LIBRARY_LOG_LEVEL"  # Env var for runtime config

    # SQLAlchemy logger override (enabled by default, set to False to suppress)
    enable_sqlalchemy_logging: bool = True
    sqlalchemy_loggers: List[str] = field(
        default_factory=lambda: [
            "sqlalchemy",
            "sqlalchemy.engine",
            "sqlalchemy.pool",
            "sqlalchemy.orm",
        ]
    )
    sqlalchemy_log_level: str = "WARNING"  # Higher level to reduce noise

    # LangChain logger override (enabled by default, set to False to suppress)
    enable_langchain_logging: bool = True
    langchain_loggers: List[str] = field(
        default_factory=lambda: [
            "langchain",
            "langchain_core",  # Core LangChain functionality
            "langchain.chains",
            "langchain.agents",
            "langchain.tools",
            "langchain.callbacks",
            "langchain.retrievers",
            "langchain.embeddings",
            "langchain.llms",
            "langchain.chat_models",
            "langsmith",  # LangSmith tracing logs
        ]
    )
    langchain_log_level: str = "WARNING"  # Higher level to reduce noise

    # Stream configuration
    # If True, uses stdout for all logs (Railway-compatible, default)
    # If False, uses stderr for ERROR/CRITICAL logs, stdout for others
    use_stdout_for_all: bool = True


class LevelBasedStreamHandler(logging.StreamHandler):
    """
    StreamHandler that routes logs to different streams based on level.

    ERROR and CRITICAL logs go to stderr, all others go to stdout.
    This follows Unix conventions but may cause issues with platforms
    like Railway that treat stderr as errors.
    """

    def __init__(self):
        """Initialize with stdout as default stream."""
        super().__init__(sys.stdout)

    def emit(self, record):
        """Emit a record, routing to stderr for ERROR/CRITICAL levels."""
        # Save original stream
        original_stream = self.stream

        try:
            # Route ERROR and CRITICAL to stderr
            if record.levelno >= logging.ERROR:
                self.stream = sys.stderr
            else:
                self.stream = sys.stdout

            # Emit the record
            super().emit(record)
        finally:
            # Restore original stream
            self.stream = original_stream


class StructuredLogFormatter(logging.Formatter):
    """Custom formatter that outputs structured JSON logs with flexible configuration."""

    def __init__(self, config: Optional[LoggerConfig] = None):
        """Initialize the formatter with optional configuration."""
        super().__init__()
        self.config = config or LoggerConfig()

        # Add custom fields to excluded attributes
        self.config.excluded_attrs.extend(self.config.custom_fields)

    def _serialize_value(self, value: Any) -> Any:
        """Convert non-serializable values to JSON-safe types."""
        # Check for custom serializers first
        for type_class, serializer in self.config.custom_serializers.items():
            if isinstance(value, type_class):
                return serializer(value)

        # Default serializers
        if isinstance(value, UUID):
            return str(value)
        elif hasattr(value, "__dict__"):
            # For complex objects, try to convert to dict
            try:
                return {
                    k: self._serialize_value(v)
                    for k, v in value.__dict__.items()
                    if not k.startswith("_")
                }
            except (AttributeError, TypeError, ValueError, RecursionError):
                # Handle cases where object serialization fails
                return str(value)

        return value

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        # Base log record structure
        log_record = {
            "time": self.formatTime(record, self.config.time_format),
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.name,
        }

        # Add exception info if present
        if record.exc_info:
            log_record["exception"] = self.formatException(record.exc_info)

        # Add custom fields if present
        for field_name in self.config.custom_fields:
            if hasattr(record, field_name):
                log_record[field_name] = self._serialize_value(
                    getattr(record, field_name)
                )

        # Handle 'error' field explicitly to prevent conflicts with logging internals
        if hasattr(record, "error"):
            error_value = getattr(record, "error")
            if error_value is not None:
                log_record["error_details"] = self._serialize_value(error_value)

        # Handle any extra attributes
        if self.config.include_extra_attrs:
            extra_attrs = {}
            for key, value in record.__dict__.items():
                if key not in self.config.excluded_attrs:
                    extra_attrs[key] = self._serialize_value(value)

            if extra_attrs:
                log_record["extra"] = extra_attrs

        return json.dumps(log_record, default=str)


def _is_production_environment(config: LoggerConfig) -> bool:
    """Check if we're running in a production environment.

    For Railway-specific variables (RAILWAY_SERVICE_NAME, RAILWAY_PROJECT_ID),
    just checking if they exist is enough. For RAILWAY_ENVIRONMENT_NAME,
    check if the value matches production_env_values.
    """
    # Railway-specific variables that indicate Railway environment just by existing
    railway_presence_vars = ["RAILWAY_SERVICE_NAME", "RAILWAY_PROJECT_ID"]

    for env_var in config.production_env_vars:
        env_value = os.getenv(env_var, "")

        # For Railway presence vars, just check if they exist (have any value)
        if env_var in railway_presence_vars and env_value:
            return True

        # For other vars (like RAILWAY_ENVIRONMENT_NAME), check the value
        if env_value.lower() in [v.lower() for v in config.production_env_values]:
            return True

    return False


def _override_uvicorn_loggers(
    config: LoggerConfig,
    formatter: logging.Formatter,
    force_json: bool = False,
    force_dev: bool = False,
) -> None:
    """Override uvicorn loggers to use structured formatting."""
    if not config.override_uvicorn_loggers:
        return

    # Determine if we should use JSON formatting
    use_json = force_json or (not force_dev and _is_production_environment(config))

    # Create appropriate formatter for uvicorn loggers
    if use_json:
        uvicorn_formatter = StructuredLogFormatter(config)
    else:
        uvicorn_formatter = logging.Formatter(config.dev_format)

    # Override each uvicorn logger
    for logger_name in config.uvicorn_loggers:
        uvicorn_logger = logging.getLogger(logger_name)

        # Clear existing handlers
        for handler in uvicorn_logger.handlers[:]:
            uvicorn_logger.removeHandler(handler)

        # Set log level from environment or config default
        log_level = os.getenv(
            config.log_level_env_var, config.default_log_level
        ).upper()
        uvicorn_logger.setLevel(getattr(logging, log_level, logging.INFO))

        # Setup advanced features if available and enabled
        if ADVANCED_FEATURES_AVAILABLE:
            advanced_formatter = _setup_advanced_formatter(uvicorn_formatter, config)
            handler = _setup_advanced_handler(config, advanced_formatter)
        else:
            # Choose handler based on configuration
            if config.use_stdout_for_all:
                # Use stdout for all logs (Railway-compatible)
                handler = logging.StreamHandler(sys.stdout)
            else:
                # Use level-based routing (Unix convention)
                handler = LevelBasedStreamHandler()
            handler.setFormatter(uvicorn_formatter)

        uvicorn_logger.addHandler(handler)

        # Add Sentry handler if enabled
        if SENTRY_INTEGRATION_AVAILABLE and config.enable_sentry:
            sentry_config = config.sentry_config or SentryConfig()
            sentry_handler = SentryLogHandler(sentry_config)

            # Add correlation ID filter to Sentry handler if enabled
            if ADVANCED_FEATURES_AVAILABLE and config.enable_correlation_ids:

                def add_correlation_id(record):
                    correlation_id = CorrelationIDManager.get_correlation_id()
                    if correlation_id:
                        record.correlation_id = correlation_id
                    return True

                sentry_handler.addFilter(add_correlation_id)

            uvicorn_logger.addHandler(sentry_handler)

        # Prevent duplicate logs from propagating to root logger
        uvicorn_logger.propagate = False


def _override_gunicorn_loggers(
    config: LoggerConfig,
    formatter: logging.Formatter,
    force_json: bool = False,
    force_dev: bool = False,
) -> None:
    """Override gunicorn loggers to use structured formatting."""
    if not config.override_gunicorn_loggers:
        return

    # Determine if we should use JSON formatting
    use_json = force_json or (not force_dev and _is_production_environment(config))

    # Create appropriate formatter for gunicorn loggers
    if use_json:
        gunicorn_formatter = StructuredLogFormatter(config)
    else:
        gunicorn_formatter = logging.Formatter(config.dev_format)

    # Override each gunicorn logger
    for logger_name in config.gunicorn_loggers:
        gunicorn_logger = logging.getLogger(logger_name)

        # Clear existing handlers
        for handler in gunicorn_logger.handlers[:]:
            gunicorn_logger.removeHandler(handler)

        # Set log level from environment or config default
        log_level = os.getenv(
            config.log_level_env_var, config.default_log_level
        ).upper()
        gunicorn_logger.setLevel(getattr(logging, log_level, logging.INFO))

        # Setup advanced features if available and enabled
        if ADVANCED_FEATURES_AVAILABLE:
            advanced_formatter = _setup_advanced_formatter(gunicorn_formatter, config)
            handler = _setup_advanced_handler(config, advanced_formatter)
        else:
            # Choose handler based on configuration
            if config.use_stdout_for_all:
                # Use stdout for all logs (Railway-compatible)
                handler = logging.StreamHandler(sys.stdout)
            else:
                # Use level-based routing (Unix convention)
                handler = LevelBasedStreamHandler()
            handler.setFormatter(gunicorn_formatter)

        gunicorn_logger.addHandler(handler)

        # Add Sentry handler if enabled
        if SENTRY_INTEGRATION_AVAILABLE and config.enable_sentry:
            sentry_config = config.sentry_config or SentryConfig()
            sentry_handler = SentryLogHandler(sentry_config)

            # Add correlation ID filter to Sentry handler if enabled
            if ADVANCED_FEATURES_AVAILABLE and config.enable_correlation_ids:

                def add_correlation_id(record):
                    correlation_id = CorrelationIDManager.get_correlation_id()
                    if correlation_id:
                        record.correlation_id = correlation_id
                    return True

                sentry_handler.addFilter(add_correlation_id)

            gunicorn_logger.addHandler(sentry_handler)

        # Prevent duplicate logs from propagating to root logger
        gunicorn_logger.propagate = False


def _override_library_loggers(
    config: LoggerConfig,
    formatter: logging.Formatter,
    force_json: bool = False,
    force_dev: bool = False,
) -> None:
    """Override third-party library loggers to use structured formatting."""
    if not config.override_library_loggers:
        return

    if not config.enable_library_logging:
        # If library logging is disabled, silence the loggers completely
        for logger_name in config.library_loggers:
            library_logger = logging.getLogger(logger_name)
            library_logger.setLevel(logging.CRITICAL + 1)  # Effectively silence
            library_logger.propagate = False
        return

    # Determine if we should use JSON formatting
    use_json = force_json or (not force_dev and _is_production_environment(config))

    # Create appropriate formatter for library loggers
    if use_json:
        library_formatter = StructuredLogFormatter(config)
    else:
        library_formatter = logging.Formatter(config.dev_format)

    # Override each library logger
    for logger_name in config.library_loggers:
        library_logger = logging.getLogger(logger_name)

        # Clear existing handlers
        for handler in library_logger.handlers[:]:
            library_logger.removeHandler(handler)

        # Set log level from environment variable or config
        # (allows independent control from app log level)
        log_level = os.getenv(
            config.library_log_level_env_var, config.library_log_level
        ).upper()
        library_logger.setLevel(getattr(logging, log_level, logging.WARNING))

        # Setup advanced features if available and enabled
        if ADVANCED_FEATURES_AVAILABLE:
            advanced_formatter = _setup_advanced_formatter(library_formatter, config)
            handler = _setup_advanced_handler(config, advanced_formatter)
        else:
            # Choose handler based on configuration
            if config.use_stdout_for_all:
                # Use stdout for all logs (Railway-compatible)
                handler = logging.StreamHandler(sys.stdout)
            else:
                # Use level-based routing (Unix convention)
                handler = LevelBasedStreamHandler()
            handler.setFormatter(library_formatter)

        library_logger.addHandler(handler)

        # Add Sentry handler if enabled
        if SENTRY_INTEGRATION_AVAILABLE and config.enable_sentry:
            sentry_config = config.sentry_config or SentryConfig()
            sentry_handler = SentryLogHandler(sentry_config)

            # Add correlation ID filter to Sentry handler if enabled
            if ADVANCED_FEATURES_AVAILABLE and config.enable_correlation_ids:

                def add_correlation_id(record):
                    correlation_id = CorrelationIDManager.get_correlation_id()
                    if correlation_id:
                        record.correlation_id = correlation_id
                    return True

                sentry_handler.addFilter(add_correlation_id)

            library_logger.addHandler(sentry_handler)

        # Prevent duplicate logs from propagating to root logger
        library_logger.propagate = False


def _override_sqlalchemy_loggers(
    config: LoggerConfig,
    formatter: logging.Formatter,
    force_json: bool = False,
    force_dev: bool = False,
) -> None:
    """Override SQLAlchemy loggers to use structured formatting."""
    if not config.enable_sqlalchemy_logging:
        # If SQLAlchemy logging is disabled, silence the loggers completely
        for logger_name in config.sqlalchemy_loggers:
            sqlalchemy_logger = logging.getLogger(logger_name)
            sqlalchemy_logger.setLevel(logging.CRITICAL + 1)  # Effectively silence
            sqlalchemy_logger.propagate = False
        return

    # Determine if we should use JSON formatting
    use_json = force_json or (not force_dev and _is_production_environment(config))

    # Create appropriate formatter for SQLAlchemy loggers
    if use_json:
        sqlalchemy_formatter = StructuredLogFormatter(config)
    else:
        sqlalchemy_formatter = logging.Formatter(config.dev_format)

    # Override each SQLAlchemy logger
    for logger_name in config.sqlalchemy_loggers:
        sqlalchemy_logger = logging.getLogger(logger_name)

        # Clear existing handlers
        for handler in sqlalchemy_logger.handlers[:]:
            sqlalchemy_logger.removeHandler(handler)

        # Set log level from config (default WARNING to reduce noise)
        sqlalchemy_logger.setLevel(
            getattr(logging, config.sqlalchemy_log_level, logging.WARNING)
        )

        # Setup advanced features if available and enabled
        if ADVANCED_FEATURES_AVAILABLE:
            advanced_formatter = _setup_advanced_formatter(sqlalchemy_formatter, config)
            handler = _setup_advanced_handler(config, advanced_formatter)
        else:
            # Choose handler based on configuration
            if config.use_stdout_for_all:
                # Use stdout for all logs (Railway-compatible)
                handler = logging.StreamHandler(sys.stdout)
            else:
                # Use level-based routing (Unix convention)
                handler = LevelBasedStreamHandler()
            handler.setFormatter(sqlalchemy_formatter)

        sqlalchemy_logger.addHandler(handler)

        # Add Sentry handler if enabled
        if SENTRY_INTEGRATION_AVAILABLE and config.enable_sentry:
            sentry_config = config.sentry_config or SentryConfig()
            sentry_handler = SentryLogHandler(sentry_config)

            # Add correlation ID filter to Sentry handler if enabled
            if ADVANCED_FEATURES_AVAILABLE and config.enable_correlation_ids:

                def add_correlation_id(record):
                    correlation_id = CorrelationIDManager.get_correlation_id()
                    if correlation_id:
                        record.correlation_id = correlation_id
                    return True

                sentry_handler.addFilter(add_correlation_id)

            sqlalchemy_logger.addHandler(sentry_handler)

        # Prevent duplicate logs from propagating to root logger
        sqlalchemy_logger.propagate = False


def _override_langchain_loggers(
    config: LoggerConfig,
    formatter: logging.Formatter,
    force_json: bool = False,
    force_dev: bool = False,
) -> None:
    """Override LangChain loggers to use structured formatting."""
    # Determine if we're in a production/Railway environment
    is_production = force_json or (not force_dev and _is_production_environment(config))

    if not config.enable_langchain_logging:
        # Only silence LangChain loggers in production/Railway
        # In dev, let them log naturally
        if is_production:
            for logger_name in config.langchain_loggers:
                langchain_logger = logging.getLogger(logger_name)
                langchain_logger.setLevel(logging.CRITICAL + 1)  # Effectively silence
                langchain_logger.propagate = False
        return

    # Determine if we should use JSON formatting
    use_json = force_json or (not force_dev and _is_production_environment(config))

    # Create appropriate formatter for LangChain loggers
    if use_json:
        langchain_formatter = StructuredLogFormatter(config)
    else:
        langchain_formatter = logging.Formatter(config.dev_format)

    # Override each LangChain logger
    for logger_name in config.langchain_loggers:
        langchain_logger = logging.getLogger(logger_name)

        # Clear existing handlers
        for handler in langchain_logger.handlers[:]:
            langchain_logger.removeHandler(handler)

        # Set log level from config (default WARNING to reduce noise)
        langchain_logger.setLevel(
            getattr(logging, config.langchain_log_level, logging.WARNING)
        )

        # Setup advanced features if available and enabled
        if ADVANCED_FEATURES_AVAILABLE:
            advanced_formatter = _setup_advanced_formatter(langchain_formatter, config)
            handler = _setup_advanced_handler(config, advanced_formatter)
        else:
            # Choose handler based on configuration
            if config.use_stdout_for_all:
                # Use stdout for all logs (Railway-compatible)
                handler = logging.StreamHandler(sys.stdout)
            else:
                # Use level-based routing (Unix convention)
                handler = LevelBasedStreamHandler()
            handler.setFormatter(langchain_formatter)

        langchain_logger.addHandler(handler)

        # Add Sentry handler if enabled
        if SENTRY_INTEGRATION_AVAILABLE and config.enable_sentry:
            sentry_config = config.sentry_config or SentryConfig()
            sentry_handler = SentryLogHandler(sentry_config)

            # Add correlation ID filter to Sentry handler if enabled
            if ADVANCED_FEATURES_AVAILABLE and config.enable_correlation_ids:

                def add_correlation_id(record):
                    correlation_id = CorrelationIDManager.get_correlation_id()
                    if correlation_id:
                        record.correlation_id = correlation_id
                    return True

                sentry_handler.addFilter(add_correlation_id)

            langchain_logger.addHandler(sentry_handler)

        # Prevent duplicate logs from propagating to root logger
        langchain_logger.propagate = False


def get_logger(
    name: Optional[str] = None,
    config: Optional[LoggerConfig] = None,
    force_json: bool = False,
    force_dev: bool = False,
) -> Union[logging.Logger, "AsyncLogger"]:
    """
    Get a structured logger instance with flexible configuration.

    Args:
        name: Logger name, defaults to calling module name
        config: Logger configuration, uses default if not provided
        force_json: Force JSON formatting regardless of environment
        force_dev: Force development formatting regardless of environment

    Returns:
        Configured logger instance (AsyncLogger if async is enabled)
    """
    logger_name = name or __name__
    logger = logging.getLogger(logger_name)

    # Only configure if not already configured
    if not logger.handlers:
        config = config or LoggerConfig()

        # Set log level from environment or config default
        log_level = os.getenv(
            config.log_level_env_var, config.default_log_level
        ).upper()
        logger.setLevel(getattr(logging, log_level, logging.INFO))

        # Determine formatter based on environment and override flags
        use_json = force_json or (not force_dev and _is_production_environment(config))

        if use_json:
            formatter = StructuredLogFormatter(config)
        else:
            formatter = logging.Formatter(config.dev_format)

        # Setup advanced features if available and enabled
        if ADVANCED_FEATURES_AVAILABLE:
            formatter = _setup_advanced_formatter(formatter, config)
            handler = _setup_advanced_handler(config, formatter)
        else:
            # Choose handler based on configuration
            if config.use_stdout_for_all:
                # Use stdout for all logs (Railway-compatible)
                handler = logging.StreamHandler(sys.stdout)
            else:
                # Use level-based routing (Unix convention)
                handler = LevelBasedStreamHandler()
            handler.setFormatter(formatter)

        logger.addHandler(handler)

        # Add Sentry handler if enabled
        if SENTRY_INTEGRATION_AVAILABLE and config.enable_sentry:
            sentry_config = config.sentry_config or SentryConfig()
            sentry_handler = SentryLogHandler(sentry_config)

            # Add correlation ID filter to Sentry handler if enabled
            if ADVANCED_FEATURES_AVAILABLE and config.enable_correlation_ids:

                def add_correlation_id(record):
                    correlation_id = CorrelationIDManager.get_correlation_id()
                    if correlation_id:
                        record.correlation_id = correlation_id
                    return True

                sentry_handler.addFilter(add_correlation_id)

            logger.addHandler(sentry_handler)

        # Prevent duplicate logs
        logger.propagate = False

        # Override uvicorn loggers if enabled
        _override_uvicorn_loggers(config, formatter, force_json, force_dev)

        # Override gunicorn loggers if enabled
        _override_gunicorn_loggers(config, formatter, force_json, force_dev)

        # Override library loggers if enabled
        _override_library_loggers(config, formatter, force_json, force_dev)

        # Override SQLAlchemy loggers (or silence them if disabled)
        _override_sqlalchemy_loggers(config, formatter, force_json, force_dev)

        # Override LangChain loggers (or silence them if disabled)
        _override_langchain_loggers(config, formatter, force_json, force_dev)

    # Return async logger if enabled
    if ADVANCED_FEATURES_AVAILABLE and config and config.enable_async:
        return AsyncLogger(logger)

    return logger


def setup_root_logger(
    config: Optional[LoggerConfig] = None,
    force_json: bool = False,
    force_dev: bool = False,
) -> None:
    """
    Setup root logger configuration for the entire application.

    Args:
        config: Logger configuration, uses default if not provided
        force_json: Force JSON formatting regardless of environment
        force_dev: Force development formatting regardless of environment
    """
    config = config or LoggerConfig()
    root_logger = logging.getLogger()

    # Clear existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Set log level
    log_level = os.getenv(config.log_level_env_var, config.default_log_level).upper()
    root_logger.setLevel(getattr(logging, log_level, logging.INFO))

    # Create console handler
    if config.use_stdout_for_all:
        # Use stdout for all logs (Railway-compatible)
        handler = logging.StreamHandler(sys.stdout)
    else:
        # Use level-based routing (Unix convention)
        handler = LevelBasedStreamHandler()

    # Determine formatter
    use_json = force_json or (not force_dev and _is_production_environment(config))

    if use_json:
        formatter = StructuredLogFormatter(config)
    else:
        formatter = logging.Formatter(config.dev_format)

    handler.setFormatter(formatter)
    root_logger.addHandler(handler)

    # Add Sentry handler if enabled
    if SENTRY_INTEGRATION_AVAILABLE and config.enable_sentry:
        sentry_config = config.sentry_config or SentryConfig()
        sentry_handler = SentryLogHandler(sentry_config)
        root_logger.addHandler(sentry_handler)

    # Override uvicorn loggers if enabled
    _override_uvicorn_loggers(config, formatter, force_json, force_dev)

    # Override gunicorn loggers if enabled
    _override_gunicorn_loggers(config, formatter, force_json, force_dev)

    # Override library loggers if enabled
    _override_library_loggers(config, formatter, force_json, force_dev)

    # Override SQLAlchemy loggers (or silence them if disabled)
    _override_sqlalchemy_loggers(config, formatter, force_json, force_dev)

    # Override LangChain loggers (or silence them if disabled)
    _override_langchain_loggers(config, formatter, force_json, force_dev)


# Backward compatibility aliases
def get_railway_logger(
    name: Optional[str] = None,
) -> Union[logging.Logger, "AsyncLogger"]:
    """Alias for get_logger for Railway compatibility."""
    return get_logger(name)


def get_structured_logger(
    name: Optional[str] = None, **kwargs
) -> Union[logging.Logger, "AsyncLogger"]:
    """Alias for get_logger with explicit naming."""
    return get_logger(name, **kwargs)


def setup_uvicorn_logging(
    config: Optional[LoggerConfig] = None,
    force_json: bool = False,
    force_dev: bool = False,
) -> None:
    """
    Setup uvicorn logging with structured formatting.

    This is a convenience function that specifically configures uvicorn loggers
    to use structured formatting. It's useful when you want to apply structured
    logging to uvicorn without affecting other loggers.

    Args:
        config: Logger configuration, uses default with uvicorn override enabled if not provided
        force_json: Force JSON formatting regardless of environment
        force_dev: Force development formatting regardless of environment
    """
    if config is None:
        config = LoggerConfig(override_uvicorn_loggers=True)
    else:
        # Ensure uvicorn override is enabled
        config.override_uvicorn_loggers = True

    # Create a dummy formatter to pass to the override function
    use_json = force_json or (not force_dev and _is_production_environment(config))
    if use_json:
        formatter = StructuredLogFormatter(config)
    else:
        formatter = logging.Formatter(config.dev_format)

    _override_uvicorn_loggers(config, formatter, force_json, force_dev)


def setup_gunicorn_logging(
    config: Optional[LoggerConfig] = None,
    force_json: bool = False,
    force_dev: bool = False,
) -> None:
    """
    Setup gunicorn logging with structured formatting.

    This is a convenience function that specifically configures gunicorn loggers
    to use structured formatting. It's useful when you want to apply structured
    logging to gunicorn without affecting other loggers.

    Args:
        config: Logger configuration, uses default with gunicorn override enabled if not provided
        force_json: Force JSON formatting regardless of environment
        force_dev: Force development formatting regardless of environment
    """
    if config is None:
        config = LoggerConfig(override_gunicorn_loggers=True)
    else:
        # Ensure gunicorn override is enabled
        config.override_gunicorn_loggers = True

    # Create a dummy formatter to pass to the override function
    use_json = force_json or (not force_dev and _is_production_environment(config))
    if use_json:
        formatter = StructuredLogFormatter(config)
    else:
        formatter = logging.Formatter(config.dev_format)

    _override_gunicorn_loggers(config, formatter, force_json, force_dev)


def setup_library_logging(
    config: Optional[LoggerConfig] = None,
    force_json: bool = False,
    force_dev: bool = False,
) -> None:
    """
    Setup third-party library logging with structured formatting.

    This is a convenience function that specifically configures common third-party
    library loggers (httpx, starlette, etc.) to use structured formatting.
    It's useful when you want to apply structured logging to all library logs.

    Note: SQLAlchemy and LangChain logging are controlled separately via
    enable_sqlalchemy_logging and enable_langchain_logging (enabled by default).
    Set to False to suppress if needed.

    Args:
        config: Logger configuration, uses default with library override enabled if not provided
        force_json: Force JSON formatting regardless of environment
        force_dev: Force development formatting regardless of environment
    """
    if config is None:
        config = LoggerConfig(override_library_loggers=True)
    else:
        # Ensure library override is enabled
        config.override_library_loggers = True

    # Create a dummy formatter to pass to the override function
    use_json = force_json or (not force_dev and _is_production_environment(config))
    if use_json:
        formatter = StructuredLogFormatter(config)
    else:
        formatter = logging.Formatter(config.dev_format)

    _override_library_loggers(config, formatter, force_json, force_dev)
    _override_sqlalchemy_loggers(config, formatter, force_json, force_dev)
    _override_langchain_loggers(config, formatter, force_json, force_dev)


def _setup_advanced_formatter(base_formatter, config: LoggerConfig):
    """Setup advanced formatter with validation and metrics."""
    if not ADVANCED_FEATURES_AVAILABLE:
        return base_formatter

    validator = None
    if config.enable_validation and config.log_schema:
        validator = LogValidator(config.log_schema)

    metrics = None
    if config.enable_metrics and config.metrics_config:
        metrics = LogMetrics(config.metrics_config)

    if validator or metrics:
        return AdvancedStructuredFormatter(base_formatter, validator, metrics)

    return base_formatter


def _setup_advanced_handler(config: LoggerConfig, formatter):
    """Setup advanced handler with async, rotation, and rate limiting."""
    if not ADVANCED_FEATURES_AVAILABLE:
        # Choose handler based on configuration
        if config.use_stdout_for_all:
            handler = logging.StreamHandler(sys.stdout)
        else:
            handler = LevelBasedStreamHandler()
        handler.setFormatter(formatter)
        return handler

    # Determine base handler type
    if config.enable_file_rotation and config.log_file_path:
        if config.rotation_config.rotation_type == "time":
            base_handler = StructuredTimedRotatingFileHandler(
                config.log_file_path, config.rotation_config, formatter
            )
        else:
            base_handler = StructuredRotatingFileHandler(
                config.log_file_path, config.rotation_config, formatter
            )
    else:
        # Choose handler based on configuration
        if config.use_stdout_for_all:
            base_handler = logging.StreamHandler(sys.stdout)
        else:
            base_handler = LevelBasedStreamHandler()
        base_handler.setFormatter(formatter)

    # Add rate limiting if enabled
    if config.enable_sampling and config.sampling_config:
        rate_limiter = RateLimiter(config.sampling_config)
        base_handler.addFilter(lambda record: rate_limiter.should_log())

    # Add correlation ID filter if enabled
    if config.enable_correlation_ids:

        def add_correlation_id(record):
            correlation_id = CorrelationIDManager.get_correlation_id()
            if correlation_id:
                record.correlation_id = correlation_id
            return True

        base_handler.addFilter(add_correlation_id)

    # Wrap with async handler if enabled
    if config.enable_async:
        return AsyncLogHandler(base_handler)

    return base_handler
