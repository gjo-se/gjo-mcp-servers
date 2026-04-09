"""Unit tests for shared/config.py."""

import logging

import pytest
from pydantic import ValidationError

from shared.config import Settings


def test_settings_default_ports_match_allocation_spec() -> None:
    """Default port values must match the agreed server allocation spec."""
    settings = Settings()

    assert settings.port_scraper == 8001
    assert settings.port_analyzer == 8002
    assert settings.port_storage == 8003
    assert settings.port_doc == 8004
    assert settings.port_playwright == 8005


def test_log_level_default_is_valid_python_logging_level() -> None:
    """Default LOG_LEVEL must resolve to a known Python logging constant."""
    settings = Settings()

    level_value = getattr(logging, settings.log_level.upper(), None)

    assert level_value is not None
    assert isinstance(level_value, int)


def test_settings_env_override_applies_to_all_overridden_fields(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Environment variables must override the matching Settings fields."""
    monkeypatch.setenv("PORT_SCRAPER", "9001")
    monkeypatch.setenv("LOG_LEVEL", "DEBUG")
    monkeypatch.setenv("TAVILY_API_KEY", "test-key")

    settings = Settings()

    assert settings.port_scraper == 9001
    assert settings.log_level == "DEBUG"
    assert settings.tavily_api_key == "test-key"


def test_invalid_port_type_raises_validation_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A non-integer port value must raise a Pydantic ValidationError."""
    monkeypatch.setenv("PORT_SCRAPER", "not-a-number")

    with pytest.raises(ValidationError):
        Settings()

