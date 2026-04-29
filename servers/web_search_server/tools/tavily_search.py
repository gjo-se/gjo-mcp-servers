"""Tavily-backed web search provider with domain filter support.

This module is the authoritative implementation of the Tavily search provider
for the ``web_search_server``. It exposes a provider-agnostic interface so that
additional providers (Google, Brave, Perplexity …) can be added later without
changing the tool contract.

Note:
    ``DOCUMENTATION_DOMAINS`` contains the default allow-list used by
    ``web_search_documentation``. Pass ``NO_DOMAIN_FILTER`` (empty list) to
    ``build_tavily_search_tool`` to run an unrestricted global search.
"""

from __future__ import annotations

import os
from collections.abc import Sequence
from typing import Any, Literal

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
    # Backend – LangChain OSS Python / tenacity
    "python.langchain.com",
    "tenacity.readthedocs.io",
    # Frontend – React / TypeScript / Tooling
    "react.dev",
    "typescriptlang.org",
    "tailwindcss.com",
    "vitejs.dev",
    "reactrouter.com",
    # Frontend – Charts
    "recharts.org",
    # Frontend – Syncfusion
    "ej2.syncfusion.com",
]

DEFAULT_MAX_RESULTS: int = 3

# Sentinel: pass to build_tavily_search_tool to disable domain filtering.
NO_DOMAIN_FILTER: list[str] = []

# Isolated domain list for Syncfusion EJ2 queries.
# Tavily's include_domains filter does not reliably surface ej2.syncfusion.com
# when mixed with a large multi-domain allow-list.  Routing Syncfusion-specific
# queries through this single-entry list restores reliable results.
SYNCFUSION_DOMAINS: list[str] = ["ej2.syncfusion.com"]

# Keywords that indicate a query targets Syncfusion EJ2 documentation.
SYNCFUSION_KEYWORDS: frozenset[str] = frozenset(
    {
        "syncfusion",
        "@syncfusion",
        "ej2-react",
        "ej2-grids",
        "ej2-charts",
        "columndirective",
        "columnsdirective",
        "gridcomponent",
        "chartcomponent",
    }
)

DEFAULT_DESCRIPTION: str = (
    "Search official documentation sources for SQLAlchemy, Alembic, pytest, "
    "React, TypeScript, Tailwind CSS, Vite, React Router, Syncfusion EJ2 and "
    "related tooling. Use this when no llms.txt source is available."
)

GENERIC_DESCRIPTION: str = (
    "Generic web search without domain restrictions. "
    "Use for general research, news, blog posts, and topics "
    "not covered by official documentation."
)


def _is_syncfusion_query(query: str) -> bool:
    """Return True when the query targets Syncfusion EJ2 documentation.

    Checks for case-insensitive occurrence of any keyword in
    :data:`SYNCFUSION_KEYWORDS` within *query*.

    Args:
        query: The raw search query string.

    Returns:
        ``True`` if the query is Syncfusion-specific, ``False`` otherwise.
    """
    lower = query.lower()
    return any(keyword in lower for keyword in SYNCFUSION_KEYWORDS)


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
    search_depth: Literal["basic", "advanced"] = "basic",
    topic: Literal["general", "news", "finance"] = "general",
) -> TavilySearch:
    """Build a configured Tavily search tool.

    Domain filter behaviour:

    * ``None`` (default) → restrict to ``DOCUMENTATION_DOMAINS``
    * ``[]`` / ``NO_DOMAIN_FILTER`` → no domain filter (global search)
    * non-empty list → restrict to the provided domains

    Args:
        include_domains: Domain allow-list.  See above for sentinel semantics.
        max_results: Maximum number of search results to return.
        include_answer: Whether to request a synthesised answer from Tavily.
        description: Human-readable description forwarded to the LangChain tool.
        search_depth: ``"basic"`` for speed, ``"advanced"`` for depth.
        topic: Tavily topic context – ``"general"``, ``"news"`` or ``"finance"``.

    Returns:
        Configured :class:`TavilySearch` instance.

    Raises:
        ValueError: When *max_results* is not positive.
    """
    if max_results <= 0:
        raise ValueError("max_results must be greater than 0")

    if include_domains is None:
        # Default: restrict to documentation domains
        domains: list[str] | None = DOCUMENTATION_DOMAINS
    elif len(include_domains) == 0:
        # Sentinel NO_DOMAIN_FILTER: no restriction
        domains = None
    else:
        domains = list(include_domains)

    os.environ.setdefault("TAVILY_API_KEY", _resolve_tavily_api_key())
    return TavilySearch(
        max_results=max_results,
        search_depth=search_depth,
        include_domains=domains,
        include_answer=include_answer,
        include_raw_content=False,
        topic=topic,
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

    Syncfusion EJ2 routing:
        Queries that match :func:`_is_syncfusion_query` are routed through an
        isolated ``["ej2.syncfusion.com"]`` domain filter.  Tavily does not
        reliably surface ``ej2.syncfusion.com`` when it is included in a large
        multi-domain allow-list, so the isolated filter restores reliable results
        without changing the external tool contract.

    Args:
        query: Documentation-focused search query.
        max_results: Maximum number of results to return.

    Returns:
        Tavily response payload as a dict.

    Raises:
        ValueError: When *query* is blank or *max_results* is not positive.
    """
    domains = (
        SYNCFUSION_DOMAINS if _is_syncfusion_query(query) else DOCUMENTATION_DOMAINS
    )
    return search_documentation(
        query,
        include_domains=domains,
        max_results=max_results,
        include_answer=False,
        description=DEFAULT_DESCRIPTION,
    )


def web_search(
    query: str,
    max_results: int = DEFAULT_MAX_RESULTS,
    search_depth: Literal["basic", "advanced"] = "basic",
    topic: Literal["general", "news", "finance"] = "general",
) -> dict[str, Any]:
    """Run an unrestricted Tavily web search for general research.

    Unlike ``web_search_documentation`` this tool applies no domain filter,
    making it suitable for news, blog posts, and topics not covered by
    official documentation sources.

    Args:
        query: Search query string.
        max_results: Maximum number of results to return.
        search_depth: ``"basic"`` for fast results, ``"advanced"`` for deeper
            analysis.
        topic: Search topic context – ``"general"``, ``"news"`` or
            ``"finance"``.

    Returns:
        Tavily response payload as a dict.

    Raises:
        ValueError: When *query* is blank or *max_results* is not positive.
    """
    if not query.strip():
        raise ValueError("query must not be empty")
    if max_results <= 0:
        raise ValueError("max_results must be greater than 0")

    tavily_tool = build_tavily_search_tool(
        include_domains=NO_DOMAIN_FILTER,
        max_results=max_results,
        include_answer=False,
        description=GENERIC_DESCRIPTION,
        search_depth=search_depth,
        topic=topic,
    )
    raw = tavily_tool.invoke({"query": query})
    return _normalize_tavily_response(raw, query)
