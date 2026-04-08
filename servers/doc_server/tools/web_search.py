"""Tavily-backed documentation web-search fallback."""

from __future__ import annotations

import os
from typing import Any

from langchain_tavily import TavilySearch

from shared.config import settings

DOCUMENTATION_DOMAINS = [
    "docs.sqlalchemy.org",
    "alembic.sqlalchemy.org",
    "docs.pytest.org",
    "pytest-asyncio.readthedocs.io",
    "docs.python.org",
]


def build_tavily_search_tool() -> TavilySearch:
    """Build the Tavily search tool with a strict documentation domain filter."""
    api_key = settings.tavily_api_key.strip() or os.environ.get(
        "TAVILY_API_KEY",
        "",
    ).strip()
    if not api_key:
        raise ValueError("TAVILY_API_KEY is required for documentation web search")

    os.environ.setdefault("TAVILY_API_KEY", api_key)
    return TavilySearch(
        max_results=3,
        search_depth="basic",
        include_domains=DOCUMENTATION_DOMAINS,
        include_answer=False,
        include_raw_content=False,
        topic="general",
        description=(
            "Search official documentation sources for SQLAlchemy, Alembic, pytest and "
            "related tooling. Use this when no llms.txt source is available."
        ),
    )


def web_search_documentation(query: str, max_results: int = 3) -> dict[str, Any]:
    """Run a Tavily search restricted to official documentation domains.

    Args:
        query: Documentation-focused search query.
        max_results: Maximum number of results to return.

    Returns:
        Tavily response payload.
    """
    if not query.strip():
        raise ValueError("query must not be empty")
    if max_results <= 0:
        raise ValueError("max_results must be greater than 0")

    tavily_tool = build_tavily_search_tool()
    tavily_tool.max_results = max_results
    return tavily_tool.invoke({"query": query})


