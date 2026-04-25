# Runbook: Playwright MCP Server

> Kanonische Referenz für den `playwright-mcp` Dienst im `gjo-mcp-servers` Projekt.
> Letzte Aktualisierung: 2026-04-25 | Ticket: #278

---

## Übersicht

Der Playwright MCP Server stellt Browser-Automatisierungs-Tools per MCP-Protokoll bereit.
Er basiert auf `@playwright/mcp` (Microsoft, npm) und ist ausschließlich für
**KI-gesteuerte Use Cases** vorgesehen – primär GitHub Copilot Agent.

> ⚠️ Der AIScope-Scraper verwendet Playwright Python direkt (deterministisch, kein LLM).
> Dieser Server ist **nicht** für den Scraper-Workflow zuständig.

---

## Port & Konfiguration

| Variable | Wert | Beschreibung |
|----------|------|--------------|
| `PORT_PLAYWRIGHT` | `8005` | Host-Port (`.env`) |
| Container-Port | `8005` | Interner Port |
| Capabilities | `vision,pdf,testing` | Aktivierte MCP-Erweiterungen |
| Host | `0.0.0.0` | Bind-Adresse (`--host=0.0.0.0` für IPv4-Healthcheck) |
| Transport | StreamableHTTP | Endpoint `/mcp` (Standard); `/sse` verfügbar (Legacy) |

---

## Start & Stop

### Nur den Playwright-Server starten

```bash
cd ~/projects/gjo-mcp-servers
docker compose --profile full-stack up playwright-mcp -d
```

### Gesamten Full-Stack starten (inkl. Playwright)

```bash
docker compose --profile full-stack up -d
```

### Stoppen

```bash
docker compose stop playwright-mcp
```

### Logs einsehen

```bash
docker compose logs -f playwright-mcp
```

---

## Docker Build

```bash
cd ~/projects/gjo-mcp-servers
docker compose --profile full-stack build playwright-mcp
```

Das Image wird aus `servers/playwright/Dockerfile` gebaut:
- Base: `node:22-slim`
- Chromium wird via `npx playwright install chromium --with-deps` installiert
- Alle System-Dependencies für Headless-Chromium sind im Dockerfile enthalten

---

## Capabilities

Der Server startet mit `--caps=vision,pdf,testing` und stellt folgende Capability-Gruppen bereit:

| Flag | Aktivierte Tools |
|------|-----------------|
| *(default)* | Navigation, Snapshot, Interaktion, Formulare, Keyboard, Tabs, Dialogs, Warten, JS-Ausführung, Netzwerk, Console, Tracing |
| `vision` | `browser_screenshot` – Screenshot als Base64 |
| `pdf` | `browser_pdf_save` – Seite als PDF speichern |
| `testing` | `browser_verify_element_visible`, `browser_verify_text_visible` |

---

## Verfügbare MCP-Tools

| Kategorie | Tool | Beschreibung |
|-----------|------|--------------|
| **Navigation** | `browser_navigate` | URL aufrufen, DOM laden (JS-gerendert) |
| | `browser_navigate_back` | Zurück navigieren |
| | `browser_navigate_forward` | Vorwärts navigieren |
| | `browser_reload` | Seite neu laden |
| **Snapshot** | `browser_snapshot` | Accessibility-Tree (token-effizient) |
| **Interaktion** | `browser_click` | Element anklicken |
| | `browser_hover` | Mouse-Over auf Element |
| | `browser_drag` | Element ziehen |
| **Formulare** | `browser_type` | Text tippen |
| | `browser_fill` | Feld direkt befüllen |
| | `browser_select_option` | Dropdown-Option auswählen |
| | `browser_check` / `browser_uncheck` | Checkbox |
| **Keyboard & Mouse** | `browser_press_key` | Einzelne Taste (Enter, Tab, …) |
| | `browser_mouse_move` | Maus an Koordinate |
| **Tabs** | `browser_tab_new` | Neuen Tab öffnen |
| | `browser_tab_list` | Offene Tabs auflisten |
| | `browser_tab_select` | Tab wechseln |
| | `browser_tab_close` | Tab schließen |
| **Dialogs** | `browser_handle_dialog` | alert / confirm / prompt |
| **Warten** | `browser_wait_for_timeout` | Wartezeit in ms |
| | `browser_wait_for_load_state` | Warten bis DOM/network/idle |
| **JS-Ausführung** | `browser_evaluate` | JS im Browser-Kontext ausführen |
| **Netzwerk & Storage** | `browser_network_requests` | Netzwerkanfragen der Seite |
| | `browser_get_storage_state` | Cookies + localStorage |
| | `browser_set_storage_state` | Session / Auth-State setzen |
| | `browser_route_clear` | Route-Mocks entfernen |
| **Console** | `browser_console_messages` | Browser-Konsolen-Output |
| **Screenshots** ⚙️ | `browser_screenshot` | Base64-Screenshot (`--caps=vision`) |
| **PDF** ⚙️ | `browser_pdf_save` | Seite als PDF (`--caps=pdf`) |
| **Testing** ⚙️ | `browser_verify_element_visible` | Element-Sichtbarkeit (`--caps=testing`) |
| | `browser_verify_text_visible` | Text-Sichtbarkeit (`--caps=testing`) |
| **Tracing** | `browser_start_tracing` | Playwright-Trace starten |
| | `browser_stop_tracing` | Trace beenden + speichern |

---

## Smoke-Test

Nach dem Start folgende Checks manuell via MCP-Client oder HTTP durchführen:

```bash
# MCP-Discovery: Tool-Definitionen abrufen
curl -s http://localhost:8005/ | head -50

# Healthcheck
docker compose ps playwright-mcp
```

Erwartete Smoke-Test-Ergebnisse:
- `browser_navigate` + `browser_snapshot` → valide Ausgabe für eine bekannte URL
- `browser_evaluate("document.title")` → Seitentitel als String
- `browser_screenshot` → Base64-String (Vision-Cap aktiv)
- MCP-Discovery → alle Tools aus der Tabelle abrufbar

---

## Debug

### Container-Shell öffnen

```bash
docker compose --profile full-stack exec playwright-mcp sh
```

### Chromium-Installation prüfen

```bash
docker compose --profile full-stack exec playwright-mcp npx playwright --version
```

### Häufige Probleme

| Problem | Ursache | Lösung |
|---------|---------|--------|
| Container startet nicht | Fehlende System-Libs | `docker compose build --no-cache playwright-mcp` |
| `browser_screenshot` schlägt fehl | `--caps=vision` nicht aktiv | CMD im docker-compose prüfen |
| Port bereits belegt | Anderer Prozess auf 8005 | `lsof -i :8005` → Prozess stoppen |

---

## Abhängigkeiten

- keine (Voraussetzungs-Ticket #278)

---

## Verwandte Dokumente

- Ticket: `docs/epics/ai_scope/Iteration 2-278-mcp-playwright-server.md`
- `servers/playwright/package.json`
- `servers/playwright/Dockerfile`
- `docker-compose.yml` → Service `playwright-mcp`

