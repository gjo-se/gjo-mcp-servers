"""Unit tests for the doc_server."""

import json

import httpx
import pytest
from starlette.testclient import TestClient

import servers.doc_server.server as doc_server_module
from servers.doc_server.server import DOC_SOURCES, app, fetch_fastapi_docs, mcp
from servers.doc_server.tools.web_search import DOCUMENTATION_DOMAINS


@pytest.mark.asyncio
async def test_fetch_fastapi_docs_uses_configured_source(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The FastAPI docs tool should use the configured llms.txt source."""

    async def fake_fetch(url: str) -> str:
        assert url == DOC_SOURCES["fastapi"]
        return "FastAPI current docs\nQuery anchor"

    monkeypatch.setattr(doc_server_module, "_fetch_llms_txt_content", fake_fetch)

    result = await fetch_fastapi_docs("query")

    assert result["source"] == "fastapi"
    assert result["url"] == DOC_SOURCES["fastapi"]
    assert result["content"] == "Query anchor"


@pytest.mark.asyncio
async def test_fetch_fastapi_docs_falls_back_to_official_search(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The FastAPI docs tool should fall back to official-domain search on 404."""

    async def fake_fetch(url: str) -> str:
        request = httpx.Request("GET", url)
        response = httpx.Response(status_code=404, request=request)
        raise httpx.HTTPStatusError("Not Found", request=request, response=response)

    def fake_search(
        query: str,
        *,
        include_domains: tuple[str, ...],
        max_results: int,
        include_answer: bool,
        description: str,
    ) -> dict[str, object]:
        assert query == "lifespan"
        assert include_domains == ("fastapi.tiangolo.com",)
        assert max_results == 3
        assert include_answer is True
        assert "official FastAPI documentation" in description
        return {
            "answer": "Use the lifespan parameter instead of startup/shutdown events.",
            "results": [
                {
                    "title": "Lifespan Events - FastAPI",
                    "url": "https://fastapi.tiangolo.com/advanced/events/",
                    "content": "Use the lifespan parameter with an async context manager.",
                }
            ],
        }

    monkeypatch.setattr(doc_server_module, "_fetch_llms_txt_content", fake_fetch)
    monkeypatch.setattr(doc_server_module, "search_documentation", fake_search)

    result = await fetch_fastapi_docs("lifespan")

    assert result["source"] == "fastapi"
    assert result["url"] == DOC_SOURCES["fastapi"]
    assert result["resolved_via"] == "official_search_fallback"
    assert result["fallback_reason"] == f"404 at {DOC_SOURCES['fastapi']}"
    assert "Lifespan Events - FastAPI" in result["content"]
    assert "Use the lifespan parameter" in result["content"]


@pytest.mark.asyncio
async def test_fetch_fastapi_docs_accepts_plain_string_search_fallback(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The FastAPI docs fallback should accept plain string search results."""

    async def fake_fetch(url: str) -> str:
        request = httpx.Request("GET", url)
        response = httpx.Response(status_code=404, request=request)
        raise httpx.HTTPStatusError("Not Found", request=request, response=response)

    def fake_search(
        query: str,
        *,
        include_domains: tuple[str, ...],
        max_results: int,
        include_answer: bool,
        description: str,
    ) -> str:
        assert query == "lifespan"
        assert include_domains == ("fastapi.tiangolo.com",)
        assert max_results == 3
        assert include_answer is True
        assert "official FastAPI documentation" in description
        return "Use the lifespan parameter with an async context manager."

    monkeypatch.setattr(doc_server_module, "_fetch_llms_txt_content", fake_fetch)
    monkeypatch.setattr(doc_server_module, "search_documentation", fake_search)

    result = await fetch_fastapi_docs("lifespan")

    assert result["resolved_via"] == "official_search_fallback"
    assert result["content"] == "Use the lifespan parameter with an async context manager."


@pytest.mark.asyncio
async def test_fetch_fastapi_docs_accepts_json_string_search_fallback(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The FastAPI docs fallback should parse JSON-string search payloads."""

    async def fake_fetch(url: str) -> str:
        request = httpx.Request("GET", url)
        response = httpx.Response(status_code=404, request=request)
        raise httpx.HTTPStatusError("Not Found", request=request, response=response)

    def fake_search(
        query: str,
        *,
        include_domains: tuple[str, ...],
        max_results: int,
        include_answer: bool,
        description: str,
    ) -> str:
        assert query == "lifespan"
        assert include_domains == ("fastapi.tiangolo.com",)
        assert max_results == 3
        assert include_answer is True
        assert "official FastAPI documentation" in description
        return json.dumps(
            {
                "answer": "Use the lifespan parameter instead of startup/shutdown events.",
                "results": [
                    {
                        "title": "Lifespan Events - FastAPI",
                        "url": "https://fastapi.tiangolo.com/advanced/events/",
                        "content": "Use the lifespan parameter with an async context manager.",
                    }
                ],
            }
        )

    monkeypatch.setattr(doc_server_module, "_fetch_llms_txt_content", fake_fetch)
    monkeypatch.setattr(doc_server_module, "search_documentation", fake_search)

    result = await fetch_fastapi_docs("lifespan")

    assert result["resolved_via"] == "official_search_fallback"
    assert "Lifespan Events - FastAPI" in result["content"]
    assert "Use the lifespan parameter" in result["content"]


def test_health_endpoint_returns_ok_payload() -> None:
    """Health endpoint should answer with the expected payload."""
    with TestClient(app) as client:
        response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "server": "doc-server"}


@pytest.mark.asyncio
async def test_tavily_fallback_tool_is_registered() -> None:
    """The Tavily-backed fallback tool should be registered on the MCP server."""
    tool = await mcp.get_tool("web_search_documentation")

    assert tool is not None


def test_documentation_source_configuration_is_complete() -> None:
    """All expected llms.txt sources and Tavily domains should be configured."""
    assert DOC_SOURCES == {
        "fastapi": "https://fastapi.tiangolo.com/llms.txt",
        "pydantic": "https://docs.pydantic.dev/llms.txt",
        "langchain": "https://docs.langchain.com/llms.txt",
        "langgraph": "https://langchain-ai.github.io/langgraph/llms.txt",
    }
    assert DOCUMENTATION_DOMAINS == [
        "docs.sqlalchemy.org",
        "alembic.sqlalchemy.org",
        "docs.pytest.org",
        "pytest-asyncio.readthedocs.io",
        "docs.python.org",
    ]
