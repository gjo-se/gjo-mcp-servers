"""Integration tests for the storage MCP server.

Every test uses isolated_storage_factory to get a fresh SQLite DB with
applied Alembic migrations. Tests are fully independent of each other.
"""

import pytest
from fastmcp import Client
from sqlalchemy import select
from starlette.testclient import TestClient

from servers.storage_server.server import app, mcp
from shared.models.skill import LayoutSnapshot


@pytest.mark.integration
def test_health_endpoint_returns_ok_payload() -> None:
    """GET /health must return status ok with the correct server name."""
    with TestClient(app) as client:
        response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "server": "storage-server"}


@pytest.mark.integration
async def test_save_skill_frequency_returns_true(isolated_storage_factory) -> None:
    """save_skill_frequency must persist a new entry and return True."""
    async with Client(mcp) as client:
        result = await client.call_tool(
            "save_skill_frequency",
            {"skill": "python", "count": 3},
        )

    assert result.is_error is False
    assert result.data is True


@pytest.mark.integration
async def test_query_top_skills_returns_results_sorted_by_count(
    isolated_storage_factory,
) -> None:
    """query_top_skills must return entries sorted by count descending."""
    async with Client(mcp) as client:
        await client.call_tool("save_skill_frequency", {"skill": "fastapi", "count": 2})
        await client.call_tool("save_skill_frequency", {"skill": "python", "count": 5})
        await client.call_tool("save_skill_frequency", {"skill": "docker", "count": 1})

        result = await client.call_tool("query_top_skills", {"limit": 3})

    assert result.is_error is False
    skills: list[dict] = result.structured_content["result"]
    assert len(skills) == 3

    names = [s["skill"] for s in skills]
    assert names[0] == "python"
    assert names[1] == "fastapi"
    assert names[2] == "docker"
    assert skills[0]["count"] == 5
    assert skills[1]["count"] == 2
    assert skills[2]["count"] == 1


@pytest.mark.integration
async def test_save_layout_snapshot_returns_true(isolated_storage_factory) -> None:
    """save_layout_snapshot must persist a snapshot and return True."""
    async with Client(mcp) as client:
        result = await client.call_tool(
            "save_layout_snapshot",
            {
                "url": "https://test.integration/snapshot",
                "tree": "<tree>snapshot</tree>",
                "timestamp": "2026-04-09T12:00:00+00:00",
                "selector": "article.result-card",
            },
        )

    assert result.is_error is False
    assert result.data is True


@pytest.mark.integration
async def test_save_layout_snapshot_persists_to_database(
    isolated_storage_factory,
) -> None:
    """save_layout_snapshot must write the snapshot so a direct DB query confirms it."""
    snapshot_url = "https://test.integration/persisted-snapshot"

    async with Client(mcp) as client:
        await client.call_tool(
            "save_layout_snapshot",
            {
                "url": snapshot_url,
                "tree": "<tree>persisted content</tree>",
                "timestamp": "2026-04-09T13:00:00+00:00",
                "selector": "article.result-card",
            },
        )

    async with isolated_storage_factory() as session:
        db_result = await session.execute(
            select(LayoutSnapshot).where(LayoutSnapshot.url == snapshot_url)
        )
        snapshot = db_result.scalar_one_or_none()

    assert snapshot is not None
    assert snapshot.snapshot_content == "<tree>persisted content</tree>"
    assert snapshot.selector == "article.result-card"


@pytest.mark.integration
async def test_query_top_skills_on_empty_database_returns_empty_list(
    isolated_storage_factory,
) -> None:
    """query_top_skills on a freshly migrated DB must return an empty list."""
    async with Client(mcp) as client:
        result = await client.call_tool("query_top_skills", {"limit": 20})

    assert result.is_error is False
    assert result.structured_content["result"] == []



