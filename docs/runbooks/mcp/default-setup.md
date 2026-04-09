# Default-Setup für `gjo-mcp-servers`

> Kanonische Referenz für den **aktuellen** lokalen Standardpfad.
> Stand heute: Der Default ist **`doc_server` / `mcpdoc`**.

---

## Ziel dieses Runbooks

Dieses Runbook beantwortet für den aktuellen Projektstand genau vier Fragen:

1. Welcher MCP-Server ist heute der Standard?
2. Wie starte ich ihn lokal?
3. Welche Variablen brauche ich dafür wirklich?
4. Was gehört bewusst **nicht** zum heutigen Default-Setup?

---

## Entscheidung

Der aktuelle kanonische Default von `gjo-mcp-servers` ist:

- **Service:** `doc_server`
- **Zweck:** `mcpdoc` / aktuelle Dokumentationsquellen
- **Transportziel:** `http://localhost:8004/mcp`
- **Kanonische Client-Konfiguration:** `.mcp.json` enthält aktuell nur `doc-server`

Nicht Teil des heutigen Default-Setups:

- `scraper-server`
- `analyzer-server`
- `storage-server`
- `playwright-mcp`
- `postgres`

Diese Dienste bleiben vorhanden, sind aber aktuell **opt-in** über das Compose-Profil
`full-stack`.

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

Im heutigen Stand enthält sie bewusst nur:

- `doc-server` → `http://localhost:8004/mcp`

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
LOG_LEVEL=INFO
```

### Optional für den Defaultpfad

```dotenv
TAVILY_API_KEY=
```

`TAVILY_API_KEY` ist nur nötig, wenn im `doc_server` der Tavily-basierte Fallback
`web_search_documentation` genutzt werden soll.

Die `llms.txt`-basierten Doku-Tools funktionieren auch ohne Tavily-Key.

### Nicht nötig für den aktuellen Defaultpfad

Diese Variablen sind aktuell **nicht** nötig, solange nur `doc_server` als Default läuft:

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

```zsh
cp .env.example .env
```

### 3. Default-Setup starten

```zsh
docker compose up -d
```

Warum genügt das?

- `doc_server` liegt in `docker-compose.override.yml`
- zusätzliche Services in `docker-compose.yml` laufen nur mit Profil `full-stack`
- dadurch startet der Standardpfad nur den aktuellen `doc_server`

---

## Verifikation

### Containerstatus prüfen

```zsh
docker compose ps
```

### Health prüfen

```zsh
curl -fsS http://localhost:8004/health
```

Erwartete Antwort:

```json
{"status":"ok","server":"doc-server"}
```

### MCP-Ziel prüfen

```zsh
cat .mcp.json
```

Für den aktuellen Defaultpfad muss `doc-server` als MCP-Endpunkt enthalten sein,
und es sollen keine weiteren Server in der kanonischen Datei stehen.

---

## Logs und Stop

### Logs

```zsh
docker compose logs -f doc-server
```

### Stoppen

```zsh
docker compose stop doc-server
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

