#!/usr/bin/env bash
set -Eeuo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
LOG_FILE="$ROOT_DIR/shared/memory/sync-log.md"
ALERT_FILE="$ROOT_DIR/.hermes-alert"
REMOTE_BRANCH="${SYNC_BRANCH:-master}"

FORBIDDEN_PATTERNS=(
  'git push --force'
  'git push -f'
  'git reset --hard'
  'git clean -fd'
  'git checkout -- .'
  'rm -rf .git'
)

die() {
  printf '%s\n' "ERROR: $*" >&2
  exit 1
}

ensure_repo() {
  [[ -e "$ROOT_DIR/.git" ]] || die "Missing git repository at hosted-aios root: $ROOT_DIR/.git"
  git_safe rev-parse --is-inside-work-tree >/dev/null 2>&1 || die "Not a git repository: $ROOT_DIR"
  [[ "$(git_safe rev-parse --show-toplevel)" == "$ROOT_DIR" ]] || die "Refusing to sync parent repository outside hosted-aios: $(git_safe rev-parse --show-toplevel)"
}

git_safe() {
  command git -c safe.directory="$ROOT_DIR" -C "$ROOT_DIR" "$@"
}

ensure_log_dir() {
  mkdir -p "$ROOT_DIR/shared/memory"
}

timestamp() {
  date '+%Y-%m-%d %H:%M:%S'
}

run_checked() {
  local joined="$*"
  local blocked
  for blocked in "${FORBIDDEN_PATTERNS[@]}"; do
    if [[ "$joined" == *"$blocked"* ]]; then
      die "Forbidden command blocked: $blocked"
    fi
  done
  "$@"
}

log_block() {
  ensure_log_dir
  {
    printf '#### %s\n' "$(timestamp)"
    local line
    for line in "$@"; do
      printf '%s\n' "$line"
    done
    printf '\n'
  } >> "$LOG_FILE"
}

count_lines() {
  awk 'NF{c++} END{print c+0}'
}

count_stash_files() {
  local ref="$1"
  git_safe stash show --name-only --format= "$ref" 2>/dev/null | count_lines
}

count_commit_files() {
  git_safe diff --cached --name-only | count_lines
}

latest_auto_stash_ref() {
  git_safe stash list --format='%gd %s' | awk '/auto-sync-/{print $1; exit}'
}

backup_conflict_file() {
  local file="$1"
  local stamp="$2"
  local conflict_copy="${file}.CONFLICT-${stamp}"
  local local_copy="${file}.LOCAL"

  if [[ -e "$file" ]]; then
    mkdir -p "$(dirname "$conflict_copy")"
    cp -p -- "$file" "$conflict_copy" || true
    if git_safe show "HEAD:$file" > "$local_copy" 2>/dev/null; then
      :
    else
      cp -p -- "$file" "$local_copy" || true
    fi
  fi

  printf '%s\n' "$conflict_copy"
}

handle_pull_conflict() {
  local stamp="$(date '+%Y-%m-%d-%H%M%S')"
  local conflict_files=()
  mapfile -t conflict_files < <(git_safe diff --name-only --diff-filter=U)

  local conflict_log=()
  local file
  for file in "${conflict_files[@]}"; do
    [[ -n "$file" ]] || continue
    local conflict_copy
    conflict_copy="$(backup_conflict_file "$file" "$stamp")"
    conflict_log+=("- CONFLICT SAVED: ${file}.CONFLICT-${stamp}")
    conflict_log+=("- LOCAL COPY: ${file}.LOCAL")
    if [[ -n "$conflict_copy" ]]; then
      :
    fi
  done

  run_checked git_safe rebase --abort || true

  if ((${#conflict_files[@]} > 0)); then
    log_block "- PULL FAILED: merge conflict in ${conflict_files[*]}" "${conflict_log[@]}" "- ACTION: manual review required"
  else
    log_block "- PULL FAILED: rebase failed without explicit conflict files" "- ACTION: manual review required"
  fi

  printf 'Pull conflict detected at %s\n' "$(timestamp)" > "$ALERT_FILE"
  if ((${#conflict_files[@]} > 0)); then
    printf 'Files: %s\n' "${conflict_files[*]}" >> "$ALERT_FILE"
  fi

  printf 'Sync conflict detected. A backup was created and remote version will be pulled.\n' >&2

  if ! run_checked git_safe pull --no-rebase -X theirs origin "$REMOTE_BRANCH"; then
    die "Could not pull remote version after rebase failure"
  fi
}

main() {
  cd "$ROOT_DIR"
  ensure_repo
  ensure_log_dir

  local stash_msg="auto-sync-$(date +%s)"
  local before_head after_head commit_count stash_ref stash_files commit_files
  if git_safe rev-parse --verify HEAD >/dev/null 2>&1; then
    before_head="$(git_safe rev-parse --short HEAD)"
  else
    before_head="NO-HEAD"
  fi

  if ! run_checked git_safe stash push -u -m "$stash_msg"; then
    die "Stash step failed"
  fi

  stash_ref="$(git_safe stash list --format='%gd %s' | awk -v msg="$stash_msg" '$0 ~ msg {print $1; exit}')"
  if [[ -n "${stash_ref:-}" ]]; then
    stash_files="$(count_stash_files "$stash_ref")"
    log_block "- STASH: ${stash_files} filer sparade"
  else
    log_block "- STASH: no local changes to save"
  fi

  if ! run_checked git_safe pull --rebase origin "$REMOTE_BRANCH"; then
    handle_pull_conflict
  else
    if git_safe rev-parse --verify HEAD >/dev/null 2>&1; then
      after_head="$(git_safe rev-parse --short HEAD)"
    else
      after_head="NO-HEAD"
    fi
    if [[ "$before_head" == "NO-HEAD" ]]; then
      commit_count="0"
    else
      commit_count="$(git_safe rev-list --count "${before_head}..HEAD" 2>/dev/null || printf '0')"
    fi
    log_block "- PULL: ${commit_count} commits fetched (${before_head}..${after_head})"
  fi

  if ! run_checked git_safe stash pop; then
    stash_ref="$(git_safe stash list --format='%gd %s' | awk -v msg="$stash_msg" '$0 ~ msg {print $1; exit}')"
    if [[ -n "${stash_ref:-}" ]]; then
      local patch_file="$ROOT_DIR/.stash-backup-$(date +%s).patch"
      if run_checked git_safe stash show -p "$stash_ref" > "$patch_file"; then
        log_block "- POP FAILED: stash backup saved to $(basename "$patch_file")" "- ACTION: patch can be applied manually"
      else
        log_block "- POP FAILED: could not create stash backup" "- ACTION: manual review required"
      fi
    else
      log_block "- POP FAILED: no auto-sync stash found" "- ACTION: manual review required"
    fi
  else
    log_block "- POP: OK"
  fi

  run_checked git_safe add -A
  commit_files="$(count_commit_files)"

  if git_safe diff --cached --quiet; then
    log_block "- COMMIT: no changes to commit"
  else
    local commit_msg="sync: auto-commit $(date +%Y-%m-%d_%H%M%S)"
    run_checked git_safe commit -m "$commit_msg"
    log_block "- COMMIT: \"$commit_msg\" (${commit_files} filer)"
  fi

  if ! run_checked git_safe push origin "$REMOTE_BRANCH"; then
    die "Push failed"
  fi

  log_block "- PUSH: OK"
}

main "$@"
