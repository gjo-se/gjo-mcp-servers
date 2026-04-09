"""Integration tests for the scraper MCP server.

Tests run in-process via fastmcp.Client and patch _fetch_search_results_html
to avoid real Playwright/network calls.
"""

from unittest.mock import patch

import pytest
from fastmcp import Client
from starlette.testclient import TestClient

from servers.scraper_server.server import app, mcp
from servers.scraper_server.tools.scrape_freelancermap import RESULT_SELECTOR

_MOCK_URL = "https://test.freelancermap.de/integration-search"
_FETCH_PATCH = (
    "servers.scraper_server.tools.scrape_freelancermap._fetch_search_results_html"
)


@pytest.mark.integration
def test_health_endpoint_returns_ok_payload() -> None:
    """GET /health must return status ok with the correct server name."""
    with TestClient(app) as client:
        response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "server": "scraper-server"}


@pytest.mark.integration
async def test_scrape_freelancermap_tool_is_registered() -> None:
    """scrape_freelancermap must be registered on the MCP server."""
    tool = await mcp.get_tool("scrape_freelancermap")

    assert tool is not None
    assert tool.name == "scrape_freelancermap"


@pytest.mark.integration
async def test_scrape_freelancermap_returns_structured_project_list(
    fixture_html: str,
) -> None:
    """scrape_freelancermap must return a non-empty list of structured project dicts."""
    with patch(_FETCH_PATCH, return_value=(fixture_html, _MOCK_URL)):
        async with Client(mcp) as client:
            result = await client.call_tool(
                "scrape_freelancermap", {"query": "python backend"}
            )

    assert result.is_error is False
    projects: list[dict] = result.structured_content["result"]
    assert isinstance(projects, list)
    assert len(projects) > 0

    first = projects[0]
    assert "title" in first
    assert "url" in first
    assert "skills_raw" in first
    assert "summary" in first


@pytest.mark.integration
async def test_scrape_freelancermap_raises_layout_error_on_empty_html(
    empty_html: str,
) -> None:
    """scrape_freelancermap must return an error result containing url and selector
    when the page contains no recognisable result cards (LayoutChangedError)."""
    with patch(_FETCH_PATCH, return_value=(empty_html, _MOCK_URL)):
        async with Client(mcp) as client:
            result = await client.call_tool(
                "scrape_freelancermap",
                {"query": "python backend"},
                raise_on_error=False,
            )

    assert result.is_error is True
    error_text = result.content[0].text
    assert RESULT_SELECTOR in error_text
    assert _MOCK_URL in error_text
