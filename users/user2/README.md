> ⚠️ Innan du kör prompten: ersätt `<REPO_ROOT>` med din lokala sökväg till `hosted-aios`.

# User2 — hosted-aiOS Setup

## Snabbstart

1. Klona repot: `git clone <github-url>`
2. Öppna `<REPO_ROOT>` i din terminal
3. Kopiera `.env.example` → `.env` och fyll i dina API-nycklar
4. Kör installationsprompten nedan

## AI-installationsprompt

Kopiera HELA texten nedan. Klistra in i din AI-assistent (Claude Code, Antigravity, etc.).
Prompten installerar automatiskt dina personliga bot-konfigurationer.

```
LÄS FÖRST:
1. <REPO_ROOT>\system\RULES.md
2. <REPO_ROOT>\system\BOT_REGISTRY.md
3. <REPO_ROOT>\users\user2\bots\

UPPGIFT: Installera mina personliga bottar för hosted-aiOS.

STEG:
1. Läs varje bot-mapp under users/user2/bots/
2. För varje bot: läs persona.md (eller CLAUDE.md) — förstå botens roll och regler
3. Kontrollera att alla sökvägar i botens persona.md pekar rätt (användarnamn, absoluta sökvägar)
4. Läs users/user2/memory/ — ladda in mina preferenser och tidigare kontext
5. Läs users/user2/skills/ — ladda in mina personliga skills
6. Verifiera att du kan navigera i systemet: hitta system/, shared/, obsidian/
7. Bekräfta: "Installation klar. [N] bottar, [N] skills, [N] minnesfiler laddade."

REGLER:
- Använd ALLTID absoluta sökvägar baserade på `<REPO_ROOT>`
- Om en fil saknas: RAPPORTERA, gissa inte
- Om en sökväg i persona.md är fel: NOTERA, ändra inte automatiskt
- Spara dina slutsatser till users/user2/memory/install-log.md
```

## Mappar

| Mapp | Innehåll |
|------|----------|
| `bots/` | Dina personliga bot-konfigurationer |
| `skills/` | Dina personliga skills |
| `memory/` | Dina bot-minnen |
| `work/` | Ditt pågående arbete |

## Miljövariabler (.env)

```env
# Obligatoriska
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...
GEMINI_API_KEY=...

# Valfria
OLLAMA_HOST=http://localhost:11434
```
