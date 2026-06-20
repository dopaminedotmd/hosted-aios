# hosted-aiOS — Systemöversikt
> Hur systemet fungerar. Enkelt, detaljerat, exakt.

---

## Vad är hosted-aiOS?

Ett delat AI-operativsystem för tre personer. En lokal dator kör en LLM (via Ollama). Via en webapp når alla LLM:en — hemifrån, från mobilen, var som helst. Systemet innehåller också en gemensam kunskapsbas (Obsidian), ett bot-system som automatiserar byggarbete, och Git-synkronisering så att alla tre alltid har identiska filer.

**Tre lager:**
1. **Server** — den fysiska datorn. Kör Ollama (LLM) + webapp + reverse proxy.
2. **Webbapp** — gränssnittet. Chat med LLM:en, alla funktioner. Nås via webbläsare.
3. **Filsystem** — mappstrukturen. All kod, alla planer, all kunskap. Synkas via Git mellan alla tre personers datorer.

---

## Hur allt hänger ihop

```
DATOR 1 (LLM-server)                 DATOR 2 (William)              DATOR 3 (Vän)
┌─────────────────────┐              ┌─────────────────┐            ┌─────────────────┐
│ Ollama (LLM)        │              │ hosted-aios/    │            │ hosted-aios/    │
│ ↓ API-anrop         │              │   (Git-klon)    │            │   (Git-klon)    │
│ Web App (port 3000) │              │   obsidian/     │            │   obsidian/     │
│ ↓ proxied           │              │   users/        │            │   users/        │
│ Nginx (port 443)    │              │   shared/       │            │   shared/       │
└──────┬──────────────┘              └────────┬────────┘            └────────┬────────┘
       │                                     │                              │
       │         GitHub (privat repo)        │                              │
       └─────────────────────────────────────┴──────────────────────────────┘
                     ↑ pull/push var 5:e minut (cron)
```

**Dataflöde:**
1. Användare öppnar webapp i telefon/webbläsare → skriver meddelande
2. Webapp skickar API-anrop till Ollama (på LLM-servern)
3. Ollama genererar svar → skickar tillbaka till webapp
4. Användaren ser svaret

**Synkflöde:**
1. William ändrar en fil i `obsidian/` på sin dator
2. Cron-script (var 5:e minut) → `git add` → `git commit` → `git push` till GitHub
3. Väns dator (cron, var 5:e minut) → `git pull` → filen dyker upp lokalt
4. Samma sak åt andra hållet

---

## Filstrukturen — vad som finns var

```
hosted-aios/
│
├── system/          ← REGLERNA. Alla bottar läser här först.
│   │                 Här står VEM som får göra VAD och HUR filer ska namnges.
│   │                 Skrivskyddad för de flesta bottarna.
│   │
├── users/           ← PERSONLIGA MAPPAR. En per person.
│   ├── william/     ← Williams bots, skills, minnen, arbetsfiler
│   ├── user2/       ← Nästa persons
│   └── user3/       ← Tredje personens
│   │
│   │   Varje användarmapp innehåller:
│   │   - README.md   → Installationsinstruktioner + AI-prompt för att sätta upp
│   │   - bots/       → Personliga bot-konfigurationer (persona.md, CLAUDE.md)
│   │   - skills/     → Personliga skills (bara dina bottar ser dem)
│   │   - memory/     → Bot-minnen (vad dina bottar lärt sig om dig)
│   │   - work/       → Ditt pågående arbete
│   │
├── shared/          ← GEMENSAMT. Alla bottar + alla personer delar.
│   ├── skills/      ← Gemensamma skills. Alla bottar läser här.
│   └── memory/      ← Gemensamma minnen (beslut, ADR:er)
│   │
├── obsidian/        ← KUNSKAPSBASEN. Er gemensamma Obsidian-vault.
│   │                 Planer, anteckningar, research, mötesprotokoll.
│   │                 Synkas mellan alla tre datorer.
│   │
├── server/          ← SERVERKONFIG. Ollama-setup, nginx, Docker.
│   │                 Bara relevant på LLM-servern.
│   │
└── webapp/          ← WEBBAPP-KODEN. Hela frontend + backend för chat-interfacet.
    │                 (Planeras i Fas 3)
```

---

## Bottarna — vem gör vad

Systemet har sex AI-bottar. Varje bot har en specifik roll. Ingen bot gör allt.

| Bot | Roll | Gör | Gör INTE |
|-----|------|-----|----------|
| **Hermes** | Projektledare | Planerar, delegerar, skriver prompts, håller koll på helheten | Kodar inte. Bygger inte. |
| **Claude Code** | Huvudkodare | Bygger server-setup, komplex kod, Git-synk-skript | Granskar inte. Planerar inte. |
| **OpenCode** | Kodare | Templates, READMEs, scaffolds, enklare byggen | Granskar inte. |
| **Codex** | Kodare (alt) | Snabba byggen, enstaka filer | Granskar inte. |
| **Antigravity** | Granskare | Analyserar ALL output från kodande bottar. Verifierar att bygget matchar planen. | **Kodar ALDRIG.** Bara analys. |
| **Shannon** | Researcher | Teknik-spaning, "hur gör man X?", hittar rätt bibliotek | Kodar inte. Bygger inte. |

### Hur bottarna arbetar tillsammans

```
1. HERMES skriver en plan → "Fas 0: skapa filstruktur"
2. HERMES delegerar till OPENCODE: "Bygg README-filer enligt denna prompt"
3. OPENCODE bygger → skriver färdiga filer
4. OPENCODE skickar slutmeddelande → "Klart. 3 READMEs skapade."
5. HERMES kopierar slutmeddelandet → skickar till ANTIGRAVITY
6. ANTIGRAVITY granskar → "README 3 saknas. README 1 har fel format."
7. ANTIGRAVITY svarar HERMES → HERMES checkar av eller skickar tillbaka för fix
```

**Regel:** Antigravity granskar ALLTID. Hermes delegerar ALLTID. Ingen bot kodar och granskar samma sak.

---

## Git-synken — hur filer hålls identiska

**Problem:** Tre personer ändrar filer på tre olika datorer. Hur ser alla alltid samma sak?

**Lösning:** GitHub (privat repo) + cron-synk var 5:e minut.

### Vattentäta regler

1. **Pull före push.** Alltid. Inga undantag.
2. **Vid konflikt → spara BÅDA versionerna.** En fil döps om till `filnamn.md.CONFLICT-2026-06-20-143022.md`. Ingenting raderas.
3. **Aldrig force push.** `git push --force` är förbjudet. Det skriver över andras arbete.
4. **Allt loggas.** Varje synk-operation skrivs till `shared/memory/sync-log.md`.
5. **Stash-skydd.** Före varje pull sparas osparade ändringar i en stash. Efter pull återställs de.

### Vad som synkas
- **Allt i `hosted-aios/` utom:**
  - `.env` (hemliga nycklar — synkas ALDRIG)
  - `.hermes/plans/` (Hermes interna arbetsfiler)
  - `node_modules/`, `__pycache__/`, `.venv/` (genererade filer)

---

## Obsidian — er gemensamma kunskapsbas

Obsidian är en markdown-baserad anteckningsapp. Er vault ligger i `obsidian/` och synkas via Git.

**Vad som finns där:**
- `00-dashboard.md` — startsida. Visar aktuell fas, status, vad som pågår.
- `01-planning/` — alla planer. En fil per fas.
- `02-decisions/` — ADR:er (Architecture Decision Records). Här dokumenteras ALLA tekniska beslut.
- `03-meetings/` — mötesanteckningar.
- `04-research/` — teknik-spaning, "borde vi använda X?"
- `05-building/` — byggloggar. Vad som byggdes, av vem, resultat.
- `06-personal/` — personliga anteckningar. En undermapp per person.

**Alla tre personer kopplar sin lokala Obsidian till samma `obsidian/`-mapp.** Via Git-synken ser alla alltid den senaste versionen.

---

## Säkerhet — vad som skyddas

| Nivå | Vad | Hur |
|------|-----|-----|
| **Hemliga nycklar** | `.env` | I `.gitignore`. Synkas ALDRIG. |
| **Systemfiler** | `system/` | Skrivskyddad för kodande bottar. Bara Hermes + William får ändra. |
| **Personliga filer** | `users/<namn>/` | Bara ägaren + Hermes får skriva. |
| **Webbapp** | API + UI | HTTPS via nginx + Let's Encrypt. Rate limiting. Security headers. |
| **Ollama** | LLM-API | Exponeras INTE direkt mot internet. Nginx reverse proxy → bara webappen når den. |

---

## Vad som återstår att bestämma

1. **Server-OS?** → Rekommendation: **Linux** (Ubuntu Server). Bättre GPU-stöd för Ollama. Lägre overhead.
2. **Docker?** → Rekommendation: **Ja.** Isolerar Ollama, webapp, nginx i separata containrar. Enklare att underhålla.
3. **Extern åtkomst?** → Rekommendation: **Tailscale.** Gratis, enkelt, krypterat. Ingen port forwarding. Funkar från mobil.
4. **Autentisering?** → Rekommendation: **JWT + valfri OAuth.** Flexibelt. Börja med enkel lösenord + JWT. Lägg till OAuth senare.
5. **Ollama-modell?** → Väntar på GPU-specs från server-maskinen. Rekommendation: börja med `llama3.2` (3B) eller `mistral` (7B) beroende på tillgänglig VRAM.

---

## Ordlista

| Term | Betyder |
|------|---------|
| **LLM** | Large Language Model — "AI:n". T.ex. Llama, Mistral. |
| **Ollama** | Programvara som kör LLM:er lokalt på en dator. |
| **Reverse proxy** | Nginx/Caddy. Tar emot webbtrafik utifrån och skickar vidare till rätt program internt. |
| **Obsidian** | Anteckningsapp som använder markdown-filer. |
| **Vault** | En mapp med markdown-filer som Obsidian öppnar. |
| **Bot** | En AI-agent med en specifik roll (Hermes, Claude Code, etc.). |
| **Skill** | En instruktionsfil som lär en bot hur den ska göra en specifik uppgift. |
| **ADR** | Architecture Decision Record — ett dokument som förklarar VARFÖR ett tekniskt beslut togs. |
| **Cron** | Schemaläggare. Kör ett skript automatiskt med jämna mellanrum. |
| **Git** | Versionshantering. Håller koll på alla ändringar i filer. |
| **GitHub** | Webbtjänst som hostar Git-repos. |
| **Stash** | Git-funktion. Sparar temporärt osparade ändringar utan att commita. |
