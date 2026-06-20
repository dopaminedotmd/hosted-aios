# Naming Conventions — hosted-aiOS

> HUR filer ska namnges. Konsekvent namngivning = bottar hittar alltid rätt.

## ALLMÄNT
- **små bokstäver** genomgående
- **bindestreck** för mellanrum (aldrig mellanslag, aldrig understreck i .md-filer)
- **inga specialtecken** (åäö OK i Obsidian, undvik i kod)

## FILTYPER

| Typ | Format | Exempel |
|-----|--------|---------|
| Plan | `YYYY-MM-DD_beskrivning.md` | `2026-06-20_fas-0-foundation.md` |
| ADR | `ADR-NNNN_titel.md` | `ADR-0001_git-hosting-beslut.md` |
| Mötesanteckning | `YYYY-MM-DD_topic.md` | `2026-06-20_veckomote.md` |
| Bygglogg | `YYYY-MM-DD_bot_fas.md` | `2026-06-20_claude-code_fas1.md` |
| Bot-persona | `persona.md` (Hermes-standard) eller `CLAUDE.md` (Claude Code) | |
| Skill | `kort-beskrivning.md` | `git-sync-rules.md` |
| Template | `typ-template.md` | `plan-template.md` |
| Serverkonfig | `tjänst.conf` eller `tjänst.json` | `nginx.conf` |
| Server-skript | `åtgärd.sh` eller `åtgärd.py` | `setup.sh` |

## UNDANTAG
- `README.md` — versaler (GitHub-standard)
- `CLAUDE.md` — versaler (Claude Code-standard)
- `SYSTEM_ARCHITECTURE.md` — versaler (toppnivå-dokument)
- `SYSTEM_OVERVIEW.md` — versaler (toppnivå-dokument)
- `RULES.md` — versaler (toppnivå-regler)
- `PROTECTED_PATHS.md` — versaler (toppnivå-regler)
- `BOT_REGISTRY.md` — versaler (toppnivå-register)
- `GLOSSARY.md` — versaler (toppnivå-referens)
- `REASONING_BANK.md` — versaler (gemensamt minne)
- `.gitignore`, `.env` — dotfiles (UNIX-standard)

## KODFILER
- Python: `snake_case.py`
- TypeScript/JavaScript: `camelCase.ts` (komponenter: `PascalCase.tsx`)
- Bash: `kebab-case.sh`
- JSON/YAML: `kebab-case.json`
