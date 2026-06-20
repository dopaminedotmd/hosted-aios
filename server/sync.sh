#!/usr/bin/env bash
# ============================================================
# sync.sh — Pull-only sync for Commander Igris
# ============================================================
# Körs av cron. Drar NER ändringar från main.
# Pushar ALDRIG. Commitar ALDRIG. Rör ALDRIG lokala ändringar.
#
# Cron:   */5 * * * * /path/to/server/sync.sh >> /var/log/igris-sync.log 2>&1
# ============================================================
set -euo pipefail

REMOTE="origin"
BRANCH="main"

log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*"; }

# ─── Safety check ──────────────────────────────────────────
if ! git rev-parse --git-dir > /dev/null 2>&1; then
    log "ERROR: Not in a git repository. Exiting."
    exit 1
fi

# Move to repo root
cd "$(git rev-parse --show-toplevel)"

# ─── Fetch only ────────────────────────────────────────────
log "Fetching from $REMOTE/$BRANCH..."
if ! git fetch --prune "$REMOTE" "$BRANCH"; then
    log "ERROR: git fetch failed. Check network or SSH key."
    exit 1
fi

# ─── Check if we're on main ────────────────────────────────
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
if [ "$CURRENT_BRANCH" != "$BRANCH" ]; then
    log "WARNING: Not on $BRANCH branch (currently: $CURRENT_BRANCH). Skipping pull."
    exit 0
fi

# ─── Fast-forward only (no merge commits) ──────────────────
LOCAL=$(git rev-parse HEAD)
REMOTE_HASH=$(git rev-parse "$REMOTE/$BRANCH")

if [ "$LOCAL" = "$REMOTE_HASH" ]; then
    log "Already up to date. ($LOCAL)"
    exit 0
fi

# Check if fast-forward is possible (no local divergence)
if git merge-base --is-ancestor "$LOCAL" "$REMOTE_HASH"; then
    log "Pulling changes (fast-forward)..."
    git merge --ff-only "$REMOTE/$BRANCH"
    log "Updated to $(git rev-parse --short HEAD)"
else
    log "ERROR: Local branch has diverged from $REMOTE/$BRANCH."
    log "This requires manual intervention. Refusing to merge."
    log "   Local:  $(git log --oneline -1 "$LOCAL")"
    log "   Remote: $(git log --oneline -1 "$REMOTE_HASH")"
    exit 1
fi

log "Sync complete."
