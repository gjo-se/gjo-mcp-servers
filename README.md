# gjo-mcp-servers

MCP Server Collection for [gjo-se.com](https://github.com/gjo-se/gjo-se.com).

Built with [fastmcp](https://github.com/jlowin/fastmcp) · Python 3.12 · uv

---

## Schnelleinstieg

### 1. Abhängigkeiten

```zsh
uv sync
```

### 2. `.env` anlegen (einmalig)

```zsh
cp .env.example .env
```

Pflichtfelder für den Default-Start:

```dotenv
PORT_DOC=8004
PORT_WEB_SEARCH=8006
LOG_LEVEL=INFO
TAVILY_API_KEY=
```

### 3. Server starten

```zsh
docker compose up -d
```

Startet den aktuellen Default: **`doc-server`** (Port 8004) + **`web-search-server`** (Port 8006).

### 4. Verifikation

```zsh
curl -fsS http://localhost:8004/health
curl -fsS http://localhost:8006/health
```

### 5. MCP-Client-Konfiguration

```zsh
cat .mcp.json
```

Die Datei `.mcp.json` ist die kanonische Quelle für die MCP-Client-Konfiguration
(symlinkt zu `~/.config/github-copilot/intellij/mcp.json`).

---

## Services

| Service | Port | Default | Beschreibung |
|---|---|---|---|
| `doc-server` | 8004 | ja¹ | llms.txt-Fetch + Tavily-Fallback für aktuelle Docs |
| `web-search-server` | 8006 | ja¹ | Tavily-Suche mit und ohne Domain-Filter |
| `scraper-server` | 8001 | opt-in | Playwright-Scraping (freelancermap.de) |
| `analyzer-server` | 8002 | opt-in | Skill-Normalisierung und Frequenzanalyse |
| `storage-server` | 8003 | opt-in | SQLAlchemy-Persistenz (PostgreSQL) |
| `playwright-mcp` | – | opt-in | Playwright MCP Bridge |

¹ `doc-server` und `web-search-server` sind in `docker-compose.override.yml` definiert
und starten automatisch mit `docker compose up -d`.

Opt-in (Full-Stack):

```zsh
docker compose --profile full-stack up -d
```

---

## Logs / Stop

```zsh
docker compose logs -f doc-server
docker compose stop
docker compose down
```

---

## Tests

```zsh
uv run pytest
uv run pytest --run-integration
uv run pytest tests/ -k "web_search"
```

---

## Dokumentation

| Dokument | Inhalt |
|---|---|
| [default-setup.md](docs/runbooks/mcp/default-setup.md) | Kanonischer Start-Pfad, Variablen, Verifikation |
| [mcp-server-blueprint.md](docs/runbooks/mcp/mcp-server-blueprint.md) | Dateistruktur, Konventionen, Vorlage für neue Server |

Shell-Helper für den Alltag (aus `gjo-se.com` heraus):
→ [`scripts/shell/dev.zsh`](https://github.com/gjo-se/gjo-se.com/blob/develop/scripts/shell/dev.zsh) –
`start_mcp_docker` / `stop_mcp_docker` / `build_mcp_docker` / `logs_mcp_docker`

