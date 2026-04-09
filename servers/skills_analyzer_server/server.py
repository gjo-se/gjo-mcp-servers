"""FastMCP server for skill normalization and frequency analysis."""

from contextlib import asynccontextmanager

from fastmcp import FastMCP
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from servers.skills_analyzer_server.tools.analyze_frequency import analyze_frequency
from servers.skills_analyzer_server.tools.normalize_skills import normalize_skills
from shared.config import settings
from shared.logging import configure_logging, get_logger

SERVER_NAME = "skills-analyzer-server"
MCP_PATH = "/mcp"
logger = get_logger(__name__)


@asynccontextmanager
async def analyzer_lifespan(_: FastMCP):
    """Configure shared logging during analyzer server lifetime."""
    configure_logging()
    logger.info("Starting %s", SERVER_NAME)
    try:
        yield
    finally:
        logger.info("Stopping %s", SERVER_NAME)


mcp = FastMCP(
    name=SERVER_NAME,
    instructions="Skill normalization and frequency analysis MCP server.",
    lifespan=analyzer_lifespan,
)
mcp.tool(
    normalize_skills,
    name="normalize_skills",
    description="Normalize raw skill labels into deterministic canonical names.",
)
mcp.tool(
    analyze_frequency,
    name="analyze_frequency",
    description="Count and sort normalized skills by frequency.",
)


@mcp.custom_route("/health", methods=["GET"], include_in_schema=False)
async def health(_: Request) -> Response:
    """Return a simple health payload for Docker and tests."""
    return JSONResponse({"status": "ok", "server": SERVER_NAME})


app = mcp.http_app(path=MCP_PATH, transport="http")


async def main() -> None:
    """Run the analyzer server over HTTP."""
    await mcp.run_http_async(
        transport="http",
        host=settings.host,
        port=settings.port_analyzer,
        path=MCP_PATH,
        log_level=settings.log_level.lower(),
    )


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
