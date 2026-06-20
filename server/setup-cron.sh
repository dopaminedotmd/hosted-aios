#!/usr/bin/env bash
set -Eeuo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
SYNC_SCRIPT="$ROOT_DIR/server/sync.sh"
LOG_FILE="$ROOT_DIR/shared/memory/sync-log.md"
TASK_NAME="hosted-aios-sync"

die() {
  printf '%s\n' "ERROR: $*" >&2
  exit 1
}

ensure_paths() {
  [[ -f "$SYNC_SCRIPT" ]] || die "Missing sync script: $SYNC_SCRIPT"
  mkdir -p "$ROOT_DIR/shared/memory"
}

install_linux_cron() {
  local cron_line="*/5 * * * * cd \"$ROOT_DIR\" && bash server/sync.sh >> shared/memory/sync-log.md 2>&1"
  local current_cron
  current_cron="$(crontab -l 2>/dev/null || true)"

  if printf '%s\n' "$current_cron" | grep -Fq "$SYNC_SCRIPT"; then
    printf 'Linux cron already installed.\n'
    return 0
  fi

  {
    printf '%s\n' "$current_cron"
    printf '%s\n' "$cron_line"
  } | crontab -

  printf 'Installed Linux cron job.\n'
  printf '%s\n' "$cron_line"
}

install_windows_task() {
  local bash_path task_cmd task_args
  local root_unix root_win bash_win

  bash_path="$(command -v bash.exe || true)"
  if [[ -z "$bash_path" ]]; then
    bash_path="$(command -v bash || true)"
  fi

  if [[ -z "$bash_path" ]]; then
    die "Could not locate bash.exe or bash for Windows task creation"
  fi

  if command -v cygpath >/dev/null 2>&1; then
    root_unix="$(cygpath -u "$ROOT_DIR")"
    root_win="$(cygpath -w "$ROOT_DIR")"
    bash_win="$(cygpath -w "$bash_path")"
  else
    root_unix="$ROOT_DIR"
    root_win="$ROOT_DIR"
    bash_win="$bash_path"
  fi

  task_cmd="$bash_win"
  task_args="-lc \"cd '$root_unix' && bash server/sync.sh >> shared/memory/sync-log.md 2>&1\""

  if schtasks.exe /Query /TN "$TASK_NAME" >/dev/null 2>&1; then
    schtasks.exe /Delete /TN "$TASK_NAME" /F >/dev/null
  fi

  schtasks.exe /Create /TN "$TASK_NAME" /SC MINUTE /MO 5 /F /TR "\"$task_cmd\" $task_args"

  printf 'Installed Windows Task Scheduler job.\n'
  printf 'Task name: %s\n' "$TASK_NAME"
  printf 'Command: %s %s\n' "$task_cmd" "$task_args"
  printf 'Windows root path: %s\n' "$root_win"
}

main() {
  ensure_paths

  case "$(uname -s 2>/dev/null || echo unknown)" in
    MINGW*|MSYS*|CYGWIN*|Windows_NT)
      install_windows_task
      ;;
    *)
      if command -v crontab >/dev/null 2>&1; then
        install_linux_cron
      else
        die "crontab not found and Windows scheduler not detected"
      fi
      ;;
  esac

  printf 'Log file target: %s\n' "$LOG_FILE"
}

main "$@"
