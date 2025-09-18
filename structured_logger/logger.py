"""
Structured JSON logger with flexible configuration for Python applications.
"""
import json
import logging
import os
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List, Callable
from uuid import UUID


@dataclass
class LoggerConfig:
    """Configuration class for structured logger."""
    
    # Environment detection
    production_env_vars: List[str] = field(default_factory=lambda: [
        "RAILWAY_ENVIRONMENT", "ENV", "ENVIRONMENT", "NODE_ENV"
    ])
    production_env_values: List[str] = field(default_factory=lambda: [
        "prod", "production", "staging"
    ])
    
    # Log level configuration
    log_level_env_var: str = "LOG_LEVEL"
    default_log_level: str = "INFO"
    
    # Custom fields to extract from log records
    custom_fields: List[str] = field(default_factory=lambda: [
        "user_id", "company_id", "request_id", "trace_id", "span_id"
    ])
    
    # Time format
    time_format: Optional[str] = None
    
    # Development formatter
    dev_format: str = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    
    # Custom serializers for specific types
    custom_serializers: Dict[type, Callable] = field(default_factory=dict)
    
    # Whether to include extra attributes in logs
    include_extra_attrs: bool = True
    
    # Fields to exclude from extra attributes
    excluded_attrs: List[str] = field(default_factory=lambda: [
        'name', 'msg', 'args', 'levelname', 'levelno', 'pathname', 'filename', 
        'module', 'lineno', 'funcName', 'created', 'msecs', 'relativeCreated', 
        'thread', 'threadName', 'processName', 'process', 'getMessage', 'exc_info', 
        'exc_text', 'stack_info'
    ])


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
        elif hasattr(value, '__dict__'):
            # For complex objects, try to convert to dict
            try:
                return {
                    k: self._serialize_value(v) 
                    for k, v in value.__dict__.items() 
                    if not k.startswith('_')
                }
            except Exception:
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
                log_record[field_name] = self._serialize_value(getattr(record, field_name))
        
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
    """Check if we're running in a production environment."""
    for env_var in config.production_env_vars:
        env_value = os.getenv(env_var, "").lower()
        if env_value in [v.lower() for v in config.production_env_values]:
            return True
    return False


def get_logger(
    name: Optional[str] = None,
    config: Optional[LoggerConfig] = None,
    force_json: bool = False,
    force_dev: bool = False
) -> logging.Logger:
    """
    Get a structured logger instance with flexible configuration.
    
    Args:
        name: Logger name, defaults to calling module name
        config: Logger configuration, uses default if not provided
        force_json: Force JSON formatting regardless of environment
        force_dev: Force development formatting regardless of environment
        
    Returns:
        Configured logger instance
    """
    logger_name = name or __name__
    logger = logging.getLogger(logger_name)
    
    # Only configure if not already configured
    if not logger.handlers:
        config = config or LoggerConfig()
        
        # Set log level from environment or config default
        log_level = os.getenv(config.log_level_env_var, config.default_log_level).upper()
        logger.setLevel(getattr(logging, log_level, logging.INFO))
        
        # Create console handler
        handler = logging.StreamHandler()
        
        # Determine formatter based on environment and override flags
        use_json = force_json or (not force_dev and _is_production_environment(config))
        
        if use_json:
            formatter = StructuredLogFormatter(config)
        else:
            formatter = logging.Formatter(config.dev_format)
        
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
        # Prevent duplicate logs
        logger.propagate = False
    
    return logger


def setup_root_logger(
    config: Optional[LoggerConfig] = None,
    force_json: bool = False,
    force_dev: bool = False
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
    handler = logging.StreamHandler()
    
    # Determine formatter
    use_json = force_json or (not force_dev and _is_production_environment(config))
    
    if use_json:
        formatter = StructuredLogFormatter(config)
    else:
        formatter = logging.Formatter(config.dev_format)
    
    handler.setFormatter(formatter)
    root_logger.addHandler(handler)


# Backward compatibility aliases
def get_railway_logger(name: Optional[str] = None) -> logging.Logger:
    """Alias for get_logger for Railway compatibility."""
    return get_logger(name)


def get_structured_logger(name: Optional[str] = None, **kwargs) -> logging.Logger:
    """Alias for get_logger with explicit naming."""
    return get_logger(name, **kwargs)