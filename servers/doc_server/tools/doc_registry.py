"""Registry: maps package names to their documentation source.

Used by check_doc_sources.py (gjo-se.com) to verify that every installed
dependency has a known MCP documentation source.
"""

from __future__ import annotations

DOC_REGISTRY: dict[str, dict[str, str]] = {
    # llms.txt-Quellen (fetch_*_docs Tools) – Backend
    "fastapi": {"type": "llms_txt", "tool": "fetch_fastapi_docs"},
    "pydantic": {"type": "llms_txt", "tool": "fetch_pydantic_docs"},
    "langchain": {"type": "llms_txt", "tool": "fetch_langchain_docs"},
    "langgraph": {"type": "llms_txt", "tool": "fetch_langgraph_docs"},
    "fastmcp": {"type": "llms_txt", "tool": "fetch_fastmcp_docs"},
    "pycharm": {"type": "llms_txt", "tool": "fetch_pycharm_docs"},
    # web_search-Quellen – Backend
    "sqlalchemy": {"type": "web_search", "domain": "docs.sqlalchemy.org"},
    "alembic": {"type": "web_search", "domain": "alembic.sqlalchemy.org"},
    "pytest": {"type": "web_search", "domain": "docs.pytest.org"},
    "pytest-asyncio": {"type": "web_search", "domain": "pytest-asyncio.readthedocs.io"},
    "httpx": {"type": "web_search", "domain": "www.python-httpx.org"},
    "playwright": {"type": "web_search", "domain": "playwright.dev"},
    "github-copilot": {"type": "web_search", "domain": "docs.github.com"},
    # web_search-Quellen – Frontend
    "react": {"type": "web_search", "domain": "react.dev"},
    "typescript": {"type": "web_search", "domain": "typescriptlang.org"},
    "tailwindcss": {"type": "web_search", "domain": "tailwindcss.com"},
    "vite": {"type": "web_search", "domain": "vitejs.dev"},
    "react-router-dom": {"type": "web_search", "domain": "reactrouter.com"},
}
