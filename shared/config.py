"""Zentrale Konfiguration für alle MCP-Server via Pydantic BaseSettings."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Lädt Konfiguration aus .env-Datei und Umgebungsvariablen."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    host: str = "0.0.0.0"
    port_scraper: int = 8001
    port_analyzer: int = 8002
    port_storage: int = 8003
    port_doc: int = 8004
    port_playwright: int = 8005

    database_url: str = (
        "postgresql+asyncpg://postgres:postgres@localhost:5432/mcp_servers"
    )

    log_level: str = "INFO"
    tavily_api_key: str = ""


settings = Settings()
