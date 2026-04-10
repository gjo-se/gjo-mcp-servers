"""Unit tests for the web_search_server."""

from __future__ import annotations

import pytest
from starlette.testclient import TestClient

import servers.web_search_server.tools.tavily_search as tavily_module
from servers.web_search_server.server import app, mcp
from servers.web_search_server.tools.tavily_search import (
    DOCUMENTATION_DOMAINS,
    NO_DOMAIN_FILTER,
    web_search,
    web_search_documentation,
)

# ---------------------------------------------------------------------------
# Health endpoint
# ---------------------------------------------------------------------------


def test_health_endpoint_returns_ok_payload() -> None:
    """Health endpoint should answer with the expected payload."""
    with TestClient(app) as client:
        response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "server": "web-search-server"}


# ---------------------------------------------------------------------------
# Tool registration
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_web_search_documentation_tool_is_registered() -> None:
    """web_search_documentation must be registered on the MCP server."""
    tool = await mcp.get_tool("web_search_documentation")

    assert tool is not None


@pytest.mark.asyncio
async def test_web_search_tool_is_registered() -> None:
    """web_search must be registered on the MCP server."""
    tool = await mcp.get_tool("web_search")

    assert tool is not None


# ---------------------------------------------------------------------------
# web_search_documentation – functional behaviour
# ---------------------------------------------------------------------------


def test_web_search_documentation_returns_results(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """web_search_documentation should forward the query and return Tavily results."""
    monkeypatch.setenv("TAVILY_API_KEY", "test-key-dummy")

    def fake_invoke(self: object, payload: dict[str, str]) -> dict[str, object]:
        assert payload["query"] == "SQLAlchemy 2.x async_sessionmaker"
        return {
            "results": [
                {
                    "title": "Asynchronous I/O — SQLAlchemy 2.1 Documentation",
                    "url": (
                        "https://docs.sqlalchemy.org/en/latest/orm/extensions/asyncio.html"
                    ),
                    "content": "Use async_sessionmaker to create async sessions.",
                }
            ]
        }

    monkeypatch.setattr(tavily_module.TavilySearch, "invoke", fake_invoke)

    result = web_search_documentation("SQLAlchemy 2.x async_sessionmaker")

    assert "results" in result
    assert (
        result["results"][0]["title"]
        == "Asynchronous I/O — SQLAlchemy 2.1 Documentation"
    )


def test_web_search_documentation_filters_to_configured_domains(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """web_search_documentation must search only within DOCUMENTATION_DOMAINS."""
    monkeypatch.setenv("TAVILY_API_KEY", "test-key-dummy")

    captured_domains: list[list[str]] = []
    original_build = tavily_module.build_tavily_search_tool

    def fake_build(**kwargs: object) -> object:
        captured_domains.append(list(kwargs.get("include_domains", [])))
        return original_build(**kwargs)

    def fake_invoke(self: object, payload: dict[str, str]) -> dict[str, object]:
        return {"results": []}

    monkeypatch.setattr(tavily_module, "build_tavily_search_tool", fake_build)
    monkeypatch.setattr(tavily_module.TavilySearch, "invoke", fake_invoke)

    web_search_documentation("Alembic 1.x autogenerate async")

    assert len(captured_domains) == 1
    assert captured_domains[0] == DOCUMENTATION_DOMAINS


def test_web_search_documentation_raises_on_empty_query() -> None:
    """web_search_documentation should raise ValueError for blank queries."""
    with pytest.raises(ValueError, match="query must not be empty"):
        web_search_documentation("   ")


# ---------------------------------------------------------------------------
# build_tavily_search_tool – guard clauses
# ---------------------------------------------------------------------------


def test_build_tavily_search_tool_raises_on_zero_max_results(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """build_tavily_search_tool should raise ValueError when max_results <= 0."""
    monkeypatch.setenv("TAVILY_API_KEY", "test-key-dummy")

    with pytest.raises(ValueError, match="max_results must be greater than 0"):
        tavily_module.build_tavily_search_tool(max_results=0)


def test_build_tavily_search_tool_no_domain_filter_sentinel(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """build_tavily_search_tool(include_domains=[]) must pass None to TavilySearch."""
    monkeypatch.setenv("TAVILY_API_KEY", "test-key-dummy")

    captured: list[dict[str, object]] = []
    original_init = tavily_module.TavilySearch.__init__

    def fake_init(self: object, **kwargs: object) -> None:
        captured.append(dict(kwargs))
        original_init(self, **kwargs)  # type: ignore[misc]

    monkeypatch.setattr(tavily_module.TavilySearch, "__init__", fake_init)

    tavily_module.build_tavily_search_tool(include_domains=NO_DOMAIN_FILTER)

    assert captured[0]["include_domains"] is None


def test_build_tavily_search_tool_none_uses_documentation_domains(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """build_tavily_search_tool(include_domains=None) must use DOCUMENTATION_DOMAINS."""
    monkeypatch.setenv("TAVILY_API_KEY", "test-key-dummy")

    captured: list[dict[str, object]] = []
    original_init = tavily_module.TavilySearch.__init__

    def fake_init(self: object, **kwargs: object) -> None:
        captured.append(dict(kwargs))
        original_init(self, **kwargs)  # type: ignore[misc]

    monkeypatch.setattr(tavily_module.TavilySearch, "__init__", fake_init)

    tavily_module.build_tavily_search_tool(include_domains=None)

    assert captured[0]["include_domains"] == DOCUMENTATION_DOMAINS


# ---------------------------------------------------------------------------
# web_search – functional behaviour
# ---------------------------------------------------------------------------


def test_web_search_passes_no_domain_filter_to_tavily(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """web_search must build a TavilySearch with include_domains=None (no filter)."""
    monkeypatch.setenv("TAVILY_API_KEY", "test-key-dummy")

    captured: list[dict[str, object]] = []
    original_init = tavily_module.TavilySearch.__init__

    def fake_init(self: object, **kwargs: object) -> None:
        captured.append(dict(kwargs))
        original_init(self, **kwargs)  # type: ignore[misc]

    def fake_invoke(self: object, payload: dict[str, str]) -> dict[str, object]:
        return {"results": [{"title": "Some blog post", "url": "https://example.com"}]}

    monkeypatch.setattr(tavily_module.TavilySearch, "__init__", fake_init)
    monkeypatch.setattr(tavily_module.TavilySearch, "invoke", fake_invoke)

    result = web_search("latest Python packaging news")

    assert "results" in result
    assert len(captured) == 1
    # NO_DOMAIN_FILTER sentinel must translate to None for Tavily
    assert captured[0].get("include_domains") is None


def test_web_search_returns_normalized_dict_on_plain_string_response(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """web_search must normalise a plain-string Tavily response into a dict."""
    monkeypatch.setenv("TAVILY_API_KEY", "test-key-dummy")

    def fake_invoke(self: object, payload: dict[str, str]) -> str:
        return "No search results found."

    monkeypatch.setattr(tavily_module.TavilySearch, "invoke", fake_invoke)

    result = web_search("obscure topic with no results")

    assert isinstance(result, dict)
    assert result["results"] == []
    assert "No search results found." in result["message"]


def test_web_search_raises_on_empty_query() -> None:
    """web_search should raise ValueError for blank queries."""
    with pytest.raises(ValueError, match="query must not be empty"):
        web_search("   ")


def test_web_search_raises_on_zero_max_results() -> None:
    """web_search should raise ValueError when max_results <= 0."""
    with pytest.raises(ValueError, match="max_results must be greater than 0"):
        web_search("valid query", max_results=0)


# ---------------------------------------------------------------------------
# DOCUMENTATION_DOMAINS completeness
# ---------------------------------------------------------------------------


def test_documentation_domains_contains_all_expected_entries() -> None:
    """DOCUMENTATION_DOMAINS must contain all entries from the copilot-instructions."""
    expected = {
        "docs.sqlalchemy.org",
        "alembic.sqlalchemy.org",
        "docs.pytest.org",
        "pytest-asyncio.readthedocs.io",
        "docs.python.org",
        "www.python-httpx.org",
        "playwright.dev",
        "docs.github.com",
        "react.dev",
        "typescriptlang.org",
        "tailwindcss.com",
        "vitejs.dev",
        "reactrouter.com",
    }
    assert expected.issubset(set(DOCUMENTATION_DOMAINS))
