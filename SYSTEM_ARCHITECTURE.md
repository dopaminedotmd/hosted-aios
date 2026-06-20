# SYSTEM ARCHITECTURE — hosted-aiOS

> Masteröversikt för hosted-aiOS. Läses av bottar som behöver hela systembilden.

## Syfte

Bygga ett delat AI-operativsystem för tre personer med lokal LLM, webapp, Obsidian-vault och bot-orkestrering.

## Delar

- `system/` — regler, register och skyddade zoner
- `users/` — personliga botar, skills, minnen och arbete
- `shared/` — gemensamma skills, minnen och mallar
- `obsidian/` — delad kunskapsbas
- `server/` — Ollama, nginx och Docker-konfiguration
- `webapp/` — frontend/backend för chatten

## Faser

1. Foundation
2. Obsidian + Git Sync
3. Server Setup
4. Web App
5. Bot Orchestration

## Referens

Full masterplan finns i `obsidian/01-planning/00-master-plan.md`.
