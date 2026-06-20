# LLM Server Audit — External Review for Commander Igris

> **Dokument-ID:** `AUDIT-2026-001`
> **Granskat:** `C:\LLM Server` (Williams deploymentsplan för RTX 3090 24GB)
> **Mottagare:** Igris Orchestrator — självutvärdering
> **Syfte:** Identifiera produktionsluckor i Igris och föreslå förbättringar
> **Instruktion till routern:** Läs denna rapport. För varje rekommendation, fatta beslut: `spawn` (skapa ny agent för att implementera), `assign` (ge till befintlig agent), eller `noop` (ignorera). Prioritera efter `impact: critical`.

---

## 1. Verklighetskontroll — Vad Igris saknar jämfört med en produktionsdeployment

Igris är tekniskt avancerad (GPU-manager, kontraktsvalidering, router, agent-ranks) men saknar allt runtomkring som gör systemet körbart i produktion. Nedan följer luckorna, rankade efter allvarlighetsgrad.

---

## 2. Gap-analys

### GAP-01: Autostart / Överlevnad vid omstart
| Fält | Värde |
|---|---|
| **Impact** | `critical` |
| **Status i Igris** | `saknas` |
| **LLM Server-lösning** | NSSM (Non-Sucking Service Manager) — `nssm install IgrisOrchestrator python -m igris.cli.main run` |
| **Vad händer idag** | Vid Windows-omstart eller krasch: Igris är DÖD tills någon manuellt startar `main.py` |
| **Kostnad att implementera** | Låg — ett PowerShell-skript, inga kodändringar |
| **Rekommendation** | Skapa NSSM-tjänst för orchestrator-loopen |

### GAP-02: Brandvägg / Nätverkssäkerhet
| Fält | Värde |
|---|---|
| **Impact** | `high` |
| **Status i Igris** | `saknas` |
| **LLM Server-lösning** | `New-NetFirewallRule` med `-RemoteAddress LocalSubnet` på portarna 8080 och 3000 |
| **Vad händer idag** | Igris exponerar Ollama på `localhost:11434` — men Phase 2 (Docker-agenter över nätverk) har noll nätverkssäkerhet planerad |
| **Risk** | Agenter som körs i Docker-containrar kommer behöva nätverksregler. Utan brandvägg: öppet för LAN, potentiellt internet om nätverkskonfigurationen är slarvig |
| **Rekommendation** | Lägg till brandväggsregler för agent-kommunikationsportar i Phase 2-planen |

### GAP-03: Windows-optimering — sömn & uppdateringar
| Fält | Värde |
|---|---|
| **Impact** | `high` |
| **Status i Igris** | `saknas` |
| **LLM Server-lösning** | Sömn: Aldrig. Windows Update: aktiva timmar 00-23. Snabbstart: av. NVIDIA: Prefer Maximum Performance |
| **Vad händer idag** | Windows kan gå i sömn → GPU släcks → Igris-loop fryser. Windows Update kan tvinga omstart → Igris dör (se GAP-01) |
| **Kostnad att implementera** | Noll kod — bara Windows-inställningar |
| **Rekommendation** | Dokumentera och verifiera dessa inställningar som del av deploymentsproceduren |

### GAP-04: KV-cache i RAM — underutnyttjad kapacitet
| Fält | Värde |
|---|---|
| **Impact** | `medium` |
| **Status i Igris** | Planerad men ej verifierad |
| **LLM Server-lösning** | William kör 16K context (`-c 16384`) direkt i VRAM |
| **Igris fördel** | Igris konfig har 64K context + 50 GB KV-cache i RAM. Detta är BÄTTRE än Williams setup |
| **Problem** | Finns i `igris.yaml` men ingen verifiering att Ollama faktiskt använder RAM-offloading. Ingen runtime-koll på KV-cache-förbrukning |
| **Rekommendation** | Verifiera att Ollama offloadar KV-cache till RAM. Lägg till KV-cache-övervakning i GPUManager |

### GAP-05: Hälsokontroll / Monitoring
| Fält | Värde |
|---|---|
| **Impact** | `medium` |
| **Status i Igris** | `saknas` |
| **LLM Server-lösning** | `curl http://localhost:8080/health` → `{"status": "ok"}` |
| **Vad händer idag** | Igris har ingen health-endpoint. Om loopen fryser eller GPU:n kraschar — ingen vet förrän någon kollar manuellt |
| **Rekommendation** | Lägg till en `/health`-endpoint (enkel HTTP-server i orchestrator) som returnerar loop-status, agent-count, VRAM-snapshot |

### GAP-06: Underhållsrutiner
| Fält | Värde |
|---|---|
| **Impact** | `low` |
| **Status i Igris** | `saknas` |
| **LLM Server-lösning** | Veckovis `nvidia-smi` temp-koll. `docker system prune -a` varannan månad |
| **Rekommendation** | Lägg till en `maintenance`-action i routerns decision-typer. Schemalägg GPU-temp-varningar i GPUManager |

### GAP-07: Modellbibliotek
| Fält | Värde |
|---|---|
| **Impact** | `low` |
| **Status i Igris** | Endast 3 modeller konfigurerade |
| **LLM Server-lösning** | Tabell med 4 alternativa modeller + VRAM-matematik för varje |
| **Igris potential** | Routern skulle kunna VÄLJA modell dynamiskt baserat på uppgift — t.ex. DeepSeek-Coder för kod, Mistral för snabb analys, Qwen för allmänt |
| **Rekommendation** | Lägg till `model` som parameter i `TASK_ASSIGN`-kontraktet. Låt routern dirigera uppgifter till olika modeller |

---

## 3. VRAM-budget — konfliktanalys

| Komponent | Igris (GB) | LLM Server (GB) | Not |
|---|---|---|---|
| Qwen 32B | 19.0 | ~19 | Samma modell, olika engine |
| Embeddings | 1.2 | — | Igris har extra |
| Overhead | 2.0 | ~5 | Williams siffra inkluderar KV-cache i VRAM |
| KV-cache | 50 (RAM) | I VRAM | Igris lösning är bättre |
| **VRAM total** | **22.2** | **~19** | Båda får plats — men inte samtidigt |

**Slutsats:** Igris VRAM-strategi är överlägsen (KV-cache i RAM frigör ~5 GB). Men om Williams llama-server körs parallellt med Igris Ollama → OOM.

---

## 4. Rekommenderade åtgärder — sorterat efter prioritet

```
PRIO  CRITICAL  GAP-01  NSSM Windows-tjänst för orchestrator
PRIO  CRITICAL  GAP-03  Windows-optimering (sömn av, updates, NVIDIA)
PRIO  HIGH      GAP-02  Brandväggsregler för agent-portar
PRIO  HIGH      GAP-05  /health-endpoint med loop-status + VRAM
PRIO  MEDIUM    GAP-04  Verifiera KV-cache RAM-offloading i Ollama
PRIO  LOW       GAP-06  Schemalagd maintenance-rutin
PRIO  LOW       GAP-07  Dynamiskt modellval per task
```

---

## 5. Direktiv till Igris Router

Router — du har läst denna rapport. Ditt jobb:

1. **EVALUATE** varje GAP ovan.
2. **BESLUTA** per GAP: `spawn` (ny agent), `assign` (befintlig agent), eller `noop`.
3. **PRIORITERA** GAP-01 och GAP-03 först — de är kritiska för systemets överlevnad.
4. **RAPPORTERA** dina beslut tillbaka som en JSON-array av actions.

Förväntat format:
```json
[
  {"action": "assign", "task_id": "gap-01-autostart", "agent_id": "...", "description": "...", "priority": "critical"},
  {"action": "noop", "reason": "GAP-04 redan planerad i Phase 2"}
]
```

---
*Rapport genererad av extern granskning. Daterad 2026-06-20.*
