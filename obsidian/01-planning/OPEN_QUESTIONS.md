# Öppna Frågor — hosted-aiOS
> Beslutade: 2026-06-20. 8 av 10 frågor spikade.

---

## ✅ SPIKAT

### 1. Server-OS
**Beslut:** Ubuntu Server 24.04 LTS
**Varför:** Bäst GPU-stöd för Ollama/vLLM. Docker fungerar native. CUDA/ROCm stabilt.

### 2. Docker
**Beslut:** Ja — alla komponenter i containrar
**Varför:** Isolerade agenter med olika Trust Levels. Enkel backup/uppgradering. Resurskontroll per container.

### 3. Extern åtkomst
**Beslut:** Tailscale
**Varför:** Gratis mesh-VPN. Ingen port forwarding. Krypterat. Fungerar på mobil.

### 4. Autentisering
**Beslut:** JWT + lösenord först → OAuth senare
**Varför:** Enklast att implementera. OAuth kan läggas till utan att riva.

### 5. Ollama-modell
**Beslut:** Qwen2.5-Coder-32B (Q4_K_M) + Llama 3.1 8B
**Varför:** 3090 har 24GB VRAM. 32B (~20GB) för tung kodning. 8B (~6GB) för routing/lätta tasks.

### 6. Server-maskin
**Beslut:** RTX 3090 24GB VRAM
**Saknas:** RAM + CPU-specs

### 7. Git-host
**Beslut:** GitHub privat repo

### 8. Git-synk
**Beslut:** Cron var 5:e minut (pull+rebase)

---

## ❌ ÖPPET

### 9. Webbapp-framework
**Rekommendation:** Next.js
**Alternativ:** React + Express, Python/FastAPI
**Svar:**
> [Namn], [Datum]:
> 

### 10. Domän / URL
**Rekommendation:** Lokal Tailscale-IP + ev. `aios.local`
**Beror på:** Tailscale-konfigurationen
**Svar:**
> [Namn], [Datum]:
> 

---

## Notering: Igris-subsystem

"**Igris**" nämns som ett agent-orkestreringslager med:
- Trust Levels (Level 0 → A-Rank)
- Sandboxade Docker-containers per agent
- Commander Agent
- Separat planeringsfas: **Fas 5 — Igris** (efter Fas 0-4)

Igris är ett subsystem ovanpå hosted-aiOS — rör inte Fas 0-4.
