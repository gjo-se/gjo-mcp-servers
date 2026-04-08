"""FastMCP server skeleton for the scraper service."""

from contextlib import asynccontextmanager

from fastmcp import FastMCP
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from servers.scraper_server.tools.scrape_freelancermap import scrape_freelancermap
from shared.config import settings
from shared.logging import configure_logging, get_logger

SERVER_NAME = "scraper-server"
MCP_PATH = "/mcp"
logger = get_logger(__name__)


@asynccontextmanager
async def scraper_lifespan(_: FastMCP):
    """Configure logging when the MCP server starts."""
    configure_logging()
    logger.info("Starting %s", SERVER_NAME)
    try:
        yield
    finally:
        logger.info("Stopping %s", SERVER_NAME)


mcp = FastMCP(
    name=SERVER_NAME,
    instructions="Scraper MCP server.",
    lifespan=scraper_lifespan,
)
mcp.tool(
    scrape_freelancermap,
    name="scrape_freelancermap",
    description=(
        "Stub tool for future freelancermap scraping. "
        "Full implementation arrives in T-08."
    ),
)


@mcp.custom_route("/health", methods=["GET"], include_in_schema=False)
async def health(_: Request) -> Response:
    """Return a simple health payload for Docker and tests."""
    return JSONResponse({"status": "ok", "server": SERVER_NAME})


app = mcp.http_app(path=MCP_PATH, transport="http")


async def main() -> None:
    """Run the scraper server over HTTP."""
    await mcp.run_http_async(
        transport="http",
        host=settings.host,
        port=settings.port_scraper,
        path=MCP_PATH,
        log_level=settings.log_level.lower(),
    )


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())


