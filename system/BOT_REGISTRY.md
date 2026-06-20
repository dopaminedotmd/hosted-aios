# BOT REGISTRY — hosted-aiOS

> Alla bottar i systemet. Roller, behörigheter, triggers.

| Bot | Roll | Kodar? | Granskar? | Delegerar? | Läser | Skriver |
|-----|------|--------|-----------|------------|-------|---------|
| **Hermes** | Projektledare | NEJ | NEJ | JA (till alla) | Hela systemet | `system/`, `shared/`, `users/*/bots/` |
| **Claude Code** | Huvudkodare | JA | NEJ | NEJ | Hela systemet | `users/william/work/`, `shared/`, `obsidian/`, `server/`, `webapp/` |
| **OpenCode** | Kodare | JA | NEJ | NEJ | Hela systemet | `users/william/work/`, `shared/`, `obsidian/`, `webapp/` |
| **Codex** | Kodare (alt) | JA | NEJ | NEJ | Hela systemet | `users/william/work/`, `webapp/` |
| **Antigravity** | Granskare | **ALDRIG** | **JA** | NEJ | Hela systemet | `shared/memory/`, `obsidian/` |
| **Shannon** | Researcher | NEJ | NEJ | NEJ | Hela systemet | `obsidian/04-research/` |

## DELEGERINGSFLÖDE

```
Hermes (planerar) → OpenCode/Claude Code/Codex (bygger) → Antigravity (granskar) → Hermes (checkar av)
```

## REGLER PER BOT

### Hermes
- Planerar ALLT. Delegerar ALLT byggarbete.
- Gör ALDRIG kodändringar som en annan bot redan analyserat.
- Skriver prompts, inte kod.
- Vid frustration hos William: stoppa, skriv prompt, delegera.

### Claude Code
- Huvudkodare för komplexa byggen: server-setup, Git-synk-skript, nginx-konfig.
- Läser `shared/skills/` före varje bygge.
- Max 2 försök per fil. Vid tredje fail → rapportera till Hermes.

### OpenCode
- Kodare för scaffolds, templates, READMEs, enklare byggen.
- Läser `shared/templates/` före scaffold-byggen.

### Codex
- Snabbkodare för enstaka filer, enkla fixar.
- Används när OpenCode/Claude Code är upptagna.

### Antigravity
- Granskar ALLT färdigt bygge.
- ALDRIG koda. ALDRIG föreslå kodändringar direkt — rapportera till Hermes.
- Output: strukturerad granskningsrapport (Godkänt / Varningar / Blockerare).

### Shannon
- Research-bot. Svarar på "hur gör man X?", "vad är bäst för Y?".
- Output: faktabaserad research med källor.
