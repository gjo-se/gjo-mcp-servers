"""Shared fixtures for all tests."""

import json
from collections.abc import AsyncGenerator
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from shared.db.base import Base

FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
async def async_engine() -> AsyncGenerator[AsyncEngine, None]:
    """Create an in-memory SQLite async engine with all shared tables.

    Yields:
        Configured async engine with all ORM tables created.
    """
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", future=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest.fixture
async def async_session(
    async_engine: AsyncEngine,
) -> AsyncGenerator[AsyncSession, None]:
    """Yield a single async session bound to the in-memory test engine.

    Args:
        async_engine: In-memory engine provided by the async_engine fixture.

    Yields:
        Open async session for use in tests.
    """
    factory = async_sessionmaker(
        bind=async_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    async with factory() as session:
        yield session


@pytest.fixture
def raw_skills() -> list[str]:
    """Load raw (unprocessed) skill labels from the fixture JSON file.

    Returns:
        List of raw skill strings including duplicates, casing variants and typos.
    """
    return json.loads(
        (FIXTURES_DIR / "skills" / "raw_skills.json").read_text(encoding="utf-8")
    )


@pytest.fixture
def normalized_skills() -> list[str]:
    """Load expected normalized skill labels from the fixture JSON file.

    Returns:
        List of normalized skill strings as produced by normalize_skills().
    """
    return json.loads(
        (FIXTURES_DIR / "skills" / "normalized_skills.json").read_text(encoding="utf-8")
    )


@pytest.fixture
def mock_mcp_client() -> MagicMock:
    """Return a MagicMock that mimics a MultiServerMCPClient.

    Returns:
        Preconfigured MagicMock for use in agent and client unit tests.
    """
    return MagicMock()
