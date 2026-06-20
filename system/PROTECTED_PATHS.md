# PROTECTED PATHS — hosted-aiOS

> Filer och mappar som kräver uttryckligt OK innan skrivning.
> Gäller ALLA bottar utom Hermes och filens ägare.

## HELIGA — Rörs ALDRIG av kodande bottar

| Sökväg | Skyddad för | Vem får skriva |
|--------|-------------|----------------|
| `system/RULES.md` | Alla utom Hermes | Hermes, William |
| `system/PROTECTED_PATHS.md` | Alla utom Hermes | Hermes, William |
| `system/BOT_REGISTRY.md` | Alla utom Hermes | Hermes, William |
| `system/GLOSSARY.md` | Alla utom Hermes | Hermes, William |
| `SYSTEM_ARCHITECTURE.md` | Alla utom Hermes | Hermes, William |
| `SYSTEM_OVERVIEW.md` | Alla utom Hermes | Hermes, William |

## SKYDDADE — Kräver ägarens OK

| Sökväg | Skyddad för |
|--------|-------------|
| `users/<namn>/bots/` | Alla utom ägaren |
| `users/<namn>/memory/` | Alla utom ägaren |
| `users/<namn>/work/` | Alla utom ägaren (läs OK) |
| `system/agents/` | Kodande bottar — endast Hermes/William uppdaterar |
| `server/` | Kodande bottar — endast efter Hermes OK |
| `.env` | ALLA — synkas ALDRIG, rörs ALDRIG av bottar |

## GEMENSAMMA — Alla får skriva (inom regler)

| Sökväg | Notering |
|--------|----------|
| `shared/skills/` | Följ `file-routing.md` |
| `shared/memory/` | Följ `naming-conventions.md` |
| `obsidian/` | Följ vault-strukturen |
| `users/<namn>/skills/` | Personliga skills |
