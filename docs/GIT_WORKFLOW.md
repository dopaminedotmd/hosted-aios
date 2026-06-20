# Git Workflow — Commander Igris

> Gäller ALLA utvecklare. Ingen pushar direkt till main. Någonsin.

---

## 1. Huvudregel

**Main är skyddad.** Alla ändringar går via branch → PR → merge.

```
Din branch → PR → Godkännande → Merge till main → Klart
```

Branch protection på GitHub blockerar alla direkta pushar till main. Det går inte att kringgå.

---

## 2. Dagligt arbete

```bash
# 1. Börja med ren main
git checkout main
git pull origin main

# 2. Skapa feature-branch
git checkout -b dittnamn/vad-du-gor

# 3. Jobba, commita, pusha
git add filer...
git commit -m "vad du gjorde"
git push origin dittnamn/vad-du-gor

# 4. Öppna PR på GitHub
# 5. Vänta på godkännande
# 6. Merge
```

---

## 3. Branch-namn

```
<ditt-namn>/<vad-du-bygger>
```

Exempel:
- `alpe/fix-git-sync-and-rename`
- `william/webui-real-data`
- `anner/token-auth-fix`

---

## 4. Vad händer vid parallellt arbete?

| Scenario | Resultat |
|---|---|
| Alpedal pushar branch A, William pushar branch B | Noll konflikt. Båda brancharna lever oberoende. |
| Alpedals PR merge:as först → Williams PR merge:as sen | Williams PR rebasar automatiskt. Inget förloras. |
| Williams PR merge:as först → Alpedals PR merge:as sen | Alpedals PR rebasar automatiskt. Inget förloras. |

Ordningen spelar ingen roll. GitHub hanterar rebase vid merge.

---

## 5. Serverns sync.sh

Servern kör `server/sync.sh` via cron. Den:

| Gör | Gör INTE |
|-----|----------|
| `git fetch --prune` | `git add` |
| `git merge --ff-only` | `git commit` |
| Loggar allt | `git push` |

Vid konflikt (lokal divergens): scriptet avbryter och loggar felet. Ingen data förstörs.

Cron-exempel:
```
*/5 * * * * /path/to/server/sync.sh >> /var/log/igris-sync.log 2>&1
```

---

## 6. Fail-safe: branch protection

Även om sync.sh mot förmodan skulle försöka pusha — GitHub avvisar.

**Inställning (görs en gång):**
```
Repo → Settings → Branches → Add rule → "main":
  ☑ Require a pull request before merging
  ☑ Require approvals (1)
```

Efter detta kan ingen — varken människa eller script — pusha direkt till main.

---

## 7. Checklista för ny utvecklare

- [ ] Klona repot: `git clone git@github.com:Alpedal/the-system.git`
- [ ] Läs denna fil
- [ ] Skapa din första branch: `git checkout -b dittnamn/test`
- [ ] Gör en liten ändring, pusha, öppna PR
- [ ] Klart — du är inne i workflowen
