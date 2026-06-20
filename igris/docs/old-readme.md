# The System — Commander Igris Ecosystem

> **Mottagare:** William
> **Syfte:** Komplett översikt av Igris ekosystem — plan, kod och dashboard
> **Senast uppdaterad:** 2026-06-20

---

## Vad är detta?

The System samlar ALLT relaterat till Commander Igris — ett självutvecklande multi-agent AI-ekosystem. Här finns:

1. **Den fullständiga systemplanen** — Igris identitet, arkitektur, beteenderegler
2. **Den fungerande kodbasen** — Phase 1: GPU-manager, kontraktsvalidering, orchestrator, router
3. **Dashboard-planen** — Overwatch: Solo Leveling-stil GUI för att övervaka agenterna

---

## Filstruktur

```
C:\The System\
│
├── README.md                          ← DU ÄR HÄR
├── lastsession.md                     ← Förra sessionens sammanfattning (läs först!)
│
├── Igris\                             ← COMMANDER IGRIS — hjärnan
│   ├── Planer.md                      ← MASTERPLAN: Identitet, arkitektur, beteende (50 KB, 15 sektioner)
│   ├── SelfPlaner.md                  ← Igris personliga TODO (skapas vid startup)
│   │
│   └── src\                           ← FUNGERANDE KOD (Phase 1)
│       ├── __init__.py                ← Paketdefinition + version
│       ├── requirements.txt           ← Beroenden: pydantic, nvidia-ml-py, pyyaml
│       │
│       ├── core\                      ← Orchestrator, GPU Manager, Contract Validator
│       │   ├── orchestrator.py        ← Observe → Evaluate → Provision → Deploy loop
│       │   ├── gpu_manager.py         ← VRAM-övervakning via nvidia-ml-py (singleton)
│       │   ├── contract_validator.py  ← Pydantic-validering: 8 kontraktstyper + schema-register
│       │   └── __init__.py
│       │
│       ├── models\                    ← Pydantic-modeller
│       │   ├── agent.py              ← Agent, AgentRank (E→SSS), AgentStatus
│       │   ├── task.py               ← Task, TaskPriority, TaskStatus
│       │   ├── hardware.py           ← GPUAllocation, RAMAllocation, HardwareProfile
│       │   └── __init__.py
│       │
│       ├── cli\                       ← Kommandoradsgränssnitt
│       │   ├── main.py               ← python -m igris.cli.main [run|status|validate]
│       │   └── __init__.py
│       │
│       ├── prompts\                   ← Router-prompt för Llama 3.1 8B
│       │   ├── router_prompts.py      ← System prompt, observation builder, decision parser
│       │   └── __init__.py
│       │
│       ├── tests\                     ← Pytest-tester (körs grönt)
│       │   ├── test_gpu_manager.py    ← Singleton, VRAM-snapshot, allokering, OOM-risk
│       │   ├── test_contract_validator.py ← 8 kontraktstyper + edge cases
│       │   └── __init__.py
│       │
│       ├── config\                    ← Konfiguration
│       │   └── igris.yaml             ← VRAM-budget, hårdvara, agent-ranks, OOM-trösklar
│       │
│       └── data\                      ← Persisterad state
│           ├── agents.json            ← Agent-register
│           └── tasks.json             ← Task-kö
│
└── Overwatch\                         ← DASHBOARD GUI (planering)
    └── Dashboard-Plan.md              ← Solo Leveling-stil, Throne Room, The Gate
```

---

## Läsordning för William

1. **`lastsession.md`** — Sammanfattning av förra sessionen. Nyckelbeslut, användarpreferenser, hårdvarukonfiguration.
2. **`Igris\Planer.md`** — Den kompletta systemplanen (v1.2, 1057 rader). Läs hela — den definierar ALLT: identitet, arkitektur, dataflöde, agentlivscykel, minnessystem, beteenderegler.
3. **`Igris\src\`** — Bläddra i koden. Börja med:
   - `config/igris.yaml` — VRAM-budget och hårdvarukonfiguration
   - `core/orchestrator.py` — Huvudloopen (549 rader)
   - `core/contract_validator.py` — Kontraktsvalidering (249 rader)
   - `core/gpu_manager.py` — GPU/VRAM-manager (187 rader)
4. **`Overwatch\Dashboard-Plan.md`** — Dashboard-visionen (v0.2): Throne Room, pixel-art agenter, The Gate chatt

---

## Status just nu

| Komponent | Status |
|---|---|
| Igris Planer.md | ✅ v1.2 — komplett |
| Igris kod (Phase 1) | ✅ Fungerande — tester gröna |
| Overwatch plan | ✅ v0.2 — konceptuell |
| SelfPlaner.md | 🔄 Skapas av Igris vid startup |
| Phase 2 (Docker-agenter) | ⬜ Inte påbörjad |

---

## Hårdvara

| Komponent | Spec |
|---|---|
| GPU 1 | RTX 3090 24 GB — Qwen2.5-Coder-32B |
| GPU 2 | RTX 3080 10 GB — Router + Embeddings (framtida) |
| RAM | 64 GB DDR4 — KV-cache offloading (50 GB) |
| OS | Windows 10/11 |
| Python | 3.11+ |

### VRAM-budget (RTX 3090)

| Komponent | Allokerat |
|---|---|
| Qwen2.5-Coder-32B Q4_K_M | 19.0 GB |
| BGE-M3 embeddings | 1.2 GB |
| Overhead/slack | 2.0 GB |
| **VRAM totalt** | **22.2 GB / 24 GB** |

KV-cache (64K context) offloadas till system-RAM (50 GB av 64 GB DDR4).

---

## Kommandon

```powershell
# Kör Igris orchestrator
cd "C:\The System\Igris\src"
$env:PYTHONPATH = "C:\The System\Igris\src"
python -m igris.cli.main run

# Visa status
python -m igris.cli.main status

# Validera kontraktsscheman
python -m igris.cli.main validate

# Kör tester
pytest tests/ -v
```

---

## Arkitektur i korthet

```
Observe (GPU/RAM/agents/tasks)
    ↓
Evaluate (Router: Llama 3.1 8B fattar beslut)
    ↓
Provision (Contract Validator bygger validerade kontrakt)
    ↓
Deploy (Utför: spawna agenter, tilldela tasks, befordra)
    ↓
[loopar var 30e sekund]
```

**Agent-ranks:** E → C → B → A → S → SS → SSS
- E-Rank: Entry, noll historik, basic tools
- B-Rank: Task-Ready, patchar under övervakning
- A-Rank: Expert, full tool access, multi-file refactors
- S-Rank: Mentor — kan summona egna lärlingar

**Agenter dör aldrig** — de rehabiliteras, reflekterar eller (i extrema fall) minnesrensas och återuppfostras.

---

*Sammanställt för William — redo att zippas.*
