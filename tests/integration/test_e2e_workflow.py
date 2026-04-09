"""End-to-End integration tests crossing scraper, analyzer and storage servers.

Both workflows run in-process via fastmcp.Client:

  Primary:         scrape → normalize → analyze → save_skill_frequency → query
  Layout-Recovery: scrape (empty) → LayoutChangedError → save_layout_snapshot → verify
"""

from datetime import UTC, datetime
from unittest.mock import patch

import pytest
from fastmcp import Client
from sqlalchemy import select

from servers.scraper_server.server import mcp as scraper_mcp
from servers.skills_analyzer_server.server import mcp as analyzer_mcp
from servers.storage_server.server import mcp as storage_mcp
from shared.models.skill import LayoutSnapshot

_FETCH_PATCH = (
    "servers.scraper_server.tools.scrape_freelancermap._fetch_search_results_html"
)
_SCRAPE_URL = "https://test.e2e.freelancermap.de/search"


@pytest.mark.integration
async def test_primary_workflow_scrape_normalize_analyze_store_query(
    isolated_storage_factory,
    fixture_html: str,
) -> None:
    """Primary E2E: scrape → normalize → analyze → store → query.

    Runs via MCP clients across three independent server instances.
    The fixture HTML produces 2 projects with 6 raw skills total.
    """
    # Step 1: Scrape (Playwright mocked with fixture HTML)
    with patch(_FETCH_PATCH, return_value=(fixture_html, _SCRAPE_URL)):
        async with Client(scraper_mcp) as client:
            scrape_result = await client.call_tool(
                "scrape_freelancermap", {"query": "python backend"}
            )

    assert scrape_result.is_error is False
    projects: list[dict] = scrape_result.structured_content["result"]
    assert len(projects) > 0

    # Extract raw skills from all scraped projects
    raw_skills: list[str] = []
    for project in projects:
        skills_str: str = project.get("skills_raw", "")
        if skills_str:
            raw_skills.extend(s.strip() for s in skills_str.split(",") if s.strip())

    assert len(raw_skills) > 0

    # Step 2: Normalize raw skills
    async with Client(analyzer_mcp) as client:
        normalize_result = await client.call_tool(
            "normalize_skills", {"raw_skills": raw_skills}
        )
        assert normalize_result.is_error is False
        normalized: list[str] = normalize_result.structured_content["result"]

        # Step 3: Analyze frequency
        freq_result = await client.call_tool(
            "analyze_frequency", {"skills": normalized}
        )
        assert freq_result.is_error is False
        frequencies: list[dict] = freq_result.structured_content["result"]

    assert len(frequencies) > 0
    assert all("skill" in f and "count" in f for f in frequencies)

    # Step 4: Persist each skill frequency (prefixed for test isolation)
    async with Client(storage_mcp) as client:
        for entry in frequencies:
            save_result = await client.call_tool(
                "save_skill_frequency",
                {"skill": f"e2e-{entry['skill']}", "count": entry["count"]},
            )
            assert save_result.data is True

        # Step 5: Query top skills and verify stored entries are present
        query_result = await client.call_tool("query_top_skills", {"limit": 20})

    assert query_result.is_error is False
    top_skills: list[dict] = query_result.structured_content["result"]
    e2e_skills = [s for s in top_skills if s["skill"].startswith("e2e-")]

    assert len(e2e_skills) > 0
    # python appears in both fixture projects → must be the top e2e skill
    top_e2e = max(e2e_skills, key=lambda s: s["count"])
    assert top_e2e["skill"] == "e2e-python"
    assert top_e2e["count"] == 2


@pytest.mark.integration
async def test_layout_recovery_workflow_error_to_snapshot_persistence(
    isolated_storage_factory,
    empty_html: str,
) -> None:
    """Layout-Recovery E2E (server level):
    scrape returns LayoutChangedError → save_layout_snapshot → DB confirms snapshot.

    This test validates the server-side half of the recovery workflow that the
    LangGraph agent (T-15) orchestrates end-to-end.
    """
    recovery_url = "https://test.e2e/layout-recovery"

    # Step 1: Scraper fails with LayoutChangedError on empty HTML
    with patch(_FETCH_PATCH, return_value=(empty_html, recovery_url)):
        async with Client(scraper_mcp) as client:
            scrape_result = await client.call_tool(
                "scrape_freelancermap",
                {"query": "recovery-trigger"},
                raise_on_error=False,
            )

    assert scrape_result.is_error is True
    # Error message must include the url and selector for downstream recovery
    error_text: str = scrape_result.content[0].text
    assert recovery_url in error_text
    assert "article.result-card" in error_text

    # Step 2: Persist the layout snapshot (simulates what the LangGraph agent does)
    captured_at = datetime.now(UTC).isoformat()
    snapshot_tree = "<recovery-tree>simulated accessibility snapshot</recovery-tree>"

    async with Client(storage_mcp) as client:
        snapshot_result = await client.call_tool(
            "save_layout_snapshot",
            {
                "url": recovery_url,
                "tree": snapshot_tree,
                "timestamp": captured_at,
                "selector": "article.result-card",
            },
        )

    assert snapshot_result.is_error is False
    assert snapshot_result.data is True

    # Step 3: Verify snapshot is persisted in the database
    async with isolated_storage_factory() as session:
        db_result = await session.execute(
            select(LayoutSnapshot).where(LayoutSnapshot.url == recovery_url)
        )
        snapshot = db_result.scalar_one_or_none()

    assert snapshot is not None
    assert "simulated accessibility snapshot" in snapshot.snapshot_content
    assert snapshot.selector == "article.result-card"






