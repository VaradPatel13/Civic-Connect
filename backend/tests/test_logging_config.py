"""
Unit tests for structured JSON logging configuration (PR-02).
"""
import json
import logging

from backend.core.logging_config import JSONFormatter, setup_logging


def test_json_formatter_valid_output():
    """Verify JSONFormatter formats standard log records to valid JSON dicts."""
    formatter = JSONFormatter()
    record = logging.LogRecord(
        name="test_logger",
        level=logging.INFO,
        pathname="test.py",
        lineno=42,
        msg="Test log message with arg %s",
        args=("foo",),
        exc_info=None,
    )
    formatted = formatter.format(record)

    data = json.loads(formatted)
    assert data["level"] == "INFO"
    assert data["logger"] == "test_logger"
    assert data["message"] == "Test log message with arg foo"
    assert "timestamp" in data
    assert "service" in data
    assert "environment" in data


def test_json_formatter_warning_level_location():
    """Verify WARNING level logs include module, function, and line details."""
    formatter = JSONFormatter()
    record = logging.LogRecord(
        name="test_warning",
        level=logging.WARNING,
        pathname="test_module.py",
        lineno=99,
        msg="Warning occurred",
        args=(),
        exc_info=None,
    )
    formatted = formatter.format(record)

    data = json.loads(formatted)
    assert data["level"] == "WARNING"
    assert "module" in data
    assert "function" in data
    assert data["line"] == 99


def test_setup_logging_initialization():
    """Verify setup_logging attaches StreamHandler with JSONFormatter to root logger."""
    setup_logging(log_level=logging.DEBUG)
    root_logger = logging.getLogger()

    assert root_logger.level == logging.DEBUG
    assert len(root_logger.handlers) == 1
    assert isinstance(root_logger.handlers[0].formatter, JSONFormatter)
