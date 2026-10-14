#!/usr/bin/env bash
# Prepare a disposable verification workspace. Does NOT start main.py.
# Owner rule: do not launch this app.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck disable=SC1091
source "$SCRIPT_DIR/common.sh"

verify_forbid_launch

REPO_ROOT="$(verify_repo_root)"
verify_require_repo "$REPO_ROOT"
cd "$REPO_ROOT"

if ! command -v uv >/dev/null 2>&1; then
  printf 'error: uv not found on PATH\n' >&2
  exit 1
fi

if [[ ! -d "$REPO_ROOT/.venv" ]]; then
  uv sync --group dev
fi

RUN_ID="$(date -u +%Y%m%dT%H%M%SZ)-$$"
SCRATCH="/tmp/verify-habitica-levelup/${RUN_ID}"
mkdir -p "$SCRATCH"
chmod 700 "$SCRATCH"

# Fake non-placeholder credentials only. Never real Habitica secrets.
# Values avoid Settings placeholder set: changeme, placeholder, your-user-id,
# your-api-token, and empty.
cat >"$SCRATCH/.env" <<'EOF'
USER_ID=verify-user-id-0000
API_TOKEN=verify-api-token-0000
LOG_LEVEL=DEBUG
EOF
chmod 600 "$SCRATCH/.env"

cat >"$SCRATCH/state.env" <<EOF
RUN_ID=$RUN_ID
SCRATCH=$SCRATCH
REPO_ROOT=$REPO_ROOT
PREPARED_AT=$(date -u +%Y-%m-%dT%H:%M:%SZ)
OWNER_RULE=do-not-launch-this-app
BOT_PID=
EOF
chmod 600 "$SCRATCH/state.env"

cat >"$SCRATCH/README.txt" <<'EOF'
Verification scratch for habitica-levelup.
This directory holds fake env values only.
Owner rule: do not launch this app.
Do not run main.py, uv run task run, or docker compose from this skill.
EOF

printf 'prepared scratch (bot not started; owner rule: do not launch this app)\n'
printf 'SCRATCH=%s\n' "$SCRATCH"
