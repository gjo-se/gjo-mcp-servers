"""Integration tests for the skills analyzer MCP server.

Tests run in-process via fastmcp.Client against the actual tool implementations.
"""

import pytest
from fastmcp import Client
from starlette.testclient import TestClient

from servers.skills_analyzer_server.server import app, mcp


@pytest.mark.integration
def test_health_endpoint_returns_ok_payload() -> None:
    """GET /health must return status ok with the correct server name."""
    with TestClient(app) as client:
        response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "server": "skills-analyzer-server"}


@pytest.mark.integration
async def test_normalize_skills_and_analyze_frequency_tools_are_registered() -> None:
    """Both analyzer tools must be registered on the MCP server."""
    normalize_tool = await mcp.get_tool("normalize_skills")
    frequency_tool = await mcp.get_tool("analyze_frequency")

    assert normalize_tool is not None
    assert frequency_tool is not None


@pytest.mark.integration
async def test_normalize_skills_normalizes_casing_variants() -> None:
    """normalize_skills must return lowercase-normalized labels for all casing variants.
    """
    async with Client(mcp) as client:
        result = await client.call_tool(
            "normalize_skills",
            {"raw_skills": ["Python", "python", "PYTHON"]},
        )

    assert result.is_error is False
    assert result.data == ["python", "python", "python"]


@pytest.mark.integration
async def test_normalize_skills_applies_synonym_mapping() -> None:
    """normalize_skills must resolve known abbreviations to canonical names."""
    async with Client(mcp) as client:
        result = await client.call_tool(
            "normalize_skills",
            {"raw_skills": ["py", "ts", "pg"]},
        )

    assert result.is_error is False
    assert result.data == ["python", "typescript", "postgresql"]


@pytest.mark.integration
async def test_analyze_frequency_sorts_by_count_descending() -> None:
    """analyze_frequency must return skills sorted by count descending."""
    async with Client(mcp) as client:
        result = await client.call_tool(
            "analyze_frequency",
            {"skills": ["python", "python", "fastapi"]},
        )

    assert result.is_error is False
    frequencies: list[dict] = result.structured_content["result"]
    assert len(frequencies) == 2

    top = frequencies[0]
    assert top["skill"] == "python"
    assert top["count"] == 2

    second = frequencies[1]
    assert second["skill"] == "fastapi"
    assert second["count"] == 1


