"""Unit Tests für shared/config.py."""

from shared.config import Settings


def test_settings_defaults() -> None:
    """Settings-Defaults stimmen mit .env.example überein."""
    settings = Settings()

    assert settings.host == "0.0.0.0"
    assert settings.port_scraper == 8001
    assert settings.port_analyzer == 8002
    assert settings.port_storage == 8003
    assert settings.port_doc == 8004
    assert settings.port_playwright == 8005
    assert (
        settings.database_url
        == "postgresql+asyncpg://postgres:postgres@localhost:5432/mcp_servers"
    )
    assert settings.log_level == "INFO"
    assert settings.tavily_api_key == ""


def test_settings_override_via_env(monkeypatch) -> None:
    """Umgebungsvariablen überschreiben Defaults korrekt."""
    monkeypatch.setenv("HOST", "127.0.0.1")
    monkeypatch.setenv("PORT_SCRAPER", "9001")
    monkeypatch.setenv("LOG_LEVEL", "DEBUG")
    monkeypatch.setenv("TAVILY_API_KEY", "secret")

    settings = Settings()

    assert settings.host == "127.0.0.1"
    assert settings.port_scraper == 9001
    assert settings.log_level == "DEBUG"
    assert settings.tavily_api_key == "secret"
