# Commander Igris — The System

Autonom, sjalvutvecklande multi-agent AI-fabrik.
RTX 3090 24GB | Ryzen 9 3950X | 64GB DDR4 | qwen2.5-coder:32b

## Struktur

```
C:\LLM\
├── igris\                  # Huvudprojektet
│   ├── core\               # Orchestrator, Contract Validator, GPU Manager
│   ├── models\             # Agent, Task, HardwareProfile (Pydantic)
│   ├── skills\             # 776 agent skills
│   │   ├── caveman.py      # Caveman Ultra — kirurgiska patchar
│   │   ├── core\           # Caveman skills (7 st)
│   │   ├── superpowers\    # Superpowers skills (14 st)
│   │   ├── security\       # Cybersakerhetsskills (754 st)
│   │   └── agents\         # Agent-definitioner (3 st)
│   ├── cartographer\       # Repo-Cartographer — inkrementell skanner
│   ├── prompts\            # Routing Prompts for 8B-router
│   ├── cli\                # CLI (run, status, validate, map, idle)
│   ├── config\             # igris.yaml — full konfiguration
│   ├── tests\              # 83 tester
│   ├── desktop.py          # Desktop GUI-app (CustomTkinter)
│   └── idle_detector.py    # 15-min idle → Active Idle Mode
│
└── external\               # Klonade referens-repon
    ├── caveman\             # JuliusBrussee/caveman
    ├── superpowers\         # obra/superpowers
    ├── cybersecurity-skills\ # mukul975/Anthropic-Cybersecurity-Skills
    ├── nvidia-skills\       # NVIDIA/skills
    └── awesome-agent-skills\ # VoltAgent/awesome-agent-skills (1424+)
```

## Snabbkommandon

```bash
python C:\LLM\igris\desktop.py           # Desktop-app
python -m igris.cli.main status          # Systemstatus
python -m igris.cli.main validate        # Validera kontrakt
python -m igris.cli.main map <path>      # Scanna repo
python -m pytest C:\LLM\igris\tests\     # 83 tester
```

## Modeller (Ollama)

| Modell | Roll | Storlek |
|---|---|---|
| qwen2.5-coder:32b | Huvudmodell | 19 GB |
| llama3.1:8b | Router | 4.9 GB |
| bge-m3:latest | Embeddings | 1.2 GB |

## Faser

- **Fas 0** — Klar: Repo-Cartographer, idle-detektor, CLI
- **Fas 1** — Klar: Contract Validator, GPU Manager, Routing Prompts, Orchestrator
- **Fas 2** — Nasta: Docker Sandbox, Post-Write Hooks
- **Fas 3** — Planerad: Active Idle Training, syntetiska tester
