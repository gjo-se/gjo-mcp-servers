"""FastMCP server for generic, provider-agnostic web search.

Exposes the ``web_search_documentation`` tool which is backed by Tavily and
restricted to a curated list of official documentation domains. The server is
intentionally decoupled from ``doc_server`` so that any other MCP server (e.g.
``scraper_server``, ``skills_analyzer_server``) can consume web-search
capabilities without introducing a cross-server dependency.

Provider roadmap:
    - Tavily (implemented) – :mod:`servers.web_search_server.tools.tavily_search`
    - Google (planned)
    - Brave / Perplexity (planned)
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import Final

from fastmcp import FastMCP
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from servers.web_search_server.tools.tavily_search import web_search_documentation
from shared.config import settings
from shared.logging import configure_logging, get_logger

SERVER_NAME: Final[str] = "web-search-server"
MCP_PATH: Final[str] = "/mcp"

logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# Server lifespan
# ---------------------------------------------------------------------------
@asynccontextmanager
async def web_search_lifespan(_: FastMCP):
    """Configure shared logging during web search server lifetime."""
    configure_logging()
    logger.info("Starting %s", SERVER_NAME)
    try:
        yield
    finally:
        logger.info("Stopping %s", SERVER_NAME)


# ---------------------------------------------------------------------------
# MCP server registration
# ---------------------------------------------------------------------------
mcp = FastMCP(
    name=SERVER_NAME,
    instructions=(
        "Generic web search server. Use web_search_documentation to query "
        "official documentation sources when no llms.txt feed is available."
    ),
    lifespan=web_search_lifespan,
)

mcp.tool(
    web_search_documentation,
    name="web_search_documentation",
    description=(
        "Search official documentation domains via Tavily for SQLAlchemy, Alembic, "
        "pytest and related tooling when no llms.txt source exists."
    ),
)


@mcp.custom_route("/health", methods=["GET"], include_in_schema=False)
async def health(_: Request) -> Response:
    """Return a simple health payload for Docker and tests."""
    return JSONResponse({"status": "ok", "server": SERVER_NAME})


app = mcp.http_app(path=MCP_PATH, transport="http")


async def main() -> None:
    """Run the web search server over HTTP."""
    await mcp.run_http_async(
        transport="http",
        host=settings.host,
        port=settings.port_web_search,
        path=MCP_PATH,
        log_level=settings.log_level.lower(),
    )


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())

