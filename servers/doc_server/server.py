"""FastMCP server for current framework documentation access."""

from __future__ import annotations

import json
from contextlib import asynccontextmanager
from typing import Any, Final

import httpx
from fastmcp import FastMCP
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from servers.doc_server.tools.web_search import (
    search_documentation,
    web_search_documentation,
)
from shared.config import settings
from shared.logging import configure_logging, get_logger

SERVER_NAME: Final[str] = "doc-server"
MCP_PATH: Final[str] = "/mcp"
FASTAPI_FALLBACK_DOMAINS: Final[tuple[str, ...]] = ("fastapi.tiangolo.com",)
FASTAPI_FALLBACK_QUERY: Final[str] = "FastAPI official documentation latest guidance"
FASTAPI_FALLBACK_DESCRIPTION: Final[str] = (
    "Search the official FastAPI documentation when llms.txt is unavailable. "
    "Use only official FastAPI docs results."
)
PYDANTIC_FALLBACK_DOMAINS: Final[tuple[str, ...]] = (
    "docs.pydantic.dev",
    "pydantic.dev",
)
PYDANTIC_FALLBACK_QUERY: Final[str] = "Pydantic v2 official documentation latest guidance"
PYDANTIC_FALLBACK_DESCRIPTION: Final[str] = (
    "Search the official Pydantic documentation when llms.txt is unavailable. "
    "Use only official Pydantic docs results."
)
DOC_SOURCES: Final[dict[str, str]] = {
    "fastapi": "https://fastapi.tiangolo.com/llms.txt",
    "pydantic": "https://docs.pydantic.dev/llms.txt",
    "langchain": "https://docs.langchain.com/llms.txt",
    "langgraph": "https://langchain-ai.github.io/langgraph/llms.txt",
}
logger = get_logger(__name__)


@asynccontextmanager
async def doc_lifespan(_: FastMCP):
    """Configure shared logging during doc server lifetime."""
    configure_logging()
    logger.info("Starting %s", SERVER_NAME)
    try:
        yield
    finally:
        logger.info("Stopping %s", SERVER_NAME)


async def _fetch_llms_txt_content(url: str) -> str:
    """Fetch llms.txt content from the configured documentation URL."""
    async with httpx.AsyncClient(timeout=20.0, follow_redirects=True) as client:
        response = await client.get(url)
        response.raise_for_status()
    return response.text


async def _fetch_documentation(source_name: str, query: str = "") -> dict[str, str]:
    """Fetch and optionally filter a configured llms.txt source."""
    url = DOC_SOURCES[source_name]
    content = await _fetch_llms_txt_content(url)
    normalized_query = query.strip().lower()

    if not normalized_query:
        excerpt = content
    else:
        matching_lines = [
            line for line in content.splitlines() if normalized_query in line.lower()
        ]
        excerpt = "\n".join(matching_lines) or content

    return {
        "source": source_name,
        "url": url,
        "content": excerpt,
        "query": query,
    }


def _format_search_results(search_payload: dict[str, Any] | str) -> str:
    """Convert Tavily results into a deterministic text excerpt."""
    if isinstance(search_payload, str):
        normalized_payload = search_payload.strip()
        if not normalized_payload:
            raise ValueError("FastAPI documentation fallback returned no usable results")

        try:
            parsed_payload = json.loads(normalized_payload)
        except json.JSONDecodeError:
            return normalized_payload

        if not isinstance(parsed_payload, dict):
            return normalized_payload

        search_payload = parsed_payload

    sections: list[str] = []

    answer = str(search_payload.get("answer") or "").strip()
    if answer:
        sections.append(f"Answer: {answer}")

    raw_results = search_payload.get("results") or []
    for result in raw_results:
        if not isinstance(result, dict):
            continue

        title = str(result.get("title") or "").strip()
        url = str(result.get("url") or "").strip()
        content = str(result.get("content") or "").strip()
        block_lines = [
            line
            for line in (
                f"Title: {title}" if title else "",
                f"URL: {url}" if url else "",
                content,
            )
            if line
        ]
        if block_lines:
            sections.append("\n".join(block_lines))

    if not sections:
        raise ValueError("FastAPI documentation fallback returned no usable results")

    return "\n\n".join(sections)


def _search_fastapi_documentation(query: str) -> dict[str, str]:
    """Search official FastAPI docs when the llms.txt source is unavailable."""
    search_query = query.strip() or FASTAPI_FALLBACK_QUERY
    search_payload = search_documentation(
        search_query,
        include_domains=FASTAPI_FALLBACK_DOMAINS,
        max_results=3,
        include_answer=True,
        description=FASTAPI_FALLBACK_DESCRIPTION,
    )
    return {
        "source": "fastapi",
        "url": DOC_SOURCES["fastapi"],
        "content": _format_search_results(search_payload),
        "query": query,
        "resolved_via": "official_search_fallback",
        "fallback_url": "https://fastapi.tiangolo.com/",
    }


def _search_pydantic_documentation(query: str) -> dict[str, str]:
    """Search official Pydantic docs when the llms.txt source is unavailable."""
    search_query = query.strip() or PYDANTIC_FALLBACK_QUERY
    search_payload = search_documentation(
        search_query,
        include_domains=PYDANTIC_FALLBACK_DOMAINS,
        max_results=3,
        include_answer=True,
        description=PYDANTIC_FALLBACK_DESCRIPTION,
    )
    return {
        "source": "pydantic",
        "url": DOC_SOURCES["pydantic"],
        "content": _format_search_results(search_payload),
        "query": query,
        "resolved_via": "official_search_fallback",
        "fallback_url": "https://docs.pydantic.dev/",
    }


async def fetch_fastapi_docs(query: str = "") -> dict[str, str]:
    """Fetch current FastAPI docs from official sources.

    The server prefers llms.txt, but falls back to an official-domain search when the
    llms.txt endpoint is unavailable.
    """
    try:
        return await _fetch_documentation("fastapi", query)
    except httpx.HTTPStatusError as exc:
        response = exc.response
        if response is None or response.status_code != httpx.codes.NOT_FOUND:
            raise

        result = _search_fastapi_documentation(query)
        result["fallback_reason"] = f"{response.status_code} at {DOC_SOURCES['fastapi']}"
        return result


async def fetch_pydantic_docs(query: str = "") -> dict[str, str]:
    """Fetch current Pydantic docs via llms.txt with Tavily fallback.

    MUST be used for Pydantic questions because training data may be outdated.
    Falls back to an official-domain Tavily search when llms.txt is unavailable.
    """
    try:
        return await _fetch_documentation("pydantic", query)
    except (httpx.HTTPStatusError, httpx.HTTPError) as exc:
        status_code: int | None = None
        if isinstance(exc, httpx.HTTPStatusError):
            status_code = exc.response.status_code if exc.response is not None else None

        result = _search_pydantic_documentation(query)
        reason = (
            f"{status_code} at {DOC_SOURCES['pydantic']}"
            if status_code is not None
            else f"HTTP error at {DOC_SOURCES['pydantic']}: {exc}"
        )
        result["fallback_reason"] = reason
        return result


async def fetch_langchain_docs(query: str = "") -> dict[str, str]:
    """Fetch current LangChain docs via llms.txt.

    MUST be used for LangChain questions because training data may be outdated.
    """
    return await _fetch_documentation("langchain", query)


async def fetch_langgraph_docs(query: str = "") -> dict[str, str]:
    """Fetch current LangGraph docs via llms.txt.

    MUST be used for LangGraph questions because training data may be outdated.
    """
    return await _fetch_documentation("langgraph", query)


mcp = FastMCP(
    name=SERVER_NAME,
    instructions=(
        "Documentation MCP server with llms.txt sources and Tavily fallback. "
        "Use this server for framework questions that require current docs."
    ),
    lifespan=doc_lifespan,
)
mcp.tool(
    fetch_fastapi_docs,
    name="fetch_fastapi_docs",
    description=(
        "Fetch current FastAPI documentation from official sources. Prefer llms.txt "
        "and fall back to official FastAPI documentation search when needed. MUST be "
        "used for FastAPI questions because training data may be outdated."
    ),
)
mcp.tool(
    fetch_pydantic_docs,
    name="fetch_pydantic_docs",
    description=(
        "Fetch current Pydantic documentation from llms.txt. MUST be used for Pydantic "
        "questions because training data may be outdated."
    ),
)
mcp.tool(
    fetch_langchain_docs,
    name="fetch_langchain_docs",
    description=(
        "Fetch current LangChain documentation from llms.txt. "
        "MUST be used for LangChain "
        "questions because training data may be outdated."
    ),
)
mcp.tool(
    fetch_langgraph_docs,
    name="fetch_langgraph_docs",
    description=(
        "Fetch current LangGraph documentation from llms.txt. "
        "MUST be used for LangGraph "
        "questions because training data may be outdated."
    ),
)
mcp.tool(
    web_search_documentation,
    name="web_search_documentation",
    description=(
        "Search official documentation domains via Tavily for SQLAlchemy, "
        "Alembic, pytest "
        "and related tooling when no llms.txt source exists."
    ),
)


@mcp.custom_route("/health", methods=["GET"], include_in_schema=False)
async def health(_: Request) -> Response:
    """Return a simple health payload for Docker and tests."""
    return JSONResponse({"status": "ok", "server": SERVER_NAME})


app = mcp.http_app(path=MCP_PATH, transport="http")


async def main() -> None:
    """Run the doc server over HTTP."""
    await mcp.run_http_async(
        transport="http",
        host=settings.host,
        port=settings.port_doc,
        path=MCP_PATH,
        log_level=settings.log_level.lower(),
    )


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
