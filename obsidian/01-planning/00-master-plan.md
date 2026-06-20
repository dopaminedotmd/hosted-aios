# hosted-aiOS — Master Plan v1.0
> Systemarkitektur för lokal LLM-server + fleranvändar-webapp + bot-orkestrering + Obsidian-vault + Git-synk.

**Status:** DRAFT — inväntar bot-granskning
**Skapad:** 2026-06-20 · Hermes
**Projektmapp:** `C:\Users\willi\Desktop\hosted-aios`
**Användare:** 3 pers (William + 2 vänner)

---

## 0. SYSTEMÖVERSIKT

```
                          INTERNET
                              |
                    +---------+---------+
                    |                   |
              [Mobil/PC]          [Mobil/PC]
           (Användare 2)      (Användare 3)
                    |                   |
                    +-------+-----------+
                            |
                    +-------v--------+
                    |  REVERSE PROXY |
                    |  (nginx/caddy) |
                    +-------+--------+
                            |
              +-------------+-------------+
              |                           |
    +---------v--------+       +----------v---------+
    |   WEB APP        |       |   OLLAMA SERVER    |
    |   (Next.js/?)    |       |   (port 11434)     |
    |   port 3000      |       |   lokal LLM        |
    +---------+--------+       +----------+---------+
              |                           |
              +-------------+-------------+
                            |
              +-------------v-------------+
              |    AI-OS FILSTRUKTUR      |
              |  C:\...\hosted-aios\      |
              +---------------------------+
```

### Komponenter

| Komponent | Syfte | Status |
|-----------|-------|--------|
| **Ollama** | Lokal LLM-inferens | Väntar på maskin-specs |
| **Web App** | Chat-UI + funktioner | Planeras i Fas 3 |
| **Reverse Proxy** | Exponera webapp + Ollama säkert | Fas 2 |
| **Obsidian Vault** | Gemensam kunskapsbas | Fas 1 |
| **Git Sync** | Synkronisera allt mellan 3 pers | Fas 1 |
| **Bot-system** | Hermes/Claude/Antigravity etc. | Fas 1 |
| **Skills-mapp** | Gemensamma + personliga skills | Fas 1 |

---

## 1. FILSTRUKTUR — hosted-aios/

```
hosted-aios/
│
├── README.md                          ← Systemöversikt + quickstart
├── SYSTEM_ARCHITECTURE.md             ← Detta dokuments slutversion
├── .gitignore                         ← Global ignore
├── .env.example                       ← Mall för miljövariabler
│
├── users/                             ← PERSONLIGA MAPPAR (3 st)
│   ├── william/
│   │   ├── README.md                  ← Installationsinstruktioner för Williams bottar
│   │   ├── bots/                      ← Williams bot-konfigurationer
│   │   │   ├── hermes/
│   │   │   │   └── persona.md
│   │   │   ├── claude-code/
│   │   │   │   └── CLAUDE.md
│   │   │   ├── antigravity/
│   │   │   │   └── persona.md
│   │   │   └── ... (opencode, shannon, codex)
│   │   ├── skills/                    ← Williams personliga skills
│   │   ├── memory/                    ← Williams bot-minnen
│   │   └── work/                      ← Williams pågående arbete
│   │
│   ├── user2/                         ← Samma struktur
│   │   ├── README.md
│   │   ├── bots/
│   │   ├── skills/
│   │   ├── memory/
│   │   └── work/
│   │
│   └── user3/                         ← Samma struktur
│       ├── README.md
│       ├── bots/
│       ├── skills/
│       ├── memory/
│       └── work/
│
├── shared/                            ← GEMENSAMMA RESURSER
│   ├── skills/                        ← ALLA bottar läser här
│   │   ├── SKILL_INDEX.md
│   │   ├── system/
│   │   │   ├── file-routing.md        ← VAR filer ska ligga
│   │   │   ├── naming-conventions.md  ← HUR filer namnges
│   │   │   ├── bot-protocol.md        ← Bot-kommunikationsregler
│   │   │   └── git-sync-rules.md      ← Synk-regler (vattentäta)
│   │   ├── coding/
│   │   │   ├── webapp-stack.md        ← (Fas 3)
│   │   │   └── api-design.md
│   │   └── ops/
│   │       ├── ollama-setup.md
│   │       ├── nginx-config.md
│   │       └── security.md
│   │
│   ├── memory/                        ← Gemensamma minnen (ADR:er, beslut)
│   │   └── REASONING_BANK.md
│   │
│   └── templates/                     ← Mallar för nya filer
│       ├── persona-template.md
│       ├── skill-template.md
│       └── plan-template.md
│
├── system/                            ← SYSTEMKÄRNA (skrivskyddad för bottar)
│   ├── RULES.md                       ← ÖVERORDNADE REGLER — ALLA bottar läser först
│   ├── BOT_REGISTRY.md               ← Alla bottar + deras roller
│   ├── PROTECTED_PATHS.md            ← Filer bottar ALDRIG rör utan OK
│   ├── GLOSSARY.md                    ← Gemensamma termer
│   └── agents/                        ← Bottarnas systeminstruktioner
│       ├── hermes.md
│       ├── claude-code.md
│       ├── antigravity.md
│       ├── opencode.md
│       ├── shannon.md
│       └── codex.md
│
├── obsidian/                          ← OBSIDIAN VAULT (synkas via Git)
│   ├── .obsidian/                     ← Obsidian-konfig (delad)
│   ├── 00-dashboard.md               ← Huvudvy — projektstatus
│   ├── 01-planning/                   ← ALLA planer
│   │   └── (planer organiserade efter fas)
│   ├── 02-decisions/                  ← ADR:er
│   ├── 03-meetings/                   ← Mötesanteckningar
│   ├── 04-research/                   ← Research, teknik-spaning
│   ├── 05-building/                   ← Byggloggar, status
│   ├── 06-personal/                   ← Personliga anteckningar (undermapp/user)
│   │   ├── william/
│   │   ├── user2/
│   │   └── user3/
│   └── templates/                     ← Obsidian-mallar
│
├── webapp/                            ← (Fas 3 — webbapp-kod)
│   └── README.md                      ← Placeholder
│
├── server/                            ← Serverkonfiguration
│   ├── ollama/
│   │   └── setup.sh
│   ├── nginx/
│   │   └── nginx.conf
│   └── docker/
│       └── docker-compose.yml         ← (om Docker används)
│
└── .hermes/                           ← Hermes interna planer (ignoreras av Git)
    └── plans/
```
