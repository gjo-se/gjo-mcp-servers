# MCP Server Blueprint – `gjo-mcp-servers`

> Kanonische Referenz für Aufbau, Struktur und Konventionen aller MCP-Server
> in diesem Repo. Dient als Vorlage beim Anlegen neuer Server.

---

## 1. Repo-Struktur auf einen Blick

```
gjo-mcp-servers/
├── shared/                    ← gemeinsam genutzte Infrastruktur
│   ├── config.py              ← Pydantic Settings (Ports, API-Keys, DB-URL)
│   ├── logging.py             ← Root-Logger-Setup
│   ├── db/                    ← SQLAlchemy Session + Engine (nur für storage_server)
│   └── models/                ← ORM-Modelle (nur für storage_server)
│
├── servers/
│   ├── __init__.py
│   ├── <name>_server/
│   │   ├── __init__.py
│   │   ├── server.py          ← FastMCP-Instanz, Tool-Registrierung, Health, main()
│   │   └── tools/
│   │       ├── __init__.py
│   │       └── <tool>.py      ← je eine Funktion pro Tool-Datei
│   └── ...
│
├── tests/
│   ├── unit/
│   │   └── test_<name>_server.py
│   └── integration/           ← echte DB / Netz nötig, per Default übersprungen
│
├── docker-compose.yml         ← alle Services (default opt-in via Profile)
├── docker-compose.override.yml ← aktuelle Default-Services (kein Profil nötig)
├── .mcp.json                  ← MCP-Client-Konfiguration (symlinked zu Copilot)
└── .env.example
```

---

## 2. Shared-Layer

### `shared/config.py`

Zentrale Konfiguration via Pydantic `BaseSettings`. Liest aus `.env` und
Umgebungsvariablen. Alle Server nutzen dieselbe Instanz `settings`.

```python
from shared.config import settings

await mcp.run_http_async(port=settings.port_doc, ...)
```

Relevante Felder:

| Feld | Default | Zweck |
|---|---|---|
| `host` | `0.0.0.0` | Bind-Adresse |
| `port_doc` | `8004` | doc_server |
| `port_web_search` | `8006` | web_search_server |
| `port_scraper` | `8001` | scraper_server |
| `port_analyzer` | `8002` | skills_analyzer_server |
| `port_storage` | `8003` | storage_server |
| `tavily_api_key` | `""` | Tavily-Suche |
| `log_level` | `"INFO"` | Logging |
| `database_url` | postgresql+asyncpg://… | nur storage_server |

**Neuen Port eintragen:** Feld in `Settings` ergänzen + Wert in `.env.example`.

### `shared/logging.py`

```python
from shared.logging import configure_logging, get_logger

logger = get_logger(__name__)
# Im Lifespan: configure_logging()
```

---

## 3. Anatomy eines Servers

Alle Server folgen demselben Muster. Einzige Variante: `storage_server` hat
zusätzlich DB-abhängige Tools – dazu Abschnitt 4.

### 3.1 Dateiliste (Standard, ohne DB)

```
servers/web_search_server/
├── __init__.py          ← leer oder ein Satz
├── server.py            ← FastMCP, Lifespan, Tool-Registrierung, Health, main()
└── tools/
    ├── __init__.py      ← leer oder ein Satz
    └── tavily_search.py ← Tool-Funktion(en), Hilfsfunktionen, Konstanten
```

### 3.2 `server.py` – vollständige Struktur

```python
"""FastMCP server for <kurze Beschreibung>."""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import Final

from fastmcp import FastMCP
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from servers.<name>_server.tools.<module> import <tool_function>
from shared.config import settings
from shared.logging import configure_logging, get_logger

SERVER_NAME: Final[str] = "<name>-server"    # muss mit /health-Payload übereinstimmen
MCP_PATH: Final[str] = "/mcp"

logger = get_logger(__name__)


@asynccontextmanager
async def <name>_lifespan(_: FastMCP):
    """Configure shared logging during <name> server lifetime."""
    configure_logging()
    logger.info("Starting %s", SERVER_NAME)
    try:
        yield
    finally:
        logger.info("Stopping %s", SERVER_NAME)


mcp = FastMCP(
    name=SERVER_NAME,
    instructions="<Ein Satz, was dieser Server tut.>",
    lifespan=<name>_lifespan,
)

mcp.tool(
    <tool_function>,
    name="<tool_name>",
    description="<Wird dem LLM angezeigt – präzise und handlungsorientiert.>",
)


@mcp.custom_route("/health", methods=["GET"], include_in_schema=False)
async def health(_: Request) -> Response:
    """Return a simple health payload for Docker and tests."""
    return JSONResponse({"status": "ok", "server": SERVER_NAME})


app = mcp.http_app(path=MCP_PATH, transport="http")


async def main() -> None:
    """Run the <name> server over HTTP."""
    await mcp.run_http_async(
        transport="http",
        host=settings.host,
        port=settings.port_<name>,
        path=MCP_PATH,
        log_level=settings.log_level.lower(),
    )


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
```

### 3.3 `tools/<tool>.py` – Aufbau

```python
"""Kurze Modulbeschreibung."""

from __future__ import annotations

from typing import Any

# Konstanten oben, keine Magic Numbers
DEFAULT_MAX_RESULTS: int = 3


def <tool_function>(
    param: str,
    max_results: int = DEFAULT_MAX_RESULTS,
) -> dict[str, Any]:
    """Einzeilige Zusammenfassung.

    Args:
        param: Beschreibung.
        max_results: Beschreibung.

    Returns:
        Beschreibung des Rückgabewerts.

    Raises:
        ValueError: Wann und warum.
    """
    if not param.strip():
        raise ValueError("param must not be empty")
    # ...
```

Regeln:
- **eine Funktion pro Datei** wenn die Logik nennenswert ist
- Hilfsfunktionen in derselben Datei, mit `_`-Präfix (privat)
- keine `print()`, kein nacktes `except:`
- alle öffentlichen Funktionen haben Docstrings (Google Style)
- Type Hints sind Pflicht

---

## 4. Variante: Server mit DB (storage_server)

Der `storage_server` nutzt SQLAlchemy async. Zusätzliche Dateien im Shared-Layer:

```
shared/
├── db/
│   └── session.py      ← async Session Factory
└── models/
    └── skill.py        ← ORM-Modelle (Skill, SkillFrequency, LayoutSnapshot)
```

Tool-Funktionen sind `async` und nutzen die Session direkt:

```python
# tools/save_skill_frequency.py
import shared.db.session as db_session

async def save_skill_frequency(skill: str, count: int) -> bool:
    async with db_session.get_session() as session:
        # ...
```

Integrationstests laufen gegen eine echte DB und werden per Default übersprungen:

```python
# pytest.ini / pyproject.toml:
# addopts = --ignore=tests/integration
```

---

## 5. Aktuell vorhandene Server

| Server | Port | Tools | Besonderheit |
|---|---|---|---|
| `doc_server` | 8004 | `fetch_fastapi_docs`, `fetch_pydantic_docs`, `fetch_langchain_docs`, `fetch_langgraph_docs`, `fetch_fastmcp_docs`, `fetch_pycharm_docs`, `web_search_documentation` | httpx für llms.txt + Tavily-Fallback |
| `web_search_server` | 8006 | `web_search_documentation`, `web_search` | Tavily, Domain-Filter vs. kein Filter |
| `scraper_server` | 8001 | `scrape_freelancermap` | Playwright (sync), `LayoutChangedError` |
| `skills_analyzer_server` | 8002 | `normalize_skills`, `analyze_frequency` | reine Logik, kein Netz, keine DB |
| `storage_server` | 8003 | `save_skill_frequency`, `query_top_skills`, `save_layout_snapshot` | SQLAlchemy async, PostgreSQL |

---

## 6. Tests

### Unit-Test Minimalset pro Server

```python
# tests/unit/test_<name>_server.py

from starlette.testclient import TestClient
from servers.<name>_server.server import app, mcp


# 1. Health
def test_health_endpoint_returns_ok_payload() -> None:
    with TestClient(app) as client:
        response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "server": "<name>-server"}


# 2. Tool-Registrierung
@pytest.mark.asyncio
async def test_<tool>_tool_is_registered() -> None:
    tool = await mcp.get_tool("<tool_name>")
    assert tool is not None


# 3. Funktionales Verhalten (monkeypatch externe Calls)
def test_<tool>_returns_expected_result(monkeypatch):
    monkeypatch.setenv("TAVILY_API_KEY", "test-key-dummy")
    # fake_invoke / fake_fetch patchen
    # Funktion aufrufen, Ergebnis prüfen
```

### Konventionen

- externe Calls (HTTP, Playwright, Tavily) immer via `monkeypatch` faken
- kein echter API-Key in Unit-Tests – `monkeypatch.setenv("TAVILY_API_KEY", "test-key-dummy")`
- Integrationstests in `tests/integration/`, per Default übersprungen
- `pytest-asyncio` mit `asyncio_mode = auto` in `pyproject.toml`

---

## 7. Checkliste: Neuer Server

```
[ ] Port in shared/config.py eintragen (port_<name>: int = 80XX)
[ ] Port in .env.example dokumentieren
[ ] servers/<name>_server/__init__.py anlegen
[ ] servers/<name>_server/tools/__init__.py anlegen
[ ] servers/<name>_server/tools/<tool>.py implementieren
[ ] servers/<name>_server/server.py anlegen (nach Blueprint Abschnitt 3.2)
[ ] Service in docker-compose.yml eintragen (mit Profil oder Override)
[ ] tests/unit/test_<name>_server.py anlegen (Health + Tool-Registrierung + Verhalten)
[ ] .mcp.json um neuen Server ergänzen
[ ] pre-commit run --all-files → grün
```

---

## 8. Docker-Compose-Konvention

| Datei | Enthält | Wann aktiv |
|---|---|---|
| `docker-compose.yml` | alle Services mit `profiles: ["full-stack"]` | nur mit `--profile full-stack` |
| `docker-compose.override.yml` | aktuelle Default-Services ohne Profil | immer bei `docker compose up` |

**Default heute:** `doc-server` + `web-search-server` in `override.yml`.
Neue Server kommen zunächst in `docker-compose.yml` mit `profiles: ["full-stack"]`
und werden erst in `override.yml` aufgenommen, wenn sie produktiv relevant sind.

