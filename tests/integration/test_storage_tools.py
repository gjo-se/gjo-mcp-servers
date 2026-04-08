"""Integration tests for storage_server tools against SQLite."""

import tempfile
from pathlib import Path

import pytest
from alembic.config import Config
from sqlalchemy import select

import shared.db.session as db_session
from alembic import command
from servers.storage_server.tools.query_top_skills import query_top_skills
from servers.storage_server.tools.save_layout_snapshot import save_layout_snapshot
from servers.storage_server.tools.save_skill_frequency import save_skill_frequency
from shared.models.skill import LayoutSnapshot, Skill, SkillFrequency


@pytest.fixture()
def sqlite_database_url() -> str:
    """Create a temporary SQLite database URL for one test."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        database_path = Path(tmp_dir) / "storage_tools.db"
        yield f"sqlite+aiosqlite:///{database_path}"


@pytest.fixture()
def session_factory_for_test(
    monkeypatch: pytest.MonkeyPatch,
    sqlite_database_url: str,
):
    """Apply Alembic migrations and override the shared session factory."""
    config = Config("alembic.ini")
    config.set_main_option("sqlalchemy.url", sqlite_database_url)
    command.upgrade(config, "head")

    factory = db_session.get_session_factory(sqlite_database_url)
    monkeypatch.setattr(
        db_session,
        "get_session_factory",
        lambda database_url=None: factory,
    )
    return factory


@pytest.mark.asyncio
async def test_save_skill_frequency_persists_and_updates_entries(
    session_factory_for_test,
) -> None:
    """Skill frequencies should be created and updated through the storage tool."""
    assert (
        await save_skill_frequency("Python", 3, source_query="python backend") is True
    )
    assert (
        await save_skill_frequency("python", 5, source_query="python backend") is True
    )

    async with session_factory_for_test() as session:
        skills = (await session.execute(select(Skill))).scalars().all()
        frequencies = (await session.execute(select(SkillFrequency))).scalars().all()

    assert len(skills) == 1
    assert skills[0].name == "python"
    assert len(frequencies) == 1
    assert frequencies[0].count == 5
    assert frequencies[0].source_query == "python backend"


@pytest.mark.asyncio
async def test_query_top_skills_returns_sorted_results(
    session_factory_for_test,
) -> None:
    """Top-skill queries should be ordered by count descending and skill ascending."""
    await save_skill_frequency("fastapi", 2)
    await save_skill_frequency("python", 5)
    await save_skill_frequency("postgresql", 5)

    top_skills = await query_top_skills(limit=3)

    assert top_skills == [
        {"skill": "postgresql", "count": 5},
        {"skill": "python", "count": 5},
        {"skill": "fastapi", "count": 2},
    ]


@pytest.mark.asyncio
async def test_save_layout_snapshot_persists_snapshot_data(
    session_factory_for_test,
) -> None:
    """Layout snapshots should be stored with URL, selector and content."""
    assert (
        await save_layout_snapshot(
            url="https://example.test/search",
            tree="<tree>snapshot</tree>",
            timestamp="2026-04-08T12:00:00+00:00",
            selector="article.result-card",
        )
        is True
    )

    async with session_factory_for_test() as session:
        snapshots = (await session.execute(select(LayoutSnapshot))).scalars().all()

    assert len(snapshots) == 1
    assert snapshots[0].url == "https://example.test/search"
    assert snapshots[0].selector == "article.result-card"
    assert snapshots[0].snapshot_content == "<tree>snapshot</tree>"


