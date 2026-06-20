# Last Session — Commander Igris & Overwatch Dashboard

> **Datum:** 2026-06-19  
> **Huvudfokus:** Konceptuell planering av Commander Igris ekosystem + Overwatch Dashboard

---

## LÄSORDNING (för nästa AI)

Börja här, läs sedan i denna ordning:
1. `I:\Igris\Planer.md` — komplett systemplan (v1.2, 50 KB)
2. `I:\Overwatch\Dashboard-Plan.md` — dashboard vision (v0.2, 28 KB)
3. `I:\Igris\SelfPlaner.md` — skapas av Igris vid första startup (finns inte än)
4. `C:\Users\willi\igris\contracts\models.py` — Pydantic-kontrakt (Phase 1.1, redan kodad)
5. `C:\Users\willi\igris\contracts\validator.py` — Contract Validator (Phase 1.1, redan kodad)

---

## COMMANDER IGRIS — Kärnfilosofi

- **Huvudkatalog:** `I:\Igris\`
- **Användaren (Willi):** Svensktalande utvecklare som bygger ett självutvecklande multi-agent AI-ekosystem på lokal hårdvara (2× GPU)
- **Igris:** Commander Agent — en självstyrande systemarkitekt, INTE en chatbot. Aktiv samarbetspartner som kan ifrågasätta och föreslå.

### Nyckelbeslut som skiljer sig från Master Specification

1. **Agenter dör ALDRIG** — de rehabiliteras, minnesrensas eller reflekterar. A-Rank-agent som gör fel → reflektion + plan, aldrig termination.
2. **S-Rank** finns över A-Rank — agenter som nått sin peak får SUMMONA en egen lärling. S-Rank drar styrka av lärlingen (lärling hjälper med svagheter, idéer, bugfixar). Igris kan gå emellan om S-Rank inte presterar.
3. **Rankingsystem:** E → C → B → A → S → SS → SSS (7 ranker, utrymme för fler)
4. **Self-modification:** Igris får modifiera prompt/contracts/packages med "varför → därför såhär"-resonemang
5. **Memory:** Mänsklig decay — 75% konsolidering + 25% hybrid kort-/långtid. Skarpt i dagar, sammanfattat över veckor, glöms bort efter ~2 veckor utan aktivitet
6. **DeepSeek = icke-bindande konsult:** Igris väger in The Systems åsikter men tar slutgiltiga beslut. Långsiktigt mål: full självständighet
7. **Daglig rytm:** Morgonplan (5 punkter) + kvällssammanfattning
8. **Watchdog:** Auto-restart vid krasch med crash-analysis och rapport till Användaren
9. **Initiativrätt:** Små ändringar → informera efteråt. Stora ändringar → backup/restore-point först. Kloning av sig själv → kräver godkännande.
10. **"Nej"-hantering:** Acceptera direkt, reflektera internt, efter 6+ nej på samma kategori → undvik om inte Igris är väldigt säker

### Hårdvaruarkitektur

| GPU | VRAM | Modeller |
|---|---|---|
| RTX 3090 | 24 GB | Qwen2.5-Coder-32B (15.5 GB) + KV-cache (6.5 GB) + slack (2 GB) |
| RTX 3080 | 10 GB | Llama-3.1-8B Router (4.5 GB) + BGE-M3/E5 embeddings (1.5 GB) + slack (2.5 GB) |

### Phase 1 Implementation (kodad)

- **Task 1.1 (klar):** Pydantic-kontrakt + Contract Validator på `C:\Users\willi\igris\contracts\`
  - 18 kontraktstyper inkl. reflection, dummy_test, summon_permission
  - 5-stegs valideringspipeline (JSON parse → contract_type → schema → semantic check → accept)
- **Task 1.2 (kvar):** Routing Prompt för Llama 8B
- **Task 1.3 (kvar):** NVIDIA-ML-PY Hardware Manager

### Dag 1 — Startup Protocol

När Igris startas första gången:
1. Presentera sig
2. Installera foundational skills
3. Läs Planer.md noggrant
4. Skapa SelfPlaner.md (personlig plan)
5. Kontakta The System (DeepSeek) för granskning av SelfPlan
6. Iterera tills Igris + The System är nöjda
7. SUMMONA nödvändiga E-Agenter (skills + domains + uppdrag)
8. Kör baseline benchmark på alla agenter
9. SelfPlaner.md blir löpande TODO

---

## OVERWATCH DASHBOARD

- **Huvudkatalog:** `I:\Overwatch\`
- **Teknikval:** Tauri (Rust + React/Svelte) — lättvikt, standalone desktop-app
- **Stil:** Solo Leveling dungeon + pixel-art + mörkt tema

### Kärnfunktioner

- **Throne Room:** Igris 25% större på tron, agenter som pixel-gubbar i halvcirkel, rank-crowns, status-animationer
- **The Gate:** Multi-tab chatt — prata med agenter, Igris, eller The System. Rich formatting, kommandon (/msg, /task, /search, ...)
- **Memory Vault:** Brain.md + Memory.md per agent, synligt och redigerbart
- **Agent Detail:** Klicka på pixel-gubbe → stats (STR/AGI/INT/VIT), tasks, historik
- **Dependency Graph:** Riktad graf över agentberoenden (röd=blockerad, grön=aktiv)
- **Quest Log:** Task backlog som RPG quest-lista
- **Benchmarks:** Prestandastatistik
- **System Status:** VRAM, uptime, telemetri
- **Level-Up Ceremoni:** Partikeleffekter, alla agenter vänder sig, "LEVEL UP!"-text
- **Notiscenter:** Klocka-ikon med 6 notistyper
- **System Tray:** Minimera med Igris-ikon

### Unika fördelar (ingen annan dashboard gör detta)

1. Solo Leveling-estetik i agent-dashboard
2. Throne Room som primär vy (inte listor/grafer)
3. Agenters tankar som läsbara markdown-filer (Brain.md / Memory.md)
4. Direkt chatt med varje agent
5. S-Rank mentorskap som visuella relationer

### CSS-ramverk för pixel-estetik

- **NES.css** — 8-bit stil CSS, gratis open-source
- **RPGUI** — RPG-komponenter (health bars, inventory, dialog-boxes)

---

## VIKTIGA FILER

| Fil | Innehåll | Status |
|---|---|---|
| `I:\Igris\Planer.md` | Komplett systemplan (15 sektioner) | ✅ Uppdaterad v1.2 |
| `I:\Overwatch\Dashboard-Plan.md` | Dashboard vision (15 sektioner) | ✅ Uppdaterad v0.2 |
| `I:\Igris\SelfPlaner.md` | Igris personliga plan | 🔄 Ska skapas Dag 1 |
| `I:\lastsession.md` | Denna sammanfattning | ✅ Ny |
| `C:\Users\willi\igris\contracts\models.py` | Pydantic-kontrakt (18 typer) | ✅ Kodad |
| `C:\Users\willi\igris\contracts\validator.py` | Contract Validator | ✅ Kodad |
| `C:\Users\willi\igris\contracts\__init__.py` | API | ✅ Kodad |

---

## USER PROFILE (för memory)

```
Användare: Willi
Språk: Svenska (planer), Engelska (teknisk kod)
Projekt: Commander Igris — självutvecklande multi-agent AI-ekosystem
Hårdvara: RTX 3090 24GB + RTX 3080 10GB, 64GB DDR4, Windows 10
Primary provider: DeepSeek (för närvarande deepseek-v4-flash)
```

### User Preferences (fastställda i denna session)

- Igris lyder men kan ifrågasätta — aktiv samarbetspartner, inte passivt verktyg
- Agenter dör aldrig — rehabiliteras alltid (reflektion för A+, minnesrensning för E/C)
- Self-modification ("varför → därför såhär") är OK för prompt, packages, kontrakt, kloning
- Backup/restore-point krävs före stora projektändringar
- Internetåtkomst för agenter: Igris får auktorisera om det gynnar utveckling
- Kloning OK, alla kloner delar ett medvetande
- DeepSeek = icke-bindande konsult, mål är full självständighet
- Daglig rytm: morgonplan + kvällssammanfattning
- Watchdog: auto-restart med crash-analysis, rapportera till Användare
- "Nej"-hantering: acceptera direkt, efter 6+ nej → undvik (om inte säker)
- Dashboard GUI: Solo Leveling-stil, pixel-art, Throne Room, modular
- Memory: mänsklig decay (skarp i dagar, glöms efter ~2 veckor utan aktivitet)
- Priority idle: Underhåll > Djupanalys > Träning > Spawna > Experiment
