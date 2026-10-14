#!/usr/bin/env bash
# Remove verification scratch only. Never deletes evidence/.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck disable=SC1091
source "$SCRIPT_DIR/common.sh"

SCRATCH_IN="${1:-}"
if [[ -z "$SCRATCH_IN" ]]; then
  printf 'usage: cleanup.sh SCRATCH\n' >&2
  exit 2
fi

if [[ ! -d "$SCRATCH_IN" ]]; then
  printf 'cleanup: nothing to remove (%s missing)\n' "$SCRATCH_IN"
  exit 0
fi

# Resolve .. and symlinks before any prefix check or rm.
SCRATCH="$(cd "$SCRATCH_IN" && pwd -P)"
ROOT_PREFIX="/tmp/verify-habitica-levelup"
ROOT_CANON="$(mkdir -p "$ROOT_PREFIX" && cd "$ROOT_PREFIX" && pwd -P)"

case "$SCRATCH" in
  "$ROOT_CANON"/*) ;;
  *)
    printf 'error: refusing to remove path outside %s: %s\n' "$ROOT_CANON" "$SCRATCH" >&2
    exit 1
    ;;
esac

# Require a state file that records this exact canonical path.
if [[ ! -f "$SCRATCH/state.env" ]]; then
  printf 'error: missing state.env; refusing to remove %s\n' "$SCRATCH" >&2
  exit 1
fi

TARGET_SCRATCH="$SCRATCH"
# shellcheck disable=SC1091
source "$TARGET_SCRATCH/state.env"

recorded_raw="${SCRATCH:-}"
if [[ -z "$recorded_raw" ]]; then
  printf 'error: state.env missing SCRATCH; refusing to remove %s\n' "$TARGET_SCRATCH" >&2
  exit 1
fi
if [[ -d "$recorded_raw" ]]; then
  recorded_canon="$(cd "$recorded_raw" && pwd -P)"
else
  recorded_canon="$recorded_raw"
fi
if [[ "$recorded_canon" != "$TARGET_SCRATCH" ]]; then
  printf 'error: state.env SCRATCH does not match target (%s vs %s)\n' \
    "$recorded_canon" "$TARGET_SCRATCH" >&2
  exit 1
fi
SCRATCH="$TARGET_SCRATCH"

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

rm -rf "$SCRATCH"
printf 'cleanup: removed %s (evidence preserved)\n' "$SCRATCH"
