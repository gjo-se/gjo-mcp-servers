"""FastMCP server skeleton for persistence and migrations."""

from contextlib import asynccontextmanager

from fastmcp import FastMCP
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from servers.storage_server.tools.query_top_skills import query_top_skills
from servers.storage_server.tools.save_layout_snapshot import save_layout_snapshot
from servers.storage_server.tools.save_skill_frequency import save_skill_frequency
from shared.config import settings
from shared.logging import configure_logging, get_logger

SERVER_NAME = "storage-server"
MCP_PATH = "/mcp"
logger = get_logger(__name__)


@asynccontextmanager
async def storage_lifespan(_: FastMCP):
    """Configure shared logging during storage server lifetime."""
    configure_logging()
    logger.info("Starting %s", SERVER_NAME)
    try:
        yield
    finally:
        logger.info("Stopping %s", SERVER_NAME)


mcp = FastMCP(
    name=SERVER_NAME,
    instructions="Storage MCP server with SQLAlchemy persistence foundation.",
    lifespan=storage_lifespan,
)
mcp.tool(
    save_skill_frequency,
    name="save_skill_frequency",
    description="Create or update persisted skill frequency entries.",
)
mcp.tool(
    query_top_skills,
    name="query_top_skills",
    description="Return top skills ordered by persisted frequency.",
)
mcp.tool(
    save_layout_snapshot,
    name="save_layout_snapshot",
    description="Persist layout snapshots for scraper recovery workflows.",
)


@mcp.custom_route("/health", methods=["GET"], include_in_schema=False)
async def health(_: Request) -> Response:
    """Return a simple health payload for Docker and tests."""
    return JSONResponse({"status": "ok", "server": SERVER_NAME})


app = mcp.http_app(path=MCP_PATH, transport="http")


async def main() -> None:
    """Run the storage server over HTTP."""
    await mcp.run_http_async(
        transport="http",
        host=settings.host,
        port=settings.port_storage,
        path=MCP_PATH,
        log_level=settings.log_level.lower(),
    )


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
