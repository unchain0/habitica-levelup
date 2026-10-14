#!/usr/bin/env bash
# Shared helpers for verify-habitica-levelup. Source only; do not execute.

set -euo pipefail

verify_skill_root() {
  local here
  here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
  cd "$here/.." && pwd
}

verify_repo_root() {
  local skill_root
  skill_root="$(verify_skill_root)"
  cd "$skill_root/../../.." && pwd
}

verify_require_repo() {
  local root="$1"
  if [[ ! -f "$root/main.py" || ! -f "$root/pyproject.toml" ]]; then
    printf 'error: repo root looks wrong: %s\n' "$root" >&2
    return 1
  fi
}

verify_load_state() {
  local scratch="${1:-}"
  if [[ -z "$scratch" ]]; then
    printf 'error: scratch dir required\n' >&2
    return 1
  fi
  if [[ ! -f "$scratch/state.env" ]]; then
    printf 'error: missing state.env in %s\n' "$scratch" >&2
    return 1
  fi
  # shellcheck disable=SC1091
  source "$scratch/state.env"
  if [[ -z "${REPO_ROOT:-}" || -z "${RUN_ID:-}" ]]; then
    printf 'error: state.env incomplete\n' >&2
    return 1
  fi
  verify_require_repo "$REPO_ROOT"
}

verify_evidence_dir() {
  local feature_id="$1"
  local run_id="$2"
  local skill_root
  skill_root="$(verify_skill_root)"
  local dest="$skill_root/evidence/${feature_id}-${run_id}"
  mkdir -p "$dest"
  printf '%s\n' "$dest"
}

verify_redact() {
  # Pass-through filter that strips common secret assignment shapes from logs.
  sed -E \
    -e 's/(API_TOKEN|USER_ID|api_token|user_id|apiKey|api_key)[=:][[:space:]]*[^[:space:]]+/\1=<redacted>/gi' \
    -e 's/("API_TOKEN"|"USER_ID")[[:space:]]*:[[:space:]]*"[^"]*"/\1:"<redacted>"/g'
}

verify_forbid_launch() {
  # Hard guard: helpers must never start the bot.
  if [[ "${VERIFY_ALLOW_LIVE_LAUNCH:-}" == "1" ]]; then
    printf 'error: live launch is disabled by owner rule (do not launch this app)\n' >&2
    return 1
  fi
}
