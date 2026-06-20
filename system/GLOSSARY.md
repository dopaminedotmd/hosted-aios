# GLOSSARY — hosted-aiOS

> Gemensamma termer. Alla bottar + användare använder samma språk.

| Term | Definition |
|------|-----------|
| **hosted-aiOS** | Projektets namn. Det delade AI-operativsystemet. |
| **LLM** | Large Language Model. AI-modellen som körs i Ollama. |
| **Ollama** | Programvara som kör LLM:er lokalt. API på port 11434. |
| **Reverse proxy** | Nginx/Caddy. Tar emot HTTPS-trafik → vidarebefordrar till rätt intern tjänst. |
| **Obsidian** | Markdown-baserad anteckningsapp. Er vault = `obsidian/`. |
| **Vault** | En mapp med .md-filer som Obsidian öppnar som kunskapsbas. |
| **Bot / Agent** | En AI-assistent med en specifik roll (Hermes, Claude Code, etc.). |
| **Skill** | En .md-fil i `shared/skills/` eller `users/<namn>/skills/`. Instruerar en bot hur den utför en specifik uppgift. |
| **Persona** | En bots identitetsfil (`persona.md` eller `CLAUDE.md`). Styr botens röst, regler, beteende. |
| **ADR** | Architecture Decision Record. Dokumenterar ett tekniskt beslut + varför. |
| **Delegering** | När Hermes skickar en uppgift till en kodande bot. |
| **Granskning** | När Antigravity analyserar en bots output och jämför med planen. |
| **Fas** | En av 5 faser i masterplanen (0=Foundation, 1=Obsidian+Sync, 2=Server, 3=Webapp, 4=Orkestrering). |
| **Check-av** | När Hermes markerar ett delmål som slutfört efter godkänd Antigravity-granskning. |
| **Cron** | Schemaläggare. Kör synk-skriptet var 5:e minut. |
| **Git-synk** | Automatisk synkronisering av filer mellan 3 datorer via GitHub + cron. |
| **Vattentät** | Noll risk för filförlust. Alltid spara båda versioner vid konflikt. |
