"""Unit tests for the doc_server."""

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
