"""Tavily-backed web search provider with domain filter support.

This module is the authoritative implementation of the Tavily search provider
for the ``web_search_server``. It exposes a provider-agnostic interface so that
additional providers (Google, Brave, Perplexity …) can be added later without
changing the tool contract.

Note:
    ``DOCUMENTATION_DOMAINS`` contains the default allow-list used by
    ``web_search_documentation``. Callers that need a custom domain list should
    use ``search_documentation`` directly and pass ``include_domains`` explicitly.
"""

from __future__ import annotations

import os
from collections.abc import Sequence
from typing import Any

from langchain_tavily import TavilySearch

from shared.config import settings

DOCUMENTATION_DOMAINS: list[str] = [
    # Backend – SQLAlchemy / Alembic / pytest ecosystem
    "docs.sqlalchemy.org",
    "alembic.sqlalchemy.org",
    "docs.pytest.org",
    "pytest-asyncio.readthedocs.io",
    "docs.python.org",
    # Backend – HTTP / Playwright / GitHub
    "www.python-httpx.org",
    "playwright.dev",
    "docs.github.com",
    # Frontend – React / TypeScript / Tooling
    "react.dev",
    "typescriptlang.org",
    "tailwindcss.com",
    "vitejs.dev",
    "reactrouter.com",
]

DEFAULT_MAX_RESULTS: int = 3
DEFAULT_DESCRIPTION: str = (
    "Search official documentation sources for SQLAlchemy, Alembic, pytest and "
    "related tooling. Use this when no llms.txt source is available."
)


def _resolve_tavily_api_key() -> str:
    """Return the configured Tavily API key.

    Raises:
        ValueError: When no API key is available in settings or environment.
    """
    api_key = (
        settings.tavily_api_key.strip() or os.environ.get("TAVILY_API_KEY", "").strip()
    )
    if not api_key:
        raise ValueError("TAVILY_API_KEY is required for web search")
    return api_key


def build_tavily_search_tool(
    *,
    include_domains: Sequence[str] | None = None,
    max_results: int = DEFAULT_MAX_RESULTS,
    include_answer: bool = False,
    description: str = DEFAULT_DESCRIPTION,
) -> TavilySearch:
    """Build a Tavily search tool restricted to the provided domain allow-list.

    Args:
        include_domains: Domains to restrict results to. Defaults to
            ``DOCUMENTATION_DOMAINS`` when *None*.
        max_results: Maximum number of search results to return.
        include_answer: Whether to request a synthesised answer from Tavily.
        description: Human-readable description forwarded to the LangChain tool.

    Returns:
        Configured :class:`TavilySearch` instance.

    Raises:
        ValueError: When *max_results* is not positive or *include_domains* is empty.
    """
    if max_results <= 0:
        raise ValueError("max_results must be greater than 0")

    if include_domains is not None and len(include_domains) == 0:
        raise ValueError("include_domains must not be empty")

    resolved = include_domains if include_domains is not None else DOCUMENTATION_DOMAINS
    domains = list(resolved)

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


def _normalize_tavily_response(raw: Any, query: str) -> dict[str, Any]:
    """Normalize a Tavily response to always return a dict.

    Tavily occasionally returns a plain string (e.g. "No search results found …")
    instead of a structured dict when no results are available.  FastMCP requires
    tool return values to be dicts, so this helper wraps any non-dict payload into
    a canonical ``{"query": …, "results": [], "message": …}`` structure.

    Args:
        raw: The raw value returned by :meth:`TavilySearch.invoke`.
        query: The original search query (used to populate the ``query`` field).

    Returns:
        Always a dict – either the original Tavily payload or a normalised wrapper.
    """
    if isinstance(raw, dict):
        return raw
    message = str(raw).strip() if raw is not None else "No results returned by Tavily."
    return {
        "query": query,
        "results": [],
        "answer": None,
        "message": message,
    }


def search_documentation(
    query: str,
    *,
    include_domains: Sequence[str],
    max_results: int = DEFAULT_MAX_RESULTS,
    include_answer: bool = False,
    description: str = DEFAULT_DESCRIPTION,
) -> dict[str, Any]:
    """Run a Tavily search restricted to the provided documentation domains.

    Args:
        query: Search query string.
        include_domains: Domain allow-list for the search.
        max_results: Maximum number of results to return.
        include_answer: Whether to request a synthesised answer from Tavily.
        description: Human-readable description forwarded to the LangChain tool.

    Returns:
        Tavily response payload as a dict.  Always a dict, even when Tavily
        returns no results or a plain-text message.

    Raises:
        ValueError: When *query* is blank.
    """
    if not query.strip():
        raise ValueError("query must not be empty")

    tavily_tool = build_tavily_search_tool(
        include_domains=include_domains,
        max_results=max_results,
        include_answer=include_answer,
        description=description,
    )
    raw = tavily_tool.invoke({"query": query})
    return _normalize_tavily_response(raw, query)


def web_search_documentation(
    query: str,
    max_results: int = DEFAULT_MAX_RESULTS,
) -> dict[str, Any]:
    """Run a Tavily search restricted to official documentation domains.

    This is the primary MCP tool exposed by the ``web_search_server``.

    Args:
        query: Documentation-focused search query.
        max_results: Maximum number of results to return.

    Returns:
        Tavily response payload as a dict.

    Raises:
        ValueError: When *query* is blank or *max_results* is not positive.
    """
    return search_documentation(
        query,
        include_domains=DOCUMENTATION_DOMAINS,
        max_results=max_results,
        include_answer=False,
        description=DEFAULT_DESCRIPTION,
    )
