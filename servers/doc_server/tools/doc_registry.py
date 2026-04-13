"""Registry: maps package names to their documentation source.

Used by check_doc_sources.py (gjo-se.com) to verify that every installed
dependency has a known MCP documentation source.

Scoped-Package-Strategie
------------------------
Scoped npm packages (``@scope/pkg``) werden exakt unter ihrem npm-Namen als
Registry-Key geführt – nach Lowercasing, ohne Normalisierung der Slash-Trennung.
Der Consumer ``normalize_package_name`` in ``check_doc_sources.py`` behält
Scoped-Packages nach Lowercasing und Underscore→Hyphen-Ersetzung unverändert,
sodass ``@syncfusion/ej2-base`` sowohl im Paketmanager als auch im Registry-Key
identisch ist. Keine zusätzliche Abstraktion oder Alias-Schicht ist nötig.
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
    # web_search-Quellen – Syncfusion (Scoped npm packages, exakter npm-Name als Key)
    "@syncfusion/ej2-base": {"type": "web_search", "domain": "ej2.syncfusion.com"},
    "@syncfusion/ej2-react-grids": {
        "type": "web_search",
        "domain": "ej2.syncfusion.com",
    },
    "@syncfusion/ej2-react-charts": {
        "type": "web_search",
        "domain": "ej2.syncfusion.com",
    },
}
