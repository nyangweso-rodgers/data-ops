"""
Centralized logging configuration for Dagster pipeline

DESIGN PRINCIPLES:
- Single source of truth for all logging configuration
- Environment-aware (local, dev, prod)
- Structured logging with consistent format
- Integration with Dagster's context logger
"""

import logging
import sys
import os
from typing import Optional, Dict, Any
import structlog
from enum import Enum


class Environment(Enum):
    """Deployment environments"""
    LOCAL = "local"
    DEV = "dev"
    PROD = "prod"


class LogLevel(Enum):
    """Log levels mapping"""
    DEBUG = logging.DEBUG
    INFO = logging.INFO
    WARNING = logging.WARNING
    ERROR = logging.ERROR
    CRITICAL = logging.CRITICAL


# Environment-specific log levels
ENV_LOG_LEVELS = {
    Environment.LOCAL: LogLevel.DEBUG,
    Environment.DEV: LogLevel.INFO,
    Environment.PROD: LogLevel.WARNING
}


def get_environment() -> Environment:
    """
    Detect current environment from ENV variable
    
    Returns:
        Environment enum value
    """
    env_str = os.getenv("DAGSTER_ENV", "prod").lower()
    try:
        return Environment(env_str)
    except ValueError:
        # Default to prod if invalid
        return Environment.PROD


def configure_structlog(
    env: Optional[Environment] = None,
    json_logs: bool = True
):
    """
    Configure structlog for structured logging
    
    Args:
        env: Environment (auto-detected if None)
        json_logs: If True, output JSON. If False, use console renderer (for local dev)
    """
    if env is None:
        env = get_environment()
    
    # Choose renderer based on environment and preference
    if json_logs and env == Environment.PROD:
        renderer = structlog.processors.JSONRenderer()
    else:
        # Console renderer for local development (more readable)
        renderer = structlog.dev.ConsoleRenderer(colors=True)
    
    structlog.configure(
        processors=[
            # Add log level to event dict
            structlog.processors.add_log_level,
            # Add timestamp
            structlog.processors.TimeStamper(fmt="iso", utc=True),
            # Add exception info if present
            structlog.processors.format_exc_info,
            # Stack info renderer
            structlog.processors.StackInfoRenderer(),
            # Final rendering
            renderer,
        ],
        wrapper_class=structlog.make_filtering_bound_logger(
            ENV_LOG_LEVELS[env].value
        ),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(
    name: str,
    context: Optional[Dict[str, Any]] = None
) -> structlog.BoundLogger:
    """
    Get a configured structlog logger instance
    
    Args:
        name: Logger name (typically __name__ of the module)
        context: Initial context to bind to logger (e.g., table, database)
    
    Returns:
        Configured structlog BoundLogger
    
    Example:
        >>> logger = get_logger(__name__)
        >>> logger.info("operation_started", table="accounts", rows=100)
        
        >>> # With initial context
        >>> logger = get_logger(__name__, {"database": "amtdb", "table": "accounts"})
        >>> logger.info("extraction_started")  # Context automatically included
    """
    logger = structlog.get_logger(name)
    
    if context:
        logger = logger.bind(**context)
    
    return logger


def setup_logging(
    env: Optional[Environment] = None,
    json_logs: Optional[bool] = None
):
    """
    Setup logging for the entire application
    
    Call this once at application startup (e.g., in definitions.py)
    
    Args:
        env: Environment to configure for (auto-detected if None)
        json_logs: Whether to use JSON output (auto-detected if None)
    """
    if env is None:
        env = get_environment()
    
    if json_logs is None:
        # Use JSON logs in prod, console in local/dev
        json_logs = (env == Environment.PROD)
    
    # Configure structlog
    configure_structlog(env=env, json_logs=json_logs)
    
    # Configure Python's built-in logging to work with structlog
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=ENV_LOG_LEVELS[env].value,
    )
    
    # Suppress noisy third-party loggers
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("requests").setLevel(logging.WARNING)
    logging.getLogger("boto3").setLevel(logging.WARNING)
    logging.getLogger("botocore").setLevel(logging.WARNING)
    
    # Log that logging is configured
    logger = get_logger(__name__)
    logger.info(
        "logging_configured",
        environment=env.value,
        log_level=ENV_LOG_LEVELS[env].name,
        json_output=json_logs
    )


# Context manager for timing operations
from contextlib import contextmanager
import time


@contextmanager
def log_execution_time(
    logger: structlog.BoundLogger,
    operation: str,
    **context
):
    """
    Context manager to automatically log operation execution time
    
    Args:
        logger: Structlog logger instance
        operation: Name of the operation (e.g., "data_extraction", "schema_validation")
        **context: Additional context to include in logs
    
    Example:
        >>> logger = get_logger(__name__)
        >>> with log_execution_time(logger, "data_extraction", table="accounts", batch=1):
        ...     extract_data()
        
        # Logs:
        # {"event": "data_extraction_started", "table": "accounts", "batch": 1}
        # {"event": "data_extraction_completed", "table": "accounts", "batch": 1, "duration_seconds": 2.34}
    """
    start_time = time.time()
    logger.info(f"{operation}_started", **context)
    
    try:
        yield
        duration = time.time() - start_time
        logger.info(
            f"{operation}_completed",
            duration_seconds=round(duration, 2),
            **context
        )
    except Exception as e:
        duration = time.time() - start_time
        logger.error(
            f"{operation}_failed",
            duration_seconds=round(duration, 2),
            error=str(e),
            error_type=type(e).__name__,
            **context,
            exc_info=True
        )
        raise


# Decorator for automatic function timing
from functools import wraps


def log_function_call(operation_name: Optional[str] = None):
    """
    Decorator to automatically log function calls and execution time
    
    Args:
        operation_name: Custom operation name (defaults to function name)
    
    Example:
        >>> @log_function_call("schema_loading")
        >>> def load_schema(database: str, table: str):
        ...     # Function implementation
        ...     pass
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            logger = get_logger(func.__module__)
            op_name = operation_name or func.__name__
            
            with log_execution_time(logger, op_name, function=func.__name__):
                return func(*args, **kwargs)
        
        return wrapper
    return decorator


# Helper to sanitize sensitive data in logs
def sanitize_log_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Remove sensitive information from log data
    
    Args:
        data: Dictionary that might contain sensitive keys
    
    Returns:
        Sanitized dictionary
    """
    sensitive_keys = {
        'password', 'passwd', 'pwd', 'secret', 'token', 
        'api_key', 'apikey', 'access_key', 'private_key',
        'auth', 'authorization', 'credentials'
    }
    
    sanitized = {}
    for key, value in data.items():
        key_lower = key.lower()
        
        # Check if key contains sensitive information
        if any(sensitive in key_lower for sensitive in sensitive_keys):
            sanitized[key] = "***REDACTED***"
        elif isinstance(value, dict):
            sanitized[key] = sanitize_log_data(value)
        else:
            sanitized[key] = value
    
    return sanitized