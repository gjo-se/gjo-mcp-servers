"""Unit tests for the skills analyzer server and its tools."""

import json
from pathlib import Path

import pytest
from starlette.testclient import TestClient

from servers.skills_analyzer_server.server import MCP_PATH, mcp
from servers.skills_analyzer_server.tools.analyze_frequency import analyze_frequency
from servers.skills_analyzer_server.tools.normalize_skills import normalize_skills

FIXTURE_DIR = Path(__file__).parent.parent / "fixtures" / "skills"


def _load_fixture(name: str) -> list[str]:
    """Load a JSON fixture file with skill labels."""
    return json.loads((FIXTURE_DIR / name).read_text(encoding="utf-8"))


def test_normalize_skills_matches_fixture_output() -> None:
    """normalize_skills should convert raw skill labels deterministically."""
    raw_skills = _load_fixture("raw_skills.json")
    expected = _load_fixture("normalized_skills.json")

    assert normalize_skills(raw_skills) == expected


def test_analyze_frequency_counts_and_sorts_correctly() -> None:
    """analyze_frequency should sort by count descending and then alphabetically."""
    normalized_skills = _load_fixture("normalized_skills.json")

    result = analyze_frequency(normalized_skills)

    assert result == [
        {"skill": "python", "count": 3},
        {"skill": "postgresql", "count": 2},
        {"skill": "fastapi", "count": 1},
        {"skill": "typescript", "count": 1},
    ]


def test_health_endpoint_returns_ok_payload() -> None:
    """Health endpoint should answer with the expected payload."""
    test_app = mcp.http_app(path=MCP_PATH, transport="http")

    with TestClient(test_app) as client:
        response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "server": "skills-analyzer-server",
    }


@pytest.mark.asyncio
async def test_tools_are_registered() -> None:
    """Both analyzer tools should be registered on the MCP server."""
    normalize_tool = await mcp.get_tool("normalize_skills")
    frequency_tool = await mcp.get_tool("analyze_frequency")

    assert normalize_tool is not None
    assert frequency_tool is not None
