# Default-Setup für `gjo-mcp-servers`

> Kanonische Referenz für den **aktuellen** lokalen Standardpfad.
> Stand heute: Der Default sind **`doc_server`** (8004) und **`web_search_server`** (8006).

---

## Ziel dieses Runbooks

Dieses Runbook beantwortet für den aktuellen Projektstand genau vier Fragen:

1. Welcher MCP-Server ist heute der Standard?
2. Wie starte ich ihn lokal?
3. Welche Variablen brauche ich dafür wirklich?
4. Was gehört bewusst **nicht** zum heutigen Default-Setup?

---

## Entscheidung

Der aktuelle kanonische Default von `gjo-mcp-servers` sind:

- **Service:** `doc_server` + `web_search_server`
- **Zweck:** aktuelle Dokumentationsquellen + generische Web-Suche
- **Transportziele:** `http://localhost:8004/mcp` · `http://localhost:8006/mcp`
- **Kanonische Client-Konfiguration:** `.mcp.json` enthält `doc-server` und `web-search-server`

Nicht Teil des heutigen Default-Setups:

- `scraper-server`
- `analyzer-server`
- `storage-server`
- `playwright-mcp`
- `postgres`

Diese Dienste bleiben vorhanden, sind aber aktuell **opt-in** über das Compose-Profil
`full-stack`.

### Explizite Betriebsentscheidungen

Für den aktuellen Projektstand gelten bewusst diese Entscheidungen:

1. `doc-server` und `web-search-server` liegen in `docker-compose.override.yml`.
2. Der lokale Standardbefehl bleibt `docker compose up -d`.
3. PostgreSQL ist für den heutigen Default nicht nötig.
4. Pflichtfelder: `PORT_DOC`, `PORT_WEB_SEARCH` und `LOG_LEVEL`.
5. `TAVILY_API_KEY` ist für `web_search_documentation` und `web_search` erforderlich.
6. Alle weiteren MCP-Server gehören aktuell nicht zum kanonischen Default.

---

## Benötigte Dateien

Für den aktuellen Defaultpfad relevant:

- `docker-compose.yml`
- `docker-compose.override.yml`
- `.env.example`
- `.env`
- `README.md`
- `.mcp.json`

Permanente Referenz für den Setup-Zustand:

- `docs/runbooks/mcp/default-setup.md`

---

## Kanonische `.mcp.json`

Die Datei `.mcp.json` im Repo-Root ist die aktuelle Quelle der Wahrheit für den
MCP-Client-Default.

Im heutigen Stand enthält sie:

- `doc-server` → `http://localhost:8004/mcp`
- `web-search-server` → `http://localhost:8006/mcp`

Nicht Teil der kanonischen Default-Konfiguration:

- `scraper-server`
- `analyzer-server`
- `storage-server`
- `playwright-mcp`

Diese Server können später wieder in eine erweiterte Konfiguration aufgenommen werden,
gehören aber aktuell **nicht** zum Standard.

---

## Benötigte Variablen

### Pflicht für den Defaultpfad

```dotenv
PORT_DOC=8004
PORT_WEB_SEARCH=8006
LOG_LEVEL=INFO
```

### Pflicht für Web-Search-Tools

```dotenv
TAVILY_API_KEY=<key>
```

`TAVILY_API_KEY` ist erforderlich für `web_search_documentation` und `web_search`.
Die `llms.txt`-basierten Doku-Tools (`fetch_*_docs`) funktionieren auch ohne Key.

### Nicht nötig für den aktuellen Defaultpfad

Diese Variablen sind aktuell **nicht** nötig, solange nur der Default-Stack (`doc_server` + `web_search_server`) läuft:

```dotenv
PORT_SCRAPER=8001
PORT_ANALYZER=8002
PORT_STORAGE=8003
PORT_PLAYWRIGHT=8005
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/mcp_servers
POSTGRES_DB=mcp_servers
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
```

---

## Kanonischer Startpfad

### 1. Abhängigkeiten synchronisieren

```zsh
uv sync
```

### 2. Lokale Umgebung anlegen

Einmalig nach dem Klonen oder nur falls `.env` noch nicht existiert:

```zsh
cp .env.example .env
```

Diesen Schritt nicht bei jedem Start wiederholen, damit lokale Werte in `.env`
nicht versehentlich überschrieben werden.

### 3. Default-Setup starten

```zsh
docker compose up -d
```

Warum genügt das?

- `doc_server` und `web_search_server` liegen in `docker-compose.override.yml`
- zusätzliche Services in `docker-compose.yml` laufen nur mit Profil `full-stack`
- dadurch startet der Standardpfad genau diese beiden Server

---

## Verifikation

### Containerstatus prüfen

```zsh
docker compose ps
```

### Health prüfen

```zsh
curl -fsS http://localhost:8004/health
curl -fsS http://localhost:8006/health
```

Erwartete Antworten:

```json
{"status":"ok","server":"doc-server"}
{"status":"ok","server":"web-search-server"}
```

### MCP-Ziel prüfen

```zsh
cat .mcp.json
```

Für den aktuellen Defaultpfad müssen `doc-server` und `web-search-server` als
MCP-Endpunkte enthalten sein.

---

## Logs und Stop

### Logs

```zsh
docker compose logs -f doc-server
docker compose logs -f web-search-server
```

### Stoppen

```zsh
docker compose stop
```

### Komplett herunterfahren

```zsh
docker compose down
```

---

## Optionaler Ausbaupfad

Der Mehrserver-Stack ist aktuell **nicht** der Standard, kann aber explizit gestartet werden:

```zsh
docker compose --profile full-stack up -d
```

Dafür sind zusätzliche Ports, Datenbank-Settings und gegebenenfalls weitere
fachliche Voraussetzungen nötig.

Dieser Pfad gehört zu späteren Ausbau- und Folgetickets – nicht zum heutigen Default.

