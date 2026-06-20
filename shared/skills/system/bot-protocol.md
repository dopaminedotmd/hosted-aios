# Bot Protocol — hosted-aiOS

> Hur bottar kommunicerar med varandra. Delegering, granskning, loggning.

## DELEGERINGSKEDJA

```
Hermes → Kodande bot (OpenCode / Claude Code / Codex)
       → Bot bygger → Slutmeddelande
       → Hermes kopierar slutmeddelande
       → Antigravity granskar
       → Antigravity → Hermes: granskningsrapport
       → Hermes checkar av ELLER skickar tillbaka för fix
```

## SLUTMEDDELANDE-FORMAT

När en kodande bot är klar MÅSTE den skicka ett slutmeddelande med:
1. `[KLART]` prefix
2. Lista på ALLA skapade/ändrade filer (absoluta sökvägar)
3. Kort beskrivning av vad som gjordes
4. Eventuella problem eller avvikelser från planen

Exempel:
```
[KLART] Fas 0 Del 1 — Mappstruktur skapad.

Skapade mappar: 56 st
- C:\Users\willi\Desktop\hosted-aios\system\
- C:\Users\willi\Desktop\hosted-aios\users\william\...
[...]

Problem: inga.
Avvikelser från plan: inga.
```

## GRANSKNINGSPROTOKOLL

Antigravitys granskningsrapport MÅSTE innehålla:
1. Referens till planens delmål (t.ex. "Fas 0, delmål 0.1-0.5")
2. Godkänt / Varningar / Blockerare
3. Slutbedömning: GODKÄNT / GODKÄNT MED ÅTGÄRDER / UNDERKÄNT

## LOGGNING

Alla bottar SKA logga viktiga beslut till `shared/memory/REASONING_BANK.md`:
- Prefix: `[BOT-NAMN-AUTO]` för autonoma beslut
- Prefix: `[BOT-NAMN]` för planenliga åtgärder
- Format: `Datum Tid — Åtgärd — Orsak`

## KOLLISIONER

Om två bottar riskerar att arbeta på samma fil:
1. Den bot som upptäcker kollisionen → STOPPA
2. Logga till `REASONING_BANK.md` med `[KOLLISION]`
3. Meddela Hermes
4. Vänta på Hermes beslut
