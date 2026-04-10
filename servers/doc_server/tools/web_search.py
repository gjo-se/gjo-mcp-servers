"""Tavily-backed documentation web-search fallback."""

from __future__ import annotations

import os
from typing import Any, Sequence

from langchain_tavily import TavilySearch

from shared.config import settings

DOCUMENTATION_DOMAINS = [
    "docs.sqlalchemy.org",
    "alembic.sqlalchemy.org",
    "docs.pytest.org",
    "pytest-asyncio.readthedocs.io",
    "docs.python.org",
]
DEFAULT_MAX_RESULTS = 3
DEFAULT_DESCRIPTION = (
    "Search official documentation sources for SQLAlchemy, Alembic, pytest and "
    "related tooling. Use this when no llms.txt source is available."
)


def _resolve_tavily_api_key() -> str:
    """Return the configured Tavily API key."""
    api_key = (
        settings.tavily_api_key.strip()
        or os.environ.get(
            "TAVILY_API_KEY",
            "",
        ).strip()
    )
    if not api_key:
        raise ValueError("TAVILY_API_KEY is required for documentation web search")

    return api_key


def build_tavily_search_tool(
    *,
    include_domains: Sequence[str] | None = None,
    max_results: int = DEFAULT_MAX_RESULTS,
    include_answer: bool = False,
    description: str = DEFAULT_DESCRIPTION,
) -> TavilySearch:
    """Build the Tavily search tool with a strict documentation domain filter."""
    if max_results <= 0:
        raise ValueError("max_results must be greater than 0")

    domains = list(include_domains or DOCUMENTATION_DOMAINS)
    if not domains:
        raise ValueError("include_domains must not be empty")

    os.environ.setdefault("TAVILY_API_KEY", _resolve_tavily_api_key())
    return TavilySearch(
        max_results=max_results,
        search_depth="basic",
        include_domains=domains,
        include_answer=include_answer,
        include_raw_content=False,
        topic="general",
        description=description,
    )


def search_documentation(
    query: str,
    *,
    include_domains: Sequence[str],
    max_results: int = DEFAULT_MAX_RESULTS,
    include_answer: bool = False,
    description: str = DEFAULT_DESCRIPTION,
) -> dict[str, Any]:
    """Run a Tavily search restricted to the provided documentation domains."""
    if not query.strip():
        raise ValueError("query must not be empty")

    tavily_tool = build_tavily_search_tool(
        include_domains=include_domains,
        max_results=max_results,
        include_answer=include_answer,
        description=description,
    )
    return tavily_tool.invoke({"query": query})


def web_search_documentation(
    query: str,
    max_results: int = DEFAULT_MAX_RESULTS,
) -> dict[str, Any]:
    """Run a Tavily search restricted to official documentation domains.

    Args:
        query: Documentation-focused search query.
        max_results: Maximum number of results to return.

    Returns:
        Tavily response payload.
    """
    return search_documentation(
        query,
        include_domains=DOCUMENTATION_DOMAINS,
        max_results=max_results,
        include_answer=False,
        description=DEFAULT_DESCRIPTION,
    )
