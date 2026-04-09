"""FastMCP server for current framework documentation access."""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import Final

import httpx
from fastmcp import FastMCP
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from servers.doc_server.tools.web_search import web_search_documentation
from shared.config import settings
from shared.logging import configure_logging, get_logger

SERVER_NAME: Final[str] = "doc-server"
MCP_PATH: Final[str] = "/mcp"
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
    async with httpx.AsyncClient(timeout=20.0) as client:
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


async def fetch_fastapi_docs(query: str = "") -> dict[str, str]:
    """Fetch current FastAPI docs via llms.txt.

    MUST be used for FastAPI questions because training data may be outdated.
    """
    return await _fetch_documentation("fastapi", query)


async def fetch_pydantic_docs(query: str = "") -> dict[str, str]:
    """Fetch current Pydantic docs via llms.txt.

    MUST be used for Pydantic questions because training data may be outdated.
    """
    return await _fetch_documentation("pydantic", query)


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
        "Fetch current FastAPI documentation from llms.txt. MUST be used for FastAPI "
        "questions because training data may be outdated."
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
