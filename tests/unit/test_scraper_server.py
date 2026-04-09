"""Unit tests for the scraper server skeleton."""

import pytest
from starlette.testclient import TestClient

from servers.scraper_server.server import MCP_PATH, mcp


def test_health_endpoint_returns_ok_payload() -> None:
    """Health endpoint should answer with the expected payload."""
    test_app = mcp.http_app(path=MCP_PATH, transport="http")

    with TestClient(test_app) as client:
        response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "server": "scraper-server"}


@pytest.mark.asyncio
async def test_scrape_freelancermap_tool_is_registered() -> None:
    """The scraper stub tool should be registered on the MCP server."""
    tool = await mcp.get_tool("scrape_freelancermap")

    assert tool is not None
