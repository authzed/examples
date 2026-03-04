"""
Centralized logging configuration for the Agentic RAG application.

Provides structured JSON logging with context fields for debugging and audit trails.
"""

import logging
import json
import sys
from datetime import datetime
from typing import Any, Dict


class StructuredFormatter(logging.Formatter):
    """
    Custom JSON formatter for structured logging.

    Outputs logs in JSON format with timestamp, level, logger name, message,
    and any extra context fields passed via the 'extra' parameter.
    """

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_data: Dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Add extra context fields from record attributes
        # Skip private/internal attributes
        for key, value in record.__dict__.items():
            if not key.startswith("_") and key not in [
                "name",
                "msg",
                "args",
                "created",
                "filename",
                "funcName",
                "levelname",
                "levelno",
                "lineno",
                "module",
                "msecs",
                "message",
                "pathname",
                "process",
                "processName",
                "relativeCreated",
                "thread",
                "threadName",
                "exc_info",
                "exc_text",
                "stack_info",
            ]:
                # Only add simple JSON-serializable types
                if isinstance(value, (str, int, float, bool, list, dict, type(None))):
                    log_data[key] = value

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_data)


class ContextAdapter(logging.LoggerAdapter):
    """
    Logger adapter that handles extra context fields.

    Wraps the standard logger to properly handle the 'extra' parameter
    and pass it to the StructuredFormatter.
    """

    def process(self, msg: str, kwargs: Dict[str, Any]) -> tuple:
        """Process log call to add extra fields to record."""
        # Extra fields are already handled by the formatter
        # Just pass them through
        return msg, kwargs


def setup_logging(level: str = "INFO") -> None:
    """
    Initialize structured logging configuration.

    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    # Convert string level to logging constant
    numeric_level = getattr(logging, level.upper(), logging.INFO)

    # Create console handler with JSON formatter
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(StructuredFormatter())

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)
    root_logger.handlers.clear()  # Remove existing handlers
    root_logger.addHandler(handler)

    # Reduce noise from third-party libraries
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("openai").setLevel(logging.WARNING)
    logging.getLogger("weaviate").setLevel(logging.WARNING)
    logging.getLogger("grpc").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.LoggerAdapter:
    """
    Get a module-specific logger with context support.

    Args:
        name: Logger name (typically module path like 'nodes.authorization')

    Returns:
        Logger adapter that supports extra context fields
    """
    base_logger = logging.getLogger(f"agentic_rag.{name}")
    return ContextAdapter(base_logger, {})
