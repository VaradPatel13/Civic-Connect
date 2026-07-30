"""Structured JSON Logging Configuration for CivicConnect.

Provides a production-grade JSON Formatter and setup utility for standard Python logging,
enabling structured log collection across microservices (ELK, CloudWatch, Datadog).
"""

from __future__ import annotations

import json
import logging
import sys
from datetime import UTC, datetime
from typing import Any

from backend.core.config import settings


class JSONFormatter(logging.Formatter):
    """Custom JSON log formatter producing structured JSON output."""

    def format(self, record: logging.LogRecord) -> str:
        log_entry: dict[str, Any] = {
            "timestamp": datetime.fromtimestamp(record.created, tz=UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "service": settings.app_name,
            "environment": "development" if settings.debug else "production",
        }

        # Include location details for warnings and errors
        if record.levelno >= logging.WARNING:
            log_entry["module"] = record.module
            log_entry["function"] = record.funcName
            log_entry["line"] = record.lineno

        # Include exception trace if present
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)

        # Include extra context parameters attached to log record
        extra_keys = {
            key: value
            for key, value in record.__dict__.items()
            if key
            not in {
                "args",
                "asctime",
                "created",
                "exc_info",
                "exc_text",
                "filename",
                "funcName",
                "levelname",
                "levelno",
                "lineno",
                "module",
                "msecs",
                "message",
                "msg",
                "name",
                "pathname",
                "process",
                "processName",
                "relativeCreated",
                "stack_info",
                "thread",
                "threadName",
                "taskName",
            }
        }
        if extra_keys:
            log_entry["extra"] = extra_keys

        return json.dumps(log_entry)


def setup_logging(log_level: int = logging.INFO) -> None:
    """Configures global structured logging for standard output stream."""
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Remove default handlers to avoid duplicate log outputs
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(JSONFormatter())
    root_logger.addHandler(stream_handler)


__all__ = ["JSONFormatter", "setup_logging"]
