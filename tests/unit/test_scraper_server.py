"""Unit tests for the scraper server skeleton."""

import pytest
from starlette.testclient import TestClient

from servers.scraper_server.server import app, mcp


def test_health_endpoint_returns_ok_payload() -> None:
    """Health endpoint should answer with the expected payload."""
    with TestClient(app) as client:
        response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "server": "scraper-server"}


@pytest.mark.asyncio
async def test_scrape_freelancermap_tool_is_registered() -> None:
    """The scraper stub tool should be registered on the MCP server."""
    tool = await mcp.get_tool("scrape_freelancermap")

    assert tool is not None


