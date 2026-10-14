#!/usr/bin/env bash
# Read-only readiness check for a verification scratch. Never starts the bot.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck disable=SC1091
source "$SCRIPT_DIR/common.sh"

SCRATCH="${1:-}"
verify_load_state "$SCRATCH"
cd "$REPO_ROOT"

fail() {
  printf 'doctor: not ready: %s\n' "$1" >&2
  exit 1
}

need_file() {
  [[ -f "$1" ]] || fail "missing file $1"
}

need_file "$REPO_ROOT/main.py"
need_file "$REPO_ROOT/pyproject.toml"
need_file "$REPO_ROOT/.env.example"
need_file "$REPO_ROOT/src/delivery/cli.py"
need_file "$REPO_ROOT/src/delivery/settings.py"
need_file "$REPO_ROOT/src/delivery/bot_runner.py"
need_file "$REPO_ROOT/src/delivery/logging.py"
need_file "$REPO_ROOT/src/services/levelup_service.py"
need_file "$REPO_ROOT/src/services/resilience.py"
need_file "$REPO_ROOT/src/engines/leveling.py"
need_file "$REPO_ROOT/src/integrations/habitica_gateway.py"
need_file "$REPO_ROOT/src/integrations/retry.py"
need_file "$REPO_ROOT/src/domain_models/farm_task.py"
need_file "$SCRATCH/.env"
need_file "$SCRATCH/state.env"

command -v uv >/dev/null 2>&1 || fail "uv not on PATH"

grep -q 'requires-python = ">=3.14,<3.15"' "$REPO_ROOT/pyproject.toml" \
  || fail "pyproject requires-python mismatch"
grep -q 'run = "python main.py"' "$REPO_ROOT/pyproject.toml" \
  || fail "taskipy run task missing"

grep -q '^USER_ID=' "$REPO_ROOT/.env.example" || fail ".env.example missing USER_ID"
grep -q '^API_TOKEN=' "$REPO_ROOT/.env.example" || fail ".env.example missing API_TOKEN"
grep -q 'LOG_LEVEL' "$REPO_ROOT/.env.example" || fail ".env.example missing LOG_LEVEL"

# Placeholder set must stay in lockstep with Settings.validate_not_placeholder.
settings_py="$REPO_ROOT/src/delivery/settings.py"
for token in changeme placeholder your-user-id your-api-token; do
  grep -q "\"$token\"" "$settings_py" || fail "placeholder $token missing from settings.py"
done

service_py="$REPO_ROOT/src/services/levelup_service.py"
grep -q 'MAX_LEVEL = 999' "$service_py" || fail "MAX_LEVEL != 999"
grep -q 'RATE_LIMIT_DELAY = 30.0' "$service_py" || fail "RATE_LIMIT_DELAY != 30.0"
grep -q 'PROGRESS_INTERVAL = 10' "$service_py" || fail "PROGRESS_INTERVAL != 10"
grep -q 'ARMOIRE_GOLD_THRESHOLD = 10000.0' "$service_py" || fail "ARMOIRE_GOLD_THRESHOLD != 10000.0"

grep -q 'RESTART_DELAY = 30.0' "$REPO_ROOT/src/delivery/bot_runner.py" \
  || fail "RESTART_DELAY != 30.0"
grep -q 'FARM_TASK_TITLE = "Auto Farm XP"' "$REPO_ROOT/src/domain_models/farm_task.py" \
  || fail "farm task title mismatch"
grep -q 'signal.SIGINT' "$REPO_ROOT/src/delivery/bot_runner.py" \
  || fail "SIGINT handler missing"
grep -q 'signal.SIGTERM' "$REPO_ROOT/src/delivery/bot_runner.py" \
  || fail "SIGTERM handler missing"
grep -q 'NotAuthorizedError' "$REPO_ROOT/src/integrations/retry.py" \
  || fail "retry missing NotAuthorizedError path"

# Scratch env must be the fake verify-* pair only (no value dump).
if ! grep -q '^USER_ID=verify-user-id-0000$' "$SCRATCH/.env"; then
  fail "scratch USER_ID is not the fake verify value"
fi
if ! grep -q '^API_TOKEN=verify-api-token-0000$' "$SCRATCH/.env"; then
  fail "scratch API_TOKEN is not the fake verify value"
fi

# Owner rule: prepare must not have started a bot.
if [[ -n "${BOT_PID:-}" ]]; then
  fail "BOT_PID is set; owner rule forbids a launched bot during verify"
fi

# Import-only smoke (does not run cli.main / LevelUpBot.run).
if ! uv run python -c "import src.delivery.cli, src.services.levelup_service" >/dev/null 2>&1; then
  fail "uv run import of delivery/service failed"
fi

printf 'doctor: ok scratch=%s repo=%s\n' "$SCRATCH" "$REPO_ROOT"
