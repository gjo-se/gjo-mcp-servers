# gjo-mcp-servers

MCP Server Collection for [gjo-se.com](https://github.com/gjo-se/gjo-se.com).

Built with [fastmcp](https://github.com/jlowin/fastmcp) 3.2.0 · Python 3.12 · uv

## Aktueller Default

Der aktuelle kanonische Einstieg ist **`doc_server` / `mcpdoc`**.

- Standard-Startpfad: nur `doc_server`
- kein PostgreSQL im Default notwendig
- `scraper-server`, `analyzer-server`, `storage-server` und `playwright-mcp`
  sind aktuell **nicht** Teil des verpflichtenden Default-Setups

Der vollständige Mehrserver-Stack bleibt vorhanden, ist aber nur ein **opt-in**-
Pfad über das Compose-Profil `full-stack`.

Die permanente Referenz für diesen Zustand liegt in
`docs/runbooks/mcp/default-setup.md`.

Die kanonische MCP-Client-Konfiguration ist `.mcp.json` im Repo-Root.
Sie enthält im aktuellen Default **nur** `doc-server`.

## Services

| Service | Port | Status | Beschreibung |
|---------|------|--------|--------------|
| `doc_server` | 8004 | aktueller Default | `mcpdoc` + Tavily-Fallback für aktuelle Doku |
| `scraper_server` | 8001 | optional / später | Playwright-Scraping (freelancermap.de) |
| `analyzer_server` | 8002 | optional / später | Skill-Normalisierung & Analyse |
| `storage_server` | 8003 | optional / später | domänenspezifische Storage-Tools |
| `@playwright/mcp` | 8005 | optional / später | Browser-Automation & Layout-Recovery |
| `postgres` | 5432 | optional / später | Datenbank für `storage_server` / Vollstack |

## Setup

```zsh
uv sync
cp .env.example .env
```

### Wichtige Variablen im aktuellen Default

- `PORT_DOC=8004`
- `LOG_LEVEL=INFO`
- `TAVILY_API_KEY=` ist **optional**, solange nur die `llms.txt`-Quellen genutzt werden

PostgreSQL- und weitere Service-Variablen bleiben in `.env.example` erhalten,
sind aber für den aktuellen `mcpdoc`-Default **nicht erforderlich**.

## Default-Startpfad (`mcpdoc`)

```zsh
docker compose up -d
docker compose ps
curl -fsS http://localhost:8004/health
```

Erwartung:

```json
{"status":"ok","server":"doc-server"}
```

Warum reicht `docker compose up -d`?

- `doc_server` liegt in `docker-compose.override.yml`
- alle weiteren Services in `docker-compose.yml` hängen am Profil `full-stack`
- dadurch startet der Defaultpfad nur den aktuellen `mcpdoc`-Dienst

## Kanonische `.mcp.json`

Die Datei `.mcp.json` ist die aktuelle Quelle der Wahrheit für die Standard-MCP-Konfiguration.

Im heutigen Default enthält sie bewusst nur:

- `doc-server` → `http://localhost:8004/mcp`

Damit ist klar getrennt:

- **Default heute:** `doc-server`
- **optional / später:** `scraper-server`, `analyzer-server`, `storage-server`, `playwright-mcp`

Kurze Verifikation:

```zsh
cat .mcp.json
```

Erwartung: In der kanonischen Datei ist aktuell nur `doc-server` eingetragen.

## Stop / Logs

```zsh
docker compose logs -f doc-server
docker compose stop doc-server
docker compose down
```

## Optional: Vollstack explizit starten

Dieser Pfad gehört **nicht** zum aktuellen Default-Setup.

```zsh
docker compose --profile full-stack up -d
```

Dafür werden zusätzlich die in `.env.example` dokumentierten Ports und
PostgreSQL-Variablen benötigt.

