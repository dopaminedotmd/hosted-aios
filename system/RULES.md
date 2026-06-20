# RULES — hosted-aiOS

## STARTUP-SEKVENS (obligatorisk för alla bottar)

ALLTID, före någon filoperation, läs i denna ordning:
1. system/RULES.md (denna fil)
2. system/PROTECTED_PATHS.md
3. system/BOT_REGISTRY.md (hitta din roll + behörigheter)
4. shared/skills/system/file-routing.md
5. shared/skills/system/naming-conventions.md
6. users/<ditt-namn>/bots/<din-bot>/persona.md (din personliga instruktion)

## REGLER FÖR ALLA BOTTAR

### FILPLACERING
- Alla nya filer SKA placeras enligt `shared/skills/system/file-routing.md`
- Vid osäkerhet om vart en fil ska: FRÅGA Hermes
- ALDRIG skapa filer direkt i rotmappen (`hosted-aios/`)
- ALDRIG skriva i `system/` utan Hermes eller Williams uttryckliga OK

### NAMNGIVNING
- Filer: `små bokstäver, bindestreck` (aldrig mellanslag, aldrig understreck utom i kod)
- Planer: `YYYY-MM-DD_beskrivning.md`
- ADR:er: `ADR-NNNN_titel.md`
- Loggar: `YYYY-MM-DD_bot_åtgärd.md`
- Personas: `persona.md` eller `CLAUDE.md` (för Claude Code)

### SKYDDADE ZONER
- Se `system/PROTECTED_PATHS.md` för komplett lista
- Rör ALDRIG en annan användares `users/<annat-namn>/` utan explicit OK från den personen
- `system/` är skrivskyddad för kodande bottar (OpenCode, Claude Code, Codex)

### KOMMUNIKATION
- Hermes → svenska, kortfattad, direkt
- Claude Code, OpenCode, Codex → engelska, tekniska
- Antigravity → svenska, analytisk, ALDRIG KOD
- Shannon → engelska, research-baserad

### DELEGERING
- Hermes delegerar ALLT byggarbete till kodande bottar
- Antigravity granskar ALLT färdigt bygge
- Inga bottar delegerar vidare i fler än 1 nivå
- Slutmeddelande från kodande bot → kopieras → skickas till Antigravity för granskning

### VID FEL
- Om du är osäker på något: STOPPA. Fråga Hermes.
- Om en fil inte finns där du förväntar dig: RAPPORTERA. Gissa inte.
- Om du får en konflikt med en annan bot: LOGGA till `shared/memory/REASONING_BANK.md` med prefix `[BOT-NAMN]`
