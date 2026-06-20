> ⚠️ Innan du kör något: ersätt `<REPO_ROOT>` med din lokala sökväg till `hosted-aios`.

# hosted-aiOS

> Delat AI-operativsystem. Lokal LLM-server + webapp + Obsidian-vault + bot-orkestrering.
> 3 användare. 1 server. 6 AI-bottar.

## Snabbstart

```bash
# 1. Klona repot
git clone <github-url>
cd <REPO_ROOT>

# 2. Kopiera miljövariabler
cp .env.example .env
# Fyll i .env med dina värden

# 3. Installera dina bottar
# Öppna users/<ditt-namn>/README.md — följ instruktionerna
```

## Struktur

| Mapp | Innehåll |
|------|----------|
| `system/` | Regler, bot-register, skyddslistor |
| `users/` | Personliga mappar (3 st). Bottar, skills, minnen. |
| `shared/` | Gemensamma skills + minnen |
| `obsidian/` | Gemensam kunskapsbas (Obsidian vault) |
| `server/` | Serverkonfiguration (Ollama, nginx, Docker) |
| `webapp/` | Webbapp-kod (Fas 3) |

## Bottar

| Bot | Roll |
|-----|------|
| Hermes | Projektledare — planerar, delegerar |
| Claude Code | Huvudkodare — server, komplex kod |
| OpenCode | Kodare — scaffolds, templates |
| Codex | Kodare (alt) — snabba byggen |
| Antigravity | Granskare — analyserar ALL output |
| Shannon | Researcher — teknik-spaning |

## Läs mer

- `SYSTEM_OVERVIEW.md` — Hur allt fungerar (för människor)
- `SYSTEM_ARCHITECTURE.md` — Masterplanen (för bottar)
- `obsidian/01-planning/00-master-plan.md` — Masterplanen (delad)
- `system/RULES.md` — Regler för alla bottar
