"""Shared fixtures for integration tests.

Integration tests run in-process via fastmcp.Client – kein Docker erforderlich.
Jeder Test, der Storage benötigt, erhält über isolated_storage_factory eine
frische SQLite-Datenbank mit aktuellen Alembic-Migrationen.
"""

from pathlib import Path

import pytest
from alembic.config import Config

import shared.db.session as db_session
from alembic import command

PROJECT_ROOT = Path(__file__).parent.parent.parent
FIXTURES_DIR = Path(__file__).parent.parent / "fixtures"


def _migrate_sqlite(db_url: str) -> None:
    """Run Alembic migrations against the given SQLite URL.

    Args:
        db_url: SQLite async URL, e.g. ``sqlite+aiosqlite:///path/to/db``.
    """
    alembic_config = Config(str(PROJECT_ROOT / "alembic.ini"))
    alembic_config.set_main_option("sqlalchemy.url", db_url)
    command.upgrade(alembic_config, "head")


@pytest.fixture()
def isolated_storage_factory(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    """Provide a fresh SQLite DB with applied migrations for one test.

    Patches ``db_session.get_session_factory`` so that all storage-server
    tool calls within the test use the isolated database.

    Args:
        monkeypatch: pytest monkeypatch fixture.
        tmp_path: pytest-provided per-test temporary directory.

    Returns:
        ``async_sessionmaker`` pointing to the isolated test DB.
    """
    db_url = f"sqlite+aiosqlite:///{tmp_path}/test.db"
    _migrate_sqlite(db_url)

    factory = db_session.get_session_factory(db_url)
    monkeypatch.setattr(
        db_session,
        "get_session_factory",
        lambda database_url=None: factory,
    )
    return factory


@pytest.fixture()
def fixture_html() -> str:
    """Return the freelancermap sample HTML fixture with two result cards.

    Returns:
        Raw HTML string loaded from ``tests/fixtures/html/freelancermap_sample.html``.
    """
    return (FIXTURES_DIR / "html" / "freelancermap_sample.html").read_text(
        encoding="utf-8"
    )


@pytest.fixture()
def empty_html() -> str:
    """Return minimal HTML that contains no result cards.

    Used to trigger ``LayoutChangedError`` in scraper tests.

    Returns:
        Minimal HTML string with an empty results section.
    """
    return "<html><body><section class='results'></section></body></html>"

