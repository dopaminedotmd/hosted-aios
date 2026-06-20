# File Routing — hosted-aiOS

> VAR varje filtyp ska placeras. Slå upp här innan du skapar en fil.

## REGLER
- Slå upp filtypen i tabellen nedan
- Finns den inte? Fråga Hermes.
- Skapa ALDRIG filer i rotmappen

## FILTYP → PLACERING

| Filtyp | Mapp | Exempel |
|--------|------|---------|
| Systemregler | `system/` | `system/RULES.md` |
| Bot-instruktion | `system/agents/` | `system/agents/hermes.md` |
| Personlig bot-persona | `users/<namn>/bots/<bot>/` | `users/william/bots/hermes/persona.md` |
| Gemensam skill | `shared/skills/<kategori>/` | `shared/skills/system/git-sync-rules.md` |
| Personlig skill | `users/<namn>/skills/` | `users/william/skills/my-workflow.md` |
| Plan | `obsidian/01-planning/` | `obsidian/01-planning/fas-0-foundation.md` |
| ADR | `obsidian/02-decisions/` | `obsidian/02-decisions/ADR-0001_git-hosting.md` |
| Mötesanteckning | `obsidian/03-meetings/` | `obsidian/03-meetings/2026-06-20_weekly.md` |
| Research | `obsidian/04-research/` | `obsidian/04-research/ollama-modeller.md` |
| Bygglogg | `obsidian/05-building/` | `obsidian/05-building/2026-06-20_fas0-build.md` |
| Serverkonfig | `server/<tjänst>/` | `server/nginx/nginx.conf` |
| Server-skript | `server/<tjänst>/` | `server/ollama/setup.sh` |
| Webbapp-kod | `webapp/` | `webapp/src/App.tsx` |
| Template | `shared/templates/` | `shared/templates/plan-template.md` |
| Gemensamt minne | `shared/memory/` | `shared/memory/REASONING_BANK.md` |
| Personligt minne | `users/<namn>/memory/` | `users/william/memory/preferences.md` |
| Personligt arbete | `users/<namn>/work/` | `users/william/work/draft-plan.md` |
| Obsidian-konfig | `obsidian/.obsidian/` | `obsidian/.obsidian/app.json` |
| Obsidian-template | `obsidian/templates/` | `obsidian/templates/plan-template.md` |

## ANTI-PATTERNS
- ❌ `hosted-aios/min-fil.md` — ALDRIG i root
- ❌ `hosted-aios/system/min-skill.md` — skills ligger i `shared/skills/` eller `users/*/skills/`
- ❌ `hosted-aios/obsidian/min-kod.py` — kod ligger i `webapp/` eller `server/`
