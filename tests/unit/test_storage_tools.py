"""Unit tests for storage_server tools using in-memory SQLite via conftest fixtures."""

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

import shared.db.session as db_session
from servers.storage_server.tools.query_top_skills import query_top_skills
from servers.storage_server.tools.save_layout_snapshot import save_layout_snapshot
from servers.storage_server.tools.save_skill_frequency import save_skill_frequency
from shared.models.skill import LayoutSnapshot, Skill, SkillFrequency


@pytest.fixture
async def patched_session_factory(
    async_engine: AsyncEngine,
    monkeypatch: pytest.MonkeyPatch,
) -> async_sessionmaker[AsyncSession]:
    """Patch db_session.get_session_factory to use the in-memory test engine.

    Args:
        async_engine: In-memory engine from the shared conftest fixture.
        monkeypatch: pytest monkeypatch helper.

    Returns:
        Session factory bound to the test engine.
    """
    factory = async_sessionmaker(
        bind=async_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    monkeypatch.setattr(
        db_session,
        "get_session_factory",
        lambda database_url=None: factory,
    )
    return factory


@pytest.mark.asyncio
async def test_save_skill_frequency_returns_true_and_persists_entry(
    patched_session_factory: async_sessionmaker[AsyncSession],
) -> None:
    """save_skill_frequency must return True and write the entry to the database."""
    result = await save_skill_frequency("python", 5)

    assert result is True

    async with patched_session_factory() as session:
        skill = (
            await session.execute(
                select(Skill).where(Skill.name == "python")
            )
        ).scalar_one()
        freq = (
            await session.execute(
                select(SkillFrequency).where(SkillFrequency.skill_id == skill.id)
            )
        ).scalar_one()

    assert skill.name == "python"
    assert freq.count == 5


@pytest.mark.asyncio
async def test_query_top_skills_returns_results_sorted_by_count_descending(
    patched_session_factory: async_sessionmaker[AsyncSession],
) -> None:
    """query_top_skills must return rows ordered by count desc, then alpha asc."""
    await save_skill_frequency("fastapi", 1)
    await save_skill_frequency("python", 5)
    await save_skill_frequency("postgresql", 5)

    top = await query_top_skills(limit=3)

    assert top == [
        {"skill": "postgresql", "count": 5},
        {"skill": "python", "count": 5},
        {"skill": "fastapi", "count": 1},
    ]


@pytest.mark.asyncio
async def test_save_layout_snapshot_returns_true_and_persists_snapshot(
    patched_session_factory: async_sessionmaker[AsyncSession],
) -> None:
    """save_layout_snapshot must return True and write the snapshot to the database."""
    result = await save_layout_snapshot(
        url="https://example.test/search",
        tree="<tree>snapshot content</tree>",
        timestamp="2026-04-09T10:00:00+00:00",
        selector="article.result-card",
    )

    assert result is True

    async with patched_session_factory() as session:
        snapshot = (await session.execute(select(LayoutSnapshot))).scalar_one()

    assert snapshot.url == "https://example.test/search"
    assert snapshot.selector == "article.result-card"
    assert snapshot.snapshot_content == "<tree>snapshot content</tree>"


@pytest.mark.asyncio
async def test_query_top_skills_returns_empty_list_when_database_is_empty(
    patched_session_factory: async_sessionmaker[AsyncSession],
) -> None:
    """query_top_skills must return an empty list when no entries exist."""
    result = await query_top_skills(limit=20)

    assert result == []


