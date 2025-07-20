"""
Structured logging configuration with correlation IDs and production-ready features
"""

import json
import logging
import sys
import uuid
from contextlib import contextmanager
from contextvars import ContextVar
from datetime import datetime
from typing import Any, Dict, Optional

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

# Context variable for tracking correlation IDs across async calls
correlation_id_var: ContextVar[Optional[str]] = ContextVar(
    "correlation_id", default=None
)


class StructuredFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging"""

    def __init__(self, service_name: str = "duckdb-macro-rest"):
        self.service_name = service_name
        super().__init__()

    def format(self, record: logging.LogRecord) -> str:
        # Get correlation ID from context
        correlation_id = correlation_id_var.get()

        # Base log structure
        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "service": self.service_name,
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "correlation_id": correlation_id,
        }

        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = {
                "type": record.exc_info[0].__name__ if record.exc_info[0] else None,
                "message": str(record.exc_info[1]) if record.exc_info[1] else None,
                "traceback": (
                    self.formatException(record.exc_info) if record.exc_info else None
                ),
            }

        # Add extra fields from the log record
        extra_fields = {}
        for key, value in record.__dict__.items():
            if key not in [
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
                "message",
            ]:
                extra_fields[key] = value

        if extra_fields:
            log_entry["extra"] = extra_fields

        # Add source location for debugging
        if record.pathname:
            log_entry["source"] = {
                "file": record.filename,
                "function": record.funcName,
                "line": record.lineno,
            }

        return json.dumps(log_entry, default=str, ensure_ascii=False)


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    """Middleware to generate and track correlation IDs for requests"""

    async def dispatch(self, request: Request, call_next):
        # Extract or generate correlation ID
        correlation_id = (
            request.headers.get("x-correlation-id")
            or request.headers.get("x-request-id")
            or str(uuid.uuid4())
        )

        # Set in context variable
        correlation_id_var.set(correlation_id)

        # Add to request state for access in route handlers
        request.state.correlation_id = correlation_id

        # Process the request
        response = await call_next(request)

        # Add correlation ID to response headers
        response.headers["x-correlation-id"] = correlation_id

        return response


def setup_structured_logging(
    service_name: str = "duckdb-macro-rest",
    log_level: str = "INFO",
    enable_json_logging: bool = True,
) -> None:
    """
    Configure structured logging for the application

    Args:
        service_name: Name of the service for log identification
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        enable_json_logging: Whether to use JSON formatting for logs
    """
    # Clear existing handlers
    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)

    if enable_json_logging:
        # Use structured JSON formatter
        formatter = StructuredFormatter(service_name)
    else:
        # Use simple formatter for development
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )

    console_handler.setFormatter(formatter)

    # Configure root logger
    root_logger.setLevel(getattr(logging, log_level.upper()))
    root_logger.addHandler(console_handler)

    # Set specific loggers to appropriate levels
    logging.getLogger("uvicorn").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("fastapi").setLevel(logging.INFO)


@contextmanager
def correlation_context(correlation_id: str):
    """Context manager for setting correlation ID in specific code blocks"""
    token = correlation_id_var.set(correlation_id)
    try:
        yield
    finally:
        correlation_id_var.reset(token)


class StructuredLogger:
    """
    Wrapper for structured logging with convenient methods for common use cases
    """

    def __init__(self, name: str):
        self.logger = logging.getLogger(name)

    def _log_with_extra(self, level: str, message: str, **kwargs):
        """Log with extra structured data"""
        getattr(self.logger, level)(message, extra=kwargs)

    def info(self, message: str, **kwargs):
        """Log info message with structured data"""
        self._log_with_extra("info", message, **kwargs)

    def warning(self, message: str, **kwargs):
        """Log warning message with structured data"""
        self._log_with_extra("warning", message, **kwargs)

    def error(self, message: str, **kwargs):
        """Log error message with structured data"""
        self._log_with_extra("error", message, **kwargs)

    def debug(self, message: str, **kwargs):
        """Log debug message with structured data"""
        self._log_with_extra("debug", message, **kwargs)

    def critical(self, message: str, **kwargs):
        """Log critical message with structured data"""
        self._log_with_extra("critical", message, **kwargs)

    def request_started(self, request: Request):
        """Log request start with structured data"""
        self.info(
            "Request started",
            method=request.method,
            url=str(request.url),
            user_agent=request.headers.get("user-agent"),
            remote_addr=request.client.host if request.client else None,
            content_type=request.headers.get("content-type"),
        )

    def request_completed(
        self, request: Request, response: Response, duration_ms: float
    ):
        """Log request completion with structured data"""
        self.info(
            "Request completed",
            method=request.method,
            url=str(request.url),
            status_code=response.status_code,
            duration_ms=round(duration_ms, 2),
            response_size=response.headers.get("content-length"),
        )

    def macro_execution(
        self,
        macro_name: str,
        parameters: Dict[str, Any],
        duration_ms: float,
        row_count: int,
        success: bool = True,
        error_message: Optional[str] = None,
    ):
        """Log macro execution with structured data"""
        if success:
            self.info(
                "Macro executed successfully",
                macro_name=macro_name,
                parameter_count=len(parameters),
                duration_ms=round(duration_ms, 2),
                row_count=row_count,
            )
        else:
            self.error(
                "Macro execution failed",
                macro_name=macro_name,
                parameter_count=len(parameters),
                duration_ms=round(duration_ms, 2),
                error_message=error_message,
            )

    def database_operation(
        self,
        operation: str,
        duration_ms: float,
        success: bool = True,
        error_message: Optional[str] = None,
        **kwargs,
    ):
        """Log database operations with structured data"""
        if success:
            self.info(
                f"Database {operation} completed",
                operation=operation,
                duration_ms=round(duration_ms, 2),
                **kwargs,
            )
        else:
            self.error(
                f"Database {operation} failed",
                operation=operation,
                duration_ms=round(duration_ms, 2),
                error_message=error_message,
                **kwargs,
            )


def get_structured_logger(name: str) -> StructuredLogger:
    """Get a structured logger instance"""
    return StructuredLogger(name)


# Performance logging decorator
def log_performance(logger: StructuredLogger, operation: str):
    """Decorator to log function performance"""

    def decorator(func):
        import asyncio
        import time
        from functools import wraps

        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                duration_ms = (time.time() - start_time) * 1000
                logger.info(
                    f"{operation} completed",
                    operation=operation,
                    duration_ms=round(duration_ms, 2),
                    function=func.__name__,
                )
                return result
            except Exception as e:
                duration_ms = (time.time() - start_time) * 1000
                logger.error(
                    f"{operation} failed",
                    operation=operation,
                    duration_ms=round(duration_ms, 2),
                    function=func.__name__,
                    error_message=str(e),
                )
                raise

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                duration_ms = (time.time() - start_time) * 1000
                logger.info(
                    f"{operation} completed",
                    operation=operation,
                    duration_ms=round(duration_ms, 2),
                    function=func.__name__,
                )
                return result
            except Exception as e:
                duration_ms = (time.time() - start_time) * 1000
                logger.error(
                    f"{operation} failed",
                    operation=operation,
                    duration_ms=round(duration_ms, 2),
                    function=func.__name__,
                    error_message=str(e),
                )
                raise

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator
