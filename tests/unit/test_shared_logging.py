"""Unit tests for shared/logging.py."""

import logging

import pytest

from shared.config import Settings
from shared.logging import configure_logging, get_logger


def test_configure_logging_runs_without_exception() -> None:
    """configure_logging() must complete without raising any exception."""
    configure_logging()  # must not raise


def test_configure_logging_sets_root_level_from_settings(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Root logger level must reflect the LOG_LEVEL setting after configuration."""
    monkeypatch.setenv("LOG_LEVEL", "WARNING")
    monkeypatch.setattr("shared.logging.settings", Settings())

    configure_logging()

    assert logging.getLogger().level == logging.WARNING


def test_configure_logging_attaches_formatter_to_all_handlers() -> None:
    """Every root logger handler must have a Formatter after configure_logging()."""
    configure_logging()

    root_logger = logging.getLogger()
    assert root_logger.handlers, "Root logger must have at least one handler"
    for handler in root_logger.handlers:
        assert handler.formatter is not None, f"Handler {handler!r} has no formatter"


def test_get_logger_returns_logger_with_correct_name() -> None:
    """get_logger() must return a Logger whose name matches the given argument."""
    logger = get_logger("mcp.test.module")

    assert isinstance(logger, logging.Logger)
    assert logger.name == "mcp.test.module"

