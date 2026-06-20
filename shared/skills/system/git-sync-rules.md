# Git Sync Rules — hosted-aiOS

> Vattentäta regler för synk mellan tre datorer.

## Grundregler

1. Pull före push. Alltid.
2. Stash före pull.
3. Använd `git pull --rebase`.
4. Aldrig `git push --force`.
5. Aldrig `git reset --hard`.

## Konflikter

- Spara båda versionerna med timestamp
- Skapa konfliktfil: `filnamn.md.CONFLICT-YYYY-MM-DD-HHMMSS.md`
- Logga till `shared/memory/REASONING_BANK.md`
- Meddela Hermes

## Loggning

- Logga varje synkoperation
- Notera stash-status, pull-resultat och eventuella konflikter

## Robusthet

- Pusha bara när lokala ändringar finns
- Återställ stash efter lyckad pull
- Avbryt och rapportera vid korrupt `.git` eller misslyckad stash pop
