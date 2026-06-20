# Shannon AI — Setup Guide

## Steg 1: Skaffa API-nyckel

1. Gå till https://shannon-ai.com/login
2. Skapa konto / logga in
3. Gå till https://shannon-ai.com/docs/api/your-api-key
4. Kopiera din API-nyckel

## Steg 2: Fyll i nyckeln

Ersätt `DIN_SHANNON_API_NYCKEL_HÄR` i dessa två filer:

- `C:\Users\willi\.opencode.json` (OpenCode)
- `C:\Users\willi\.claude\settings-shannon.json` (Claude Code)

## Steg 3: Använd

### OpenCode
Starta OpenCode — den använder automatiskt Shannon som default.
Byt modell: `opencode --model shannon-1.6-pro`

### Claude Code
Växla till Shannon:
```bash
bash ~/.claude/switch-claude.sh shannon
```
Starta Claude Code — kör `/model` för att se tillgängliga modeller.

Växla tillbaka till Z.AI:
```bash
bash ~/.claude/switch-claude.sh zai
```

## Modeller

| Modell | Typ | Använd för |
|--------|-----|-----------|
| `shannon-1.6-lite` | Snabb, 128K | **Fas 0 — OpenCode.** Filskapande, scaffolds. |
| `shannon-coder-1` | Kod-optimerad, 128K | **Fas 0-2 — Claude Code.** Server, skript. |
| `shannon-1.6-pro` | Reasoning, 128K | Komplex analys, granskning. |
| `shannon-2-pro` | Ny generation, 128K | Djup reasoning. |

## Priser (prenumeration)

| Plan | Pris/mån | Tokens/dag | Coder calls/4h |
|------|----------|-----------|----------------|
| Free | $0 | 30 000 | 3 |
| Plus | $5.99 | 80 000 | 20 |
| Standard | $19.99 | 265 000 | 40 |

Free-tier räcker för att testa Fas 0.
