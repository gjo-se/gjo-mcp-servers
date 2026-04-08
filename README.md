# gjo-mcp-servers

MCP Server Collection for [gjo-se.com](https://github.com/gjo-se/gjo-se.com).

Built with [fastmcp](https://github.com/jlowin/fastmcp) 3.2.0 · Python 3.12 · uv

## Servers

| Server | Port | Beschreibung |
|--------|------|-------------|
| scraper_server | 8001 | Playwright-Scraping (freelancermap.de) |
| analyzer_server | 8002 | Skill-Normalisierung & Analyse |
| storage_server | 8003 | PostgreSQL (domänenspezifische Tools) |
| doc_server | 8004 | mcpdoc + Tavily (Dev-only) |
| @playwright/mcp | 8005 | Browser-Automation & Layout-Recovery |

## Setup

```zsh
uv sync
cp .env.example .env
```
