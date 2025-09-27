"""
Advanced logging features for structured logger.

This module provides async logging, validation, rate limiting, metrics,
file rotation, and correlation ID support.
"""

import asyncio
import json
import logging
import threading
import time
import uuid
from collections import defaultdict, deque
from contextlib import contextmanager
from dataclasses import dataclass, field
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
from pathlib import Path
from queue import Empty, Queue
from threading import Lock, local
from typing import Any, Callable, Dict, List, Optional, Set, Union
from uuid import UUID

# Thread-local storage for correlation IDs
_correlation_context = local()


@dataclass
class LogSchema:
    """Schema definition for log validation."""

    required_fields: Set[str] = field(default_factory=set)
    optional_fields: Set[str] = field(default_factory=set)
    field_types: Dict[str, type] = field(default_factory=dict)
    field_validators: Dict[str, Callable[[Any], bool]] = field(default_factory=dict)
    max_message_length: Optional[int] = None
    allowed_levels: Set[str] = field(
        default_factory=lambda: {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
    )


@dataclass
class SamplingConfig:
    """Configuration for log sampling."""

    sample_rate: float = 1.0  # 0.0 to 1.0
    burst_limit: int = 100  # Allow burst of logs before sampling
    time_window: int = 60  # Time window in seconds for rate limiting
    max_logs_per_window: int = 1000


@dataclass
class MetricsConfig:
    """Configuration for metrics collection."""

    enabled: bool = True
    track_performance: bool = True
    track_counts: bool = True
    track_errors: bool = True
    metrics_interval: int = 60  # Seconds between metrics reports


@dataclass
class RotationConfig:
    """Configuration for file rotation."""

    max_bytes: int = 10 * 1024 * 1024  # 10MB
    backup_count: int = 5
    rotation_type: str = "size"  # "size" or "time"
    when: str = "midnight"  # For time-based rotation
    interval: int = 1
    encoding: str = "utf-8"


class LogValidator:
    """Validates log records against a schema."""

    def __init__(self, schema: LogSchema):
        self.schema = schema

    def validate(self, record: logging.LogRecord) -> bool:
        """Validate a log record against the schema."""
        try:
            # Check log level
            if record.levelname not in self.schema.allowed_levels:
                return False

            # Check message length
            if self.schema.max_message_length:
                if len(record.getMessage()) > self.schema.max_message_length:
                    return False

            # Check required fields
            for field in self.schema.required_fields:
                if not hasattr(record, field):
                    return False

            # Check field types and run validators
            for field, expected_type in self.schema.field_types.items():
                if hasattr(record, field):
                    value = getattr(record, field)
                    if not isinstance(value, expected_type):
                        return False

                    # Run custom validator if exists
                    if field in self.schema.field_validators:
                        if not self.schema.field_validators[field](value):
                            return False

            return True

        except Exception:
            return False


class RateLimiter:
    """Rate limiting for log messages."""

    def __init__(self, config: SamplingConfig):
        self.config = config
        self.timestamps = deque()
        self.burst_count = 0
        self.lock = Lock()
        self._last_cleanup = time.time()

    def should_log(self) -> bool:
        """Determine if a log should be allowed based on rate limiting."""
        with self.lock:
            now = time.time()

            # Clean up old timestamps periodically
            if now - self._last_cleanup > self.config.time_window:
                self._cleanup_old_timestamps(now)
                self._last_cleanup = now

            # Allow burst
            if self.burst_count < self.config.burst_limit:
                self.burst_count += 1
                self.timestamps.append(now)
                return True

            # Check rate limit
            window_start = now - self.config.time_window
            recent_logs = sum(1 for ts in self.timestamps if ts > window_start)

            if recent_logs < self.config.max_logs_per_window:
                # Apply sampling
                import random

                if random.random() <= self.config.sample_rate:
                    self.timestamps.append(now)
                    return True

            return False

    def _cleanup_old_timestamps(self, now: float):
        """Remove timestamps outside the time window."""
        window_start = now - self.config.time_window
        while self.timestamps and self.timestamps[0] <= window_start:
            self.timestamps.popleft()

        # Reset burst count if enough time has passed
        if not self.timestamps:
            self.burst_count = 0


class LogMetrics:
    """Collects and tracks logging metrics."""

    def __init__(self, config: MetricsConfig):
        self.config = config
        self.counts = defaultdict(int)
        self.errors = defaultdict(int)
        self.performance = defaultdict(list)
        self.lock = Lock()
        self.start_time = time.time()

        if config.enabled:
            self._start_metrics_thread()

    def record_log(self, record: logging.LogRecord, processing_time: float = 0):
        """Record metrics for a log entry."""
        if not self.config.enabled:
            return

        with self.lock:
            if self.config.track_counts:
                self.counts[record.levelname] += 1
                self.counts["total"] += 1

            if self.config.track_performance and processing_time > 0:
                self.performance[record.levelname].append(processing_time)

            if self.config.track_errors and record.levelname in ["ERROR", "CRITICAL"]:
                error_key = f"{record.module}:{record.funcName}"
                self.errors[error_key] += 1

    def get_metrics(self) -> Dict[str, Any]:
        """Get current metrics snapshot."""
        with self.lock:
            uptime = time.time() - self.start_time

            # Calculate performance statistics
            perf_stats = {}
            for level, times in self.performance.items():
                if times:
                    perf_stats[level] = {
                        "avg": sum(times) / len(times),
                        "min": min(times),
                        "max": max(times),
                        "count": len(times),
                    }

            return {
                "uptime": uptime,
                "counts": dict(self.counts),
                "errors": dict(self.errors),
                "performance": perf_stats,
                "timestamp": time.time(),
            }

    def _start_metrics_thread(self):
        """Start background thread for periodic metrics reporting."""

        def report_metrics():
            while True:
                time.sleep(self.config.metrics_interval)
                metrics = self.get_metrics()
                # Log metrics using standard logger to avoid recursion
                logging.getLogger("structured_logger.metrics").info(
                    "Logging metrics", extra={"metrics": metrics}
                )

        thread = threading.Thread(target=report_metrics, daemon=True)
        thread.start()


class CorrelationIDManager:
    """Manages correlation IDs for request tracing."""

    @staticmethod
    def generate_id() -> str:
        """Generate a new correlation ID."""
        return str(uuid.uuid4())

    @staticmethod
    def set_correlation_id(correlation_id: str):
        """Set correlation ID for current thread/context."""
        _correlation_context.correlation_id = correlation_id

    @staticmethod
    def get_correlation_id() -> Optional[str]:
        """Get correlation ID for current thread/context."""
        return getattr(_correlation_context, "correlation_id", None)

    @staticmethod
    def clear_correlation_id():
        """Clear correlation ID for current thread/context."""
        if hasattr(_correlation_context, "correlation_id"):
            delattr(_correlation_context, "correlation_id")

    @staticmethod
    @contextmanager
    def correlation_context(correlation_id: Optional[str] = None):
        """Context manager for correlation ID."""
        if correlation_id is None:
            correlation_id = CorrelationIDManager.generate_id()

        old_id = CorrelationIDManager.get_correlation_id()
        CorrelationIDManager.set_correlation_id(correlation_id)
        try:
            yield correlation_id
        finally:
            if old_id is not None:
                CorrelationIDManager.set_correlation_id(old_id)
            else:
                CorrelationIDManager.clear_correlation_id()


class AsyncLogHandler(logging.Handler):
    """Async log handler for high-performance logging."""

    def __init__(self, target_handler: logging.Handler, queue_size: int = 10000):
        super().__init__()
        self.target_handler = target_handler
        self.queue = Queue(maxsize=queue_size)
        self.worker_thread = None
        self.stop_event = threading.Event()
        self._start_worker()

    def emit(self, record: logging.LogRecord):
        """Emit a log record asynchronously."""
        try:
            self.queue.put_nowait(record)
        except:
            # Queue is full, drop the log or handle overflow
            pass

    def _start_worker(self):
        """Start the background worker thread."""

        def worker():
            while not self.stop_event.is_set():
                try:
                    record = self.queue.get(timeout=0.1)
                    self.target_handler.emit(record)
                    self.queue.task_done()
                except Empty:
                    continue
                except Exception:
                    # Log errors without causing recursion
                    pass

        self.worker_thread = threading.Thread(target=worker, daemon=True)
        self.worker_thread.start()

    def close(self):
        """Close the handler and stop the worker thread."""
        self.stop_event.set()
        if self.worker_thread:
            self.worker_thread.join(timeout=1.0)
        self.target_handler.close()
        super().close()


class StructuredRotatingFileHandler(RotatingFileHandler):
    """Rotating file handler with structured logging support."""

    def __init__(self, filename: str, config: RotationConfig, formatter=None):
        super().__init__(
            filename=filename,
            maxBytes=config.max_bytes,
            backupCount=config.backup_count,
            encoding=config.encoding,
        )
        if formatter:
            self.setFormatter(formatter)


class StructuredTimedRotatingFileHandler(TimedRotatingFileHandler):
    """Timed rotating file handler with structured logging support."""

    def __init__(self, filename: str, config: RotationConfig, formatter=None):
        super().__init__(
            filename=filename,
            when=config.when,
            interval=config.interval,
            backupCount=config.backup_count,
            encoding=config.encoding,
        )
        if formatter:
            self.setFormatter(formatter)


class AdvancedStructuredFormatter(logging.Formatter):
    """Enhanced structured formatter with validation and correlation support."""

    def __init__(
        self,
        base_formatter,
        validator: Optional[LogValidator] = None,
        metrics: Optional[LogMetrics] = None,
    ):
        super().__init__()
        self.base_formatter = base_formatter
        self.validator = validator
        self.metrics = metrics

    def format(self, record: logging.LogRecord) -> str:
        """Format log record with advanced features."""
        start_time = time.time()

        # Add correlation ID if available
        correlation_id = CorrelationIDManager.get_correlation_id()
        if correlation_id:
            record.correlation_id = correlation_id

        # Validate record if validator is configured
        if self.validator and not self.validator.validate(record):
            # Return empty string for invalid records or log validation error
            return ""

        # Format using base formatter
        formatted = self.base_formatter.format(record)

        # Record metrics
        if self.metrics:
            processing_time = time.time() - start_time
            self.metrics.record_log(record, processing_time)

        return formatted


# Async support using asyncio
class AsyncLogger:
    """Async wrapper for structured logger."""

    def __init__(self, logger: logging.Logger):
        self.logger = logger
        self.loop = None

    async def _log_async(self, level: int, message: str, *args, **kwargs):
        """Log message asynchronously."""
        if self.loop is None:
            self.loop = asyncio.get_event_loop()

        # Run logging in thread pool to avoid blocking
        await self.loop.run_in_executor(None, self.logger.log, level, message, *args)

    async def debug(self, message: str, *args, **kwargs):
        """Log debug message asynchronously."""
        await self._log_async(logging.DEBUG, message, *args, **kwargs)

    async def info(self, message: str, *args, **kwargs):
        """Log info message asynchronously."""
        await self._log_async(logging.INFO, message, *args, **kwargs)

    async def warning(self, message: str, *args, **kwargs):
        """Log warning message asynchronously."""
        await self._log_async(logging.WARNING, message, *args, **kwargs)

    async def error(self, message: str, *args, **kwargs):
        """Log error message asynchronously."""
        await self._log_async(logging.ERROR, message, *args, **kwargs)

    async def critical(self, message: str, *args, **kwargs):
        """Log critical message asynchronously."""
        await self._log_async(logging.CRITICAL, message, *args, **kwargs)
