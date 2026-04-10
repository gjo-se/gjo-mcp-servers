"""Unit tests for the doc_server."""

import json

import httpx
import pytest
from starlette.testclient import TestClient

import servers.doc_server.server as doc_server_module
from servers.doc_server.server import (
    DOC_SOURCES,
    app,
    fetch_fastapi_docs,
    fetch_langchain_docs,
    fetch_langgraph_docs,
    fetch_pydantic_docs,
    mcp,
)
from servers.doc_server.tools.web_search import (
    DOCUMENTATION_DOMAINS,
    web_search_documentation,
)


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


@pytest.mark.asyncio
async def test_fetch_pydantic_docs_falls_back_to_official_search(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The Pydantic docs tool should fall back to official-domain search on HTTP errors."""

    async def fake_fetch(url: str) -> str:
        request = httpx.Request("GET", url)
        response = httpx.Response(status_code=301, request=request)
        raise httpx.HTTPStatusError("Moved Permanently", request=request, response=response)

    def fake_search(
        query: str,
        *,
        include_domains: tuple[str, ...],
        max_results: int,
        include_answer: bool,
        description: str,
    ) -> dict[str, object]:
        assert "model_validate" in query or query  # query forwarded
        assert "docs.pydantic.dev" in include_domains or "pydantic.dev" in include_domains
        assert max_results == 3
        assert include_answer is True
        assert "Pydantic" in description
        return {
            "answer": "model_validate creates a model instance from data; model_dump serializes it.",
            "results": [
                {
                    "title": "Validators - Pydantic",
                    "url": "https://docs.pydantic.dev/latest/concepts/validators/",
                    "content": "Use model_validate to create a model from dict or object.",
                }
            ],
        }

    monkeypatch.setattr(doc_server_module, "_fetch_llms_txt_content", fake_fetch)
    monkeypatch.setattr(doc_server_module, "search_documentation", fake_search)

    result = await fetch_pydantic_docs("model_validate model_dump")

    assert result["source"] == "pydantic"
    assert result["url"] == DOC_SOURCES["pydantic"]
    assert result["resolved_via"] == "official_search_fallback"
    assert "fallback_reason" in result
    assert "Validators - Pydantic" in result["content"]
    assert "model_validate" in result["content"]


@pytest.mark.asyncio
async def test_fetch_pydantic_docs_uses_configured_source(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The Pydantic docs tool should use the configured llms.txt source when available."""

    async def fake_fetch(url: str) -> str:
        assert url == DOC_SOURCES["pydantic"]
        return "Pydantic v2 current docs\nmodel_validate anchor"

    monkeypatch.setattr(doc_server_module, "_fetch_llms_txt_content", fake_fetch)

    result = await fetch_pydantic_docs("model_validate")

    assert result["source"] == "pydantic"
    assert result["url"] == DOC_SOURCES["pydantic"]
    assert result["content"] == "model_validate anchor"


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


def test_web_search_documentation_returns_results(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """web_search_documentation should forward the query and return Tavily results."""
    import servers.doc_server.tools.web_search as web_search_module

    def fake_invoke(self: object, payload: dict[str, str]) -> dict[str, object]:
        assert payload["query"] == "SQLAlchemy 2.x async_sessionmaker"
        return {
            "results": [
                {
                    "title": "Asynchronous I/O — SQLAlchemy 2.1 Documentation",
                    "url": "https://docs.sqlalchemy.org/en/latest/orm/extensions/asyncio.html",
                    "content": "Use async_sessionmaker to create async sessions.",
                }
            ]
        }

    monkeypatch.setattr(
        web_search_module.TavilySearch,
        "invoke",
        fake_invoke,
    )

    result = web_search_documentation("SQLAlchemy 2.x async_sessionmaker")

    assert "results" in result
    assert result["results"][0]["title"] == "Asynchronous I/O — SQLAlchemy 2.1 Documentation"


def test_web_search_documentation_filters_to_configured_domains(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """web_search_documentation must only search within DOCUMENTATION_DOMAINS."""
    import servers.doc_server.tools.web_search as web_search_module

    captured_domains: list[list[str]] = []

    original_build = web_search_module.build_tavily_search_tool

    def fake_build(**kwargs: object) -> object:
        captured_domains.append(list(kwargs.get("include_domains", [])))
        return original_build(**kwargs)

    def fake_invoke(self: object, payload: dict[str, str]) -> dict[str, object]:
        return {"results": []}

    monkeypatch.setattr(web_search_module, "build_tavily_search_tool", fake_build)
    monkeypatch.setattr(web_search_module.TavilySearch, "invoke", fake_invoke)

    web_search_documentation("Alembic 1.x autogenerate async")

    assert len(captured_domains) == 1
    assert captured_domains[0] == DOCUMENTATION_DOMAINS


def test_web_search_documentation_raises_on_empty_query() -> None:
    """web_search_documentation should raise ValueError for blank queries."""
    import pytest as _pytest

    with _pytest.raises(ValueError, match="query must not be empty"):
        web_search_documentation("   ")


@pytest.mark.asyncio
async def test_fetch_langchain_docs_uses_configured_source(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The LangChain docs tool should use the configured llms.txt source."""

    async def fake_fetch(url: str) -> str:
        assert url == DOC_SOURCES["langchain"]
        return "LangChain current docs\nstructured output anchor"

    monkeypatch.setattr(doc_server_module, "_fetch_llms_txt_content", fake_fetch)

    result = await fetch_langchain_docs("structured output")

    assert result["source"] == "langchain"
    assert result["url"] == DOC_SOURCES["langchain"]
    assert result["content"] == "structured output anchor"


@pytest.mark.asyncio
async def test_fetch_langchain_docs_returns_full_content_without_query(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The LangChain docs tool should return full content when no query is given."""

    async def fake_fetch(url: str) -> str:
        return "LangChain full docs content"

    monkeypatch.setattr(doc_server_module, "_fetch_llms_txt_content", fake_fetch)

    result = await fetch_langchain_docs()

    assert result["source"] == "langchain"
    assert result["content"] == "LangChain full docs content"


@pytest.mark.asyncio
async def test_fetch_langgraph_docs_uses_configured_source(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The LangGraph docs tool should use the configured llms.txt source."""

    async def fake_fetch(url: str) -> str:
        assert url == DOC_SOURCES["langgraph"]
        return "LangGraph current docs\nStateGraph anchor"

    monkeypatch.setattr(doc_server_module, "_fetch_llms_txt_content", fake_fetch)

    result = await fetch_langgraph_docs("StateGraph")

    assert result["source"] == "langgraph"
    assert result["url"] == DOC_SOURCES["langgraph"]
    assert result["content"] == "StateGraph anchor"


@pytest.mark.asyncio
async def test_fetch_langgraph_docs_returns_full_content_without_query(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The LangGraph docs tool should return full content when no query is given."""

    async def fake_fetch(url: str) -> str:
        return "LangGraph full docs content"

    monkeypatch.setattr(doc_server_module, "_fetch_llms_txt_content", fake_fetch)

    result = await fetch_langgraph_docs()

    assert result["source"] == "langgraph"
    assert result["content"] == "LangGraph full docs content"


def test_documentation_source_configuration_is_complete() -> None:
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
