#!/usr/bin/env bash
# Remove verification scratch only. Never deletes evidence/.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck disable=SC1091
source "$SCRIPT_DIR/common.sh"

SCRATCH="${1:-}"
if [[ -z "$SCRATCH" ]]; then
  printf 'usage: cleanup.sh SCRATCH\n' >&2
  exit 2
fi

if [[ ! -d "$SCRATCH" ]]; then
  printf 'cleanup: nothing to remove (%s missing)\n' "$SCRATCH"
  exit 0
fi

case "$SCRATCH" in
  /tmp/verify-habitica-levelup/*) ;;
  *)
    printf 'error: refusing to remove path outside /tmp/verify-habitica-levelup/: %s\n' "$SCRATCH" >&2
    exit 1
    ;;
esac

if [[ -f "$SCRATCH/state.env" ]]; then
  # shellcheck disable=SC1091
  source "$SCRATCH/state.env"
  if [[ -n "${BOT_PID:-}" ]]; then
    if kill -0 "$BOT_PID" 2>/dev/null; then
      cmd="$(ps -p "$BOT_PID" -o args= 2>/dev/null || true)"
      case "$cmd" in
        *main.py*)
          kill -TERM "$BOT_PID" 2>/dev/null || true
          sleep 1
          if kill -0 "$BOT_PID" 2>/dev/null; then
            kill -KILL "$BOT_PID" 2>/dev/null || true
          fi
          ;;
        *)
          printf 'cleanup: refusing to signal pid %s (cmdline does not contain main.py)\n' "$BOT_PID" >&2
          ;;
      esac
    fi
  fi
fi

rm -rf "$SCRATCH"
printf 'cleanup: removed %s (evidence preserved)\n' "$SCRATCH"
