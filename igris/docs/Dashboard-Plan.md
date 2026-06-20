# Overwatch Dashboard — Plan & Vision

> **Version:** 0.2.0  
> **Status:** Konceptuell planering  
> **Inspiration:** Solo Leveling (dungeon/throne aesthetic) + Pixel-art  
> **Plattform:** Desktop-app (eget fönster, standalone)  
> **Mål:** En visuell command-center där Användaren ser, interagerar med, och styr alla agenter i Igris ekosystem.

---

## 1. VISIONEN — Vad Användaren Ser

När du öppnar Overwatch Dashboard ser du en **Solo Leveling-dungeon** framifrån.

```
┌─────────────────────────────────────────────────────────────┐
│  ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░  │
│  ░░                                                  ░░  │
│  ░░          ╔══════════════════════════╗            ░░  │
│  ░░          ║        IGRIS             ║  (25% större)░░  │
│  ░░          ║      [THRONE]            ║            ░░  │
│  ░░          ╚══════════════════════════╝            ░░  │
│  ░░                                                  ░░  │
│  ░░   ┌──────┐   ┌──────┐   ┌──────┐   ┌──────┐    ░░  │
│  ░░   │S-Rank│   │A-Rank│   │ A-R │   │ B-R  │    ░░  │
│  ░░   │ [██] │   │ [▓▓] │   │ [▓▓]│   │ [▒▒] │    ░░  │
│  ░░   └──────┘   └──────┘   └──────┘   └──────┘    ░░  │
│  ░░   ┌──────┐   ┌──────┐   ┌──────┐              ░░  │
│  ░░   │C-Rank│   │ E-R  │   │ E-R  │              ░░  │
│  ░░   │ [░░] │   │ [░░] │   │ [░░] │              ░░  │
│  ░░   └──────┘   └──────┘   └──────┘              ░░  │
│  ░░                                                  ░░  │
│  ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░  │
│                [Stats] [Memory] [Chat] [Settings]          │
└─────────────────────────────────────────────────────────────┘
```

### 1.1 Den Centrala Vyn — "The Throne Room"

- Mörk dungeon-bakgrund med svaga tegel/textur-detaljer (pixel-art stil)
- **Igris sitter på en tron** i mitten/övre delen — 25% större än alla andra agenter
- Runt omkring står agenterna uppställda som **pixel-gubbar** i halvcirkel
- Varje agent har en liten **rank-crown** över sig (E=ingen, C=liten, B=medium, A=stor, S=glowing, SS=starkt glowing, SSS=mytisk glow)
- Agenter som är **aktiva** pulserar långsamt (andningseffekt)
- Agenter som är **idle** står stilla, kanske lutar sig
- Agenter som har en **aktiv task** har ett litet verktygsikon/notis
- Längst ner: en menyrad med modulära skärmar

### 1.2 Modulära Skärmar ("Screens")

Användaren kan växla och flytta runt moduler. Varje modul är en egen "skärm" som kan:

- Fästas i huvudvyn (över dungeon-vyn)
- Öppnas som overlay (sida vid sida)
- Minimeras till nedre menyraden

**Föreslagna moduler:**

| Modul | Innehåll |
|---|---|
| **Throne Room** | Huvudvyn — dungeon med alla agenter + Igris |
| **Agent List** | Listvy med alla agenter + info (rank, domain, status) |
| **Agent Detail** | Klicka på en agent → detaljer (vad de jobbar på, planer, historik) |
| **Memory Vault** | Koppling till Obsidian-liknande minnessystem |
| **The Gate** | Chattfönster — prata med valfri agent eller The System |
| **System Status** | Hardware telemetry, VRAM, uptime, logs |
| **Benchmarks** | Prestanda-statistik och rank-evolution över tid |
| **Dependency Graph** | Visualisering av agent-beroenden i grafform |
| **Quest Log** | Task backlog som RPG quest-lista |

---

## 2. AGENTREPRESENTATION — Pixel-Gubbarna

### 2.1 Designprinciper

Varje agent är en **liten pixel-art figur** (ungefär 16-24px i en pixel-art skala, uppskalad för skärmen). Varje figur bör vara:

- **Unik silhuett** baserad på agentens domän/inriktning
- **Färgkodad efter rank**
- **Animering**: stillastående med animation idle (andning, blinkning)

### 2.2 Rank-indikatorer

- En "crown" eller aura ovanför varje gubbe baserat på rank
- E-Rank: ingen crown
- C-Rank: liten enkel crown (grå)
- B-Rank: medium crown (silver)
- A-Rank: stor crown (lila)
- S-Rank: glödande crown (guld), figuren är något större
- SS-Rank: starkt glödande crown, egen bakgrunds-aura
- SSS-Rank: mytisk aura, partikeleffekter, större än S

### 2.3 Igris — Commander Figuren

- 25% större än den största agenten
- Sitter på en **pixel-art tron**
- Har en egen aura (mörkblå/svart med vita gnistor)
- Tronen har en liten glöd — Igris är alltid "aktiv"
- Klick på Igris → Commander-detaljer (hans SelfPlan, systemstatus, upptid)

---

## 3. INTERAKTION — Vad Användaren Kan Göra

### 3.1 Klicka på en Agent

När du klickar på en pixel-gubbe händer detta:

1. Agenten "steppar fram" (liten animation)
2. Ett **Agent Detail-overlay** öppnas med:

```
┌─────────────────────────────────────────────┐
│  [Stäng]                                      │
│                                               │
│  [ ██ Figur ]  Namn: Agent-X                  │
│                Rank: A-Rank                   │
│                Domain: Backend / Python        │
│                Status: Active (task #42)       │
│                                               │
│  ─── Stats ───                                │
│  STR (precision) ████████░░ 80                │
│  AGI (hastighet) ██████░░░░ 60                │
│  INT (komplex)   █████████░ 90                │
│  VIT (uptime)    ████████░░ 80                │
│                                               │
│  ─── Memory ───                                │
│  Brain.md: [Länk / förhandsvisning]            │
│  Memory.md: [Länk / förhandsvisning]           │
│                                               │
│  ─── Current Task ───                         │
│  "Implementera OAuth2 middleware"             │
│  Progress: ████████░░ 80%                     │
│  Deadline: om 2h                              │
│                                               │
│  ─── Recent ───                               │
│  • 3 patcher applicerade senaste timmen      │
│  • 0 linting-fel                             │
│  • 5/5 tester passerade                      │
│                                               │
│  [Chatta med Agent] [Skicka till Igris]       │
└─────────────────────────────────────────────┘
```

### 3.2 Chattfönstret — "The Gate"

Dashboarden har ett inbyggt meddelandesystem där du kan:

- **Chatta med en specifik agent** — agenten får ditt meddelande som en TaskAssignment
- **Chatta med The System** (DeepSeek V4-Pro via Token-Shield) — moln-arkitekten
- **Chatta med Igris** — direktkommando till Commander
- Meddelanden visas i en terminal-liknande ruta med olika färger för olika avsändare

### 3.3 Agent List (Alternativ Vy)

En sidopanel eller fullskärm som visar en **lista** över alla agenter:

| Agent | Rank | Domain | Status | Tasks | Brain |
|---|---|---|---|---|---|
| Agent-X | A | Backend | Active | 1 | [Länk] |
| Agent-Y | B | Frontend | Idle | 0 | [Länk] |
| Agent-Z | E | Testing | Training | — | [Länk] |

---

## 4. MINNESINTEGRATION — Obsidian-Länk

Varje agent har två minnesfiler som är synliga från dashboarden.

### 4.1 Filstruktur (per agent)

```
I:\Igris\memory\agents\
├── Agent-X\
│   ├── Brain.md        ← Agentens nuvarande kontext, prompt, riktlinjer
│   ├── Memory.md       ← Agentens långtidsminne (konsoliderat)
│   └── Log.md          ← Rå task-historik (för debugging)
├── Agent-Y\
│   ├── Brain.md
│   ├── Memory.md
│   └── Log.md
└── ...
```

### 4.2 Brain.md

Agentens "working memory" — vad den har för instruktioner just nu:

```markdown
# Brain: Agent-X
**Rank:** A-Rank
**Domain:** Backend / Python
**Current Task:** OAuth2 middleware (#42)
**Skills Granted:** read_file_atomic, caveman_ultra_patch, search_symbol_graph
**Context:** Projekt använder FastAPI + PyJWT. Databas är PostgreSQL.
**Active Rules:** Skriv aldrig lösenord i loggar. Använd alltid dependency injection.
```

### 4.3 Memory.md

Agentens konsoliderade erfarenheter:

```markdown
# Memory: Agent-X
**Skapad:** 2026-06-19
**Antal tasks slutförda:** 47
**Befordringshistorik:** E → C → B → A

## Lärdomar
- [2026-06-18] Användaren föredrar tydlig error-handling över silent fails
- [2026-06-17] Token-expiry måste alltid checkas före användardata returneras

## Starka Sidor
- JSON-kontrakt: 100% valid (senaste 20 tasks)
- Patch-precision: 94.7%
- Linting pass rate: 100%

## Svaga Sidor
- Hantering av edge cases — 2 misslyckanden senaste veckan
```

### 4.4 Från Dashboarden

Användaren kan:
- Öppna Brain.md / Memory.md direkt från agent-detaljvyn
- Länka till Obsidian vault via `obsidian://open?...` URI-scheman
- Editera Brain.md direkt (om Användaren vill justera agentens kontext manuellt)

---

## 5. TEKNISKA ÖVERVÄGANDEN

### 5.1 Plattform

**Desktop-app** — eget fönster, standalone.

**Rekommendation:** Tauri (Rust + React/Vue/Svelte frontend) — lätt vikt (~5-10MB), webb-teknik för UI, säker sandlåda, minimal minnesanvändning. Viktigt eftersom dashboarden delar dator med GPU-tunga modeller.

### 5.2 Pixel-Art Render

- Använd en **CSS pixel-art scaler** (`image-rendering: pixelated`)
- Agent-figurer som **små spritesheets** (PNG med transparent bakgrund)
- Rank-crowns och auras som **CSS-animationer** (glow, pulse)

### 5.3 Kommunikation med Igris

Dashboarden pratar med Igris via **lokala portar** (WebSocket):

```
┌─────────────┐         WebSocket         ┌──────────────┐
│  Overwatch   │ ◄──────────────────────►  │  Igris Core  │
│  Dashboard    │        localhost:        │  (Commander)  │
│  (Tauri App)  │        9876              │               │
└─────────────┘                           └──────┬───────┘
                                                  │
                                        ┌─────────┴─────────┐
                                        │   Agent Containers  │
                                        │   (Docker)          │
                                        └───────────────────┘
```

- All agentdata (status, heartbeat, tasks) kommer via Igris API
- Chattmeddelanden skickas som kontraktsvaliderade JSON
- Dashboarden är **read-only på agent-nivå** — den skickar commands via Igris, inte direkt till agenter

### 5.4 Modulär Arkitektur

```
┌─────────────────────────────────────────────┐
│  OVERWATCH CORE                               │
│  ├── Window Manager (flytta/ändra storlek)   │
│  ├── Module Registry (ladda/avlasta moduler) │
│  ├── Theme Engine (mörkt tema, pixel-stil)   │
│  └── Igris API Client (WebSocket connector)  │
│                                                │
│  ── Installerade Moduler ──                    │
│  ├── ThroneRoom       (huvudvy, dungeon)      │
│  ├── AgentList        (listvy)                │
│  ├── AgentDetail      (popup / overlay)       │
│  ├── TheGate          (chattfönster)          │
│  ├── MemoryVault      (minnes-integration)    │
│  ├── SystemStatus     (telemetri)             │
│  ├── DependencyGraph  (beroenden)             │
│  └── Benchmarks       (prestanda-grafer)      │
└─────────────────────────────────────────────┘
```

Varje modul är en egen komponent som kan laddas dynamiskt, placeras fritt (dra & släpp), och stängas/återöppnas från menyraden.

---

## 6. IMPLEMENTATIONSFASER

### Fas 1: Prototyp

- [ ] Grundläggande Tauri-app med mörkt tema
- [ ] Enkel dungeon-bakgrund (CSS-gradient + pixel-mönster)
- [ ] Throne Room med Igris (statisk pixel-figur)
- [ ] Några agent-gubbar (olika färger per rank)
- [ ] Klick → Agent Detail-popup med mock-data
- [ ] WebSocket-anslutning till Igris (för live-status)

### Fas 2: Interaktiv

- [ ] The Gate — chattfönster (multi-tab)
- [ ] Live agent-status (heartbeat → animation)
- [ ] Agent List-vy med full info
- [ ] Rank-crowns och glow-effekter
- [ ] Memory Vault — visa Brain.md / Memory.md från fil
- [ ] Notiscenter + level-up firande

### Fas 3: Komplett

- [ ] Dra & släpp moduler
- [ ] Quest Log (RPG-stil task backlog)
- [ ] Benchmark-grafer
- [ ] System Status-telemetri
- [ ] Dependency Graph
- [ ] Pixel-art spritesheets (custom per agent-domän)
- [ ] Tron-animation (Igris "andas", blick rör sig)

### Fas 4: Polering

- [ ] Ljud (dungeon-ambience, UI-klick, level-up fanfar)
- [ ] Solo Leveling-estetik (partikeleffekter, glöd)
- [ ] Övergångar mellan skärmar (fade, slide)
- [ ] Obsidian deep-link integration
- [ ] Inställnings-modul (alla toggle options)
- [ ] Onboarding-flöde för nya användare
- [ ] System tray + minimering

---

## 7. ÖPPNA FRÅGOR

1. **Vem ritar pixel-gubbarna?** AI-genererat? Färdiga sprites? Proceduralt med CSS/SVG?
2. **Ska agenterna ha unika utseenden** baserat på domän — eller alla samma bas med olika färg?
3. **Chatt-loggar** — sparas lokalt i dashboarden, i Igris minne, eller i Obsidian?
4. **Hur mycket ska man kunna styra från dashboarden?** Bara läsa? Skicka commands? Ändra rank manuellt?
5. **Tronen** — tom när Igris är offline, eller alltid upptagen?

---

## 8. FORSKNING — Vad Finns Där Ute

Jag undersökte tre kategorier: (1) AI agent-dashboards, (2) multi-agent visualiseringar, (3) RPG/game-style developer tools.

### 8.1 Existerande AI Agent-Dashboards

| Verktyg | Typ | Styrkor | Svagheter | Lärdom för Overwatch |
|---|---|---|---|---|
| **AutoGen Studio** (Microsoft) | Open-source UI | Visuell agent-builder, workflow-komposition | Research-prototyp, ingen estetik | **Modul-idé:** "Flow View" med task-beroenden |
| **LangSmith Studio** (LangChain) | Kommersiell IDE | "Time travel" debugger, djup tracing, state inspector | Proprietär, kostar. Generisk design | **Måste-ha:** Time travel — kliv bakåt i agentexekvering |
| **LangGraph Studio** | Desktop IDE | Node-by-node graffinspelning, state machine | Kräver LangGraph | **Inspo:** Se agentberoenden som graf |
| **CrewAI Enterprise** | Kommersiell | RBAC, deployment pipelines, team management | Dashboard paywalled | **Inspo:** Rollbaserad vy per specialisering |
| **Dify** | Open-source | Full dashboard, analytics, conversation logs | Generisk UI | **Inspo:** Analytics — task-rate, tokens, latency |

**Huvudslutsats:** Inget av dessa verktyg har en visuell identitet eller estetik. **Overwatch är unikt i sin RPG/Solo Leveling-estetik.** Det är en enorm differentiering.

### 8.2 Multi-Agent Visualiseringstekniker

| Teknik | Används av | Beskrivning |
|---|---|---|
| **Directed graph** | LangGraph, AutoGen | Agenter som noder, meddelanden som kanter |
| **Hierarki-träd** | CrewAI | Manager → Worker, bra för Igris som Commander |
| **State machine** | LangGraph | Tydlig visualisering av agenters tillstånd |
| **Message flow** | AutoGen Studio | Realtids-tracing av inter-agent meddelanden |

**För Overwatch:** Kombinera hierarki-träd (Igris i toppen) med state indicators (idle/active/error) — ingen annan dashboard gör detta med dungeon-throne-visual.

### 8.3 RPG/Game-Style Developer Tools

| Projekt | Lärdom |
|---|---|
| **Habitica** | Gamification fungerar för produktivitet. Tasks = quests. Level-ups = rank-ökning. |
| **NES.css** (github) | 8-bit CSS-ramverk — pixel-kanter, retro-font. Kan bootstrapa estetiken gratis. |
| **RPGUI** (github) | Health bars, inventory, dialog-boxes. Health bars → agent performance bars. |
| **Solo Leveling UI replikor** (Dribbble) | Stat blocks (STR/AGI/INT) → agent attributes. Många designers har återskapat stilen. |

### 8.4 Konkreta Förbättringsförslag

- **Time Travel Debugger** — kliv bakåt i agentexekvering (inspo: LangSmith)
- **Agent Dependency Graph** — kedjor mellan agenter som väntar på varandra
- **RPG Character Sheet** — STR/AGI/INT/VIT istället för generiska grafer
- **S-Rank Mentorskap** — länkad kedja mellan mentor och lärling
- **Quest Log** — tasks som "Main Story / Side / Daily / Event"
- **Dream Sequence** — nattlig minneskonsolidering som animation

### 8.5 Overwatch Unika Fördelar

1. Solo Leveling-estetik — ingen agent-dashboard har försökt detta
2. Throne Room — andra visar agenter som listor, Overwatch visar dem i en värld
3. Brain.md / Memory.md synliga som markdown-filer
4. The Gate — prata med varje agent direkt (de flesta dashboards är read-only)
5. S-Rank mentorskap som visuella relationer

---

## 9. PIXEL-ART SPEC & ANIMATIONER

### 9.1 Agent Figurerna

Varje agent är en pixel-art figur renderad i **16×16 eller 24×24 pixlar**, uppskalad ×3 eller ×4 för skärmen.

**Silhuett per domän:**

| Domän | Silhuett | Look |
|---|---|---|
| Backend/Python | Kappa-klädd figur med bok | Scribe/mathematician |
| Frontend/JS | Figur med sköld (UI) | Shield-bearer |
| DevOps/Infra | Figur med nyckel & växlar | Tinker/engineer |
| Testing/QA | Figur med förstoringsglas | Detective |
| Data/ML | Figur med kristallkula | Mage |
| Generalist | Enkel äventyrare | Basic adventurer |
| **Igris** | Commander i rustning + mantel, på tron | Självklar |

**Animationer (idle-loop):**

| Status | Animation |
|---|---|
| **Idle** | Står stilla, blinkar var 4e sek. Andningsrörelse (1-2 px) |
| **Active** | Lätt bobbing (studs), "blick" som rör sig framåt |
| **Thinking** | Hand mot hakan, "..." ovanför huvudet |
| **Working** | Verktyg i handen, små sparkles |
| **Blocked** | Röd ton, kedja från foten |
| **Error** | Röd blinkning, utropstecken ovanför |
| **Sleeping** | Liggande, Zzz ovanför |
| **Level Up** | Partikeleffekt, växer 10%, crown flash |

### 9.2 Igris Commander Specs

- **Storlek:** ~30×30 pixlar (25% större än en 24×24 agent)
- **Tron:** ~40×30 pixlar, stenliknande med glödande kanter
- **Animation (idle):** Igris sitter stilla, manteln fladdrar. Då och då en "order"-gest
- **När han pratar:** Tronen glöder starkare, Igris lutar sig framåt
- **Offline:** Tronen syns som tom kontur

### 9.3 Färgpalett — Solo Leveling Darkness

```
Bakgrund:         #0a0a12  (väggar), #12121e (golv), #1a1a2e (dimma)
Accenter:         #00d4ff  (cyan/System), #7b2d8e (lila portal)
                  #ffd700  (guld/S-Rank/Igris), #ff4444 (röd/error)
                  #44ff44  (grön/active/success)
Rank-färger:      E:#666, C:#4c4, B:#48f, A:#94f, S:#fd0+guldglow
                  SS:#c0cfff+silverglow, SSS:#f44→#fd0 gradient+mytiskglow
```

### 9.4 Bakgrundsdetaljer

Throne Room-bakgrunden har lager:
- **L0:** Solid #0a0a12
- **L1:** Tegel/textur-mönster (repetitiv pixel-art, låg opacity)
- **L2:** Dungeon-pelare på sidorna
- **L3:** "Mist" — långsam CSS-animation, #1a1a2e med opacity
- **L4:** Ljuskälla bakom tronen (pulserar svagt)
- **L5:** Agenter + Igris (renderas överst)

---

## 10. THE GATE — DJUPGÅENDE

### 10.1 Multi-Tab Arkitektur

The Gate stödjer flera samtidiga konversationer som tabs:

```
┌─────────┬──────────┬──────────┬─────────┬──────┐
│ Igris   │ Agent-X  │ Agent-Y  │ System  │  +   │
├─────────┴──────────┴──────────┴─────────┴──────┤
│                                                 │
│  [Igris 12:34] Morgonplan för idag:             │
│  1. Granska Agent-X's OAuth2-patch              │
│  2. Träna Agent-Z i linting                     │
│                                                 │
│  ┌────────────────────────────────────────────┐ │
│  │ @Igris Vad tycker du om Agent-Xs           │ │
│  │ OAuth2-implementation?                     │ │
│  └────────────────────────────────────────────┘ │
│  [Skicka]  [@välj mottagare ▼]                  │
└──────────────────────────────────────────────────┘
```

- Tabs färgkodas: Igris=guld, Agent=rank-färg, System=cyan
- `@Agent-X` i valfri tab nämner en annan agent
- Historik sparas i lokal SQLite — scrolla hur långt som helst

### 10.2 Meddelandeformat

Stödjer: **bold**, `code`, ```code block```, > quote, [länkar](obsidian://...). Timestamp relativ (2m ago) eller absolut (12:34) vid hover.

### 10.3 Avsändarfärger

| Avsändare | Färg |
|---|---|
| Användaren | #fff |
| Igris | #ffd700, [Commander]-prefix |
| Agent (A/S+) | #9944ff (lila) |
| Agent (B/C) | #4488ff (blå) |
| Agent (E) | #666 (grå) |
| The System | #00d4ff (cyan), [System]-prefix |
| Systemmeddelande | #ff8800 (orange) |

### 10.4 Kommandon

| Kommando | Effekt |
|---|---|
| `/msg Agent-X text` | Skicka till specifik agent |
| `/broadcast text` | Skicka till alla agenter |
| `/task Agent-X bygg detta` | Skapa TaskAssignment från chatten |
| `/rank Agent-X` | Visa full rank-historik |
| `/status` | Visa systemstatus |
| `/search OAuth2` | Sök i alla Brain.md/Memory.md |
| `/help` | Lista alla kommandon |

---

## 11. NOTISER & FIRANDE

### 11.1 Notiscenter

En klocka-ikon i menyraden: `🔔 (3)`. Notistyper:

| Typ | Prioritet | Varaktighet |
|---|---|---|
| Level Up | Hög | 8s + confetti |
| Task Complete | Medium | 5s |
| Error | Hög | Kvar tills läst |
| Morning Plan | Medium | 5s |
| Benchmark Done | Låg | 3s |
| Memory Consolidation | Låg | 3s |

### 11.2 Rank-Up Ceremoni

När en agent rankar upp: alla agenter vänder sig mot den rank-upande → agenten lyser i ny rank-färg → partikeleffekt (stjärnor) → "LEVEL UP!"-text → Igris nickar → efter 3s återgår allt.

### 11.3 System Tray

Dashboarden minimeras till system tray med Igris pixel-ansikte som ikon. Tooltip: "Igris — 4 agents aktiva, 3 tasks pending". Högerklicka → meny: Open, Sleep Mode, Quit.

---

## 12. ONBOARDING — Första Gången

När Overwatch öppnas första gången (ingen Igris-anslutning):

```
┌─────────────────────────────────────────────┐
│         ╔══════════════════════╗             │
│         ║    OVERWATCH          ║             │
│         ║    COMMAND CENTER     ║             │
│         ╚══════════════════════╝             │
│   En tom Throne Room. Bara tronen syns.      │
│   [Anslut till Igris]  [Demo Mode]           │
└─────────────────────────────────────────────┘
```

Efter anslutning: intro-animation (agenter walk in från sidorna), overlay med "Välkommen. Igris har N agenter.", tooltips på UI-element första 3 gångerna.

---

## 13. INSTÄLLNINGAR

### 13.1 Visuellt

| Inställning | Default | Alternativ |
|---|---|---|
| Theme | Solo Leveling (dark) | Dark, Nord, Terminal Green |
| Pixel scale | ×3 | ×2, ×3, ×4 |
| Agent animation | On | Off, Reduced |
| Particle effects | On | Off |
| Dungeon background | On | Off |

### 13.2 The Gate

| Inställning | Default |
|---|---|
| Auto-open on mention | On |
| Message history limit | 1000 |
| Sound on message | Off |

### 13.3 Notiser

| Inställning | Default |
|---|---|
| Level Up notification | On |
| Task Complete | On |
| Error | On (always) |
| Morning Plan | On |
| Sound on notification | Off |
| Minimize to tray on close | Off |

### 13.4 Tangentbordsgenvägar

| Genväg | Funktion |
|---|---|
| `Ctrl+1-9` | Växla tab i The Gate |
| `Ctrl+T` | Ny tab |
| `Ctrl+K` | Kommandopalett |
| `Esc` | Stäng overlay |
| `F5` | Refresh agent status |
| `Ctrl+,` | Inställningar |
| `Ctrl+Shift+D` | Dependency Graph |
| `Ctrl+Shift+M` | Memory Vault |
| `Ctrl+Shift+B` | Benchmarks |
| `?` | Visa kortkommandon |

---

## 14. AGENT-DEPENDENCY GRAPH

En hel skärm dedikerad till att visualisera agentberoenden som en riktad graf.

- **Noder** = agenter, storlek baserad på rank
- **Kanter** = beroenden (A väntar på B → pil från B till A)
- **Röda kanter** = blockerande beroenden
- **Gröna kanter** = aktiva, flytande
- Klick på nod → öppnar Agent Detail
- Zoom/Pan

```
         ┌──────┐
         │IGRIS │
         └──┬───┘
     ┌──────┼──────────┬──────────┐
     ▼      ▼          ▼          ▼
  ┌────┐ ┌────┐    ┌────┐     ┌────┐
  │A-X │ │A-Y │    │B-Z │     │C-W │
  │80% │ │45%→│    │100%│     │ 0% │
  └─┬──┘ └────┘    └────┘     └─┬──┘
    ▼ waiting                  ▼ waiting
  ┌────┐                     ┌────┐
  │B-Q │                     │E-R │
  │10% │                     │PEND│
  └────┘                     └────┘
```

---

## 15. FRAMTIDA EXPANSION

### 15.1 Mobil Companion

Minimalistisk mobilvy: agent count + status, push-notiser vid level-ups/errors, snabb-chatt med Igris. Ej full Throne Room.

### 15.2 Plugin-API

Moduler kan byggas av tredje part:

```typescript
const customModule = {
  id: "my-module",
  name: "My Module",
  icon: "✨",
  render: (container, igrisApi) => { /* bygg UI */ }
}
```

### 15.3 Export Layout

Spara/återställ layout som JSON: vilka moduler, position, storlek. Dela med andra.

```json
{
  "theme": "solo-leveling-dark",
  "pixelScale": 3,
  "modules": {
    "throne-room": { "x": 0, "y": 0, "w": 600, "h": 400, "visible": true },
    "the-gate":    { "x": 620, "y": 0, "w": 400, "h": 400, "visible": true }
  }
}
```

---

*Detta dokument uppdateras när visionen förfinas. Senaste uppdatering: 2026-06-19. 15 sektioner.*