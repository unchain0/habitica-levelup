#!/usr/bin/env bash
# Drive one mapped feature via offline pytest. Never starts main.py or Habitica.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck disable=SC1091
source "$SCRIPT_DIR/common.sh"

SCRATCH="${1:-}"
FEATURE_ID="${2:-}"

if [[ -z "$FEATURE_ID" ]]; then
  printf 'usage: drive.sh SCRATCH FEATURE_ID\n' >&2
  exit 2
fi

verify_load_state "$SCRATCH"
cd "$REPO_ROOT"

if ! "$SCRIPT_DIR/doctor.sh" "$SCRATCH" >/tmp/verify-habitica-doctor-$$.txt 2>&1; then
  cat /tmp/verify-habitica-doctor-$$.txt >&2 || true
  rm -f /tmp/verify-habitica-doctor-$$.txt
  exit 1
fi
rm -f /tmp/verify-habitica-doctor-$$.txt

EVIDENCE="$(verify_evidence_dir "$FEATURE_ID" "$RUN_ID")"

# Fake env for pydantic settings in-process; still not real Habitica creds.
export USER_ID=verify-user-id-0000
export API_TOKEN=verify-api-token-0000
export LOG_LEVEL=DEBUG

# Clear dotenv file side effects from a human .env in repo root during tests.
# Individual tests already pop env; keep process env on fake values only.

pytest_args=()
case "$FEATURE_ID" in
  config-validation)
    pytest_args=(tests/test_config.py tests/test_main.py tests/test_logging_config.py)
    ;;
  farm-loop)
    pytest_args=(
      tests/test_engines.py
      tests/test_tasks.py
      tests/test_bot.py::TestLevelUpService
      tests/test_bot.py::TestLevelUpServiceRun
    )
    ;;
  account-maintenance)
    pytest_args=(
      tests/test_bot.py
      tests/test_engines.py
      -k
      "allocate or armoire or party_quest or maintain or should_buy or should_accept"
    )
    ;;
  auth-and-resilience)
    pytest_args=(
      tests/test_infrastructure.py
      tests/test_core.py
      tests/test_bot.py
      tests/integration/test_bot_integration.py
      -k
      "auth or NotAuthorized or circuit or retry or rate_limit or Rate or unauthorized or Unauthorized or restart or TooMany or timeout or Timeout"
    )
    ;;
  graceful-shutdown)
    pytest_args=(
      tests/integration/test_bot_integration.py
      tests/test_engines.py
      tests/test_bot.py::TestLevelUpServiceRun::test_run_cancelled_error
      -k
      "signal or shutdown or continue_leveling or cancelled or Cancelled"
    )
    ;;
  *)
    printf 'error: unknown feature id %s\n' "$FEATURE_ID" >&2
    exit 2
    ;;
esac

cmd=(uv run pytest -v --tb=short "${pytest_args[@]}")

{
  printf 'feature: %s\n' "$FEATURE_ID"
  printf 'run_id: %s\n' "$RUN_ID"
  printf 'command:'
  printf ' %q' "${cmd[@]}"
  printf '\n'
  printf 'owner_rule: do not launch this app\n'
  printf 'live_cli: not run (owner rule: do not launch this app)\n'
} >"$EVIDENCE/transcript.txt"

set +e
"${cmd[@]}" >"$EVIDENCE/pytest.stdout.txt" 2>"$EVIDENCE/pytest.stderr.txt"
status=$?
set -e

# Redact any accidental secret-shaped lines in captured output.
tmp_out="$(mktemp)"
verify_redact <"$EVIDENCE/pytest.stdout.txt" >"$tmp_out"
mv "$tmp_out" "$EVIDENCE/pytest.stdout.txt"
tmp_err="$(mktemp)"
verify_redact <"$EVIDENCE/pytest.stderr.txt" >"$tmp_err"
mv "$tmp_err" "$EVIDENCE/pytest.stderr.txt"

{
  printf 'exit_code: %s\n' "$status"
  tail -n 30 "$EVIDENCE/pytest.stdout.txt"
} >>"$EVIDENCE/transcript.txt"

cat >"$EVIDENCE/STATIC_NOTE.md" <<EOF
# Static note

Live CLI path (\`uv run python main.py\` / \`uv run task run\` / Docker) was
**not run (owner rule: do not launch this app)**.

This drive used offline pytest with mocks only. No Habitica HTTP calls. No
production credentials. Feature id: \`$FEATURE_ID\`. Run id: \`$RUN_ID\`.
EOF

if [[ "$status" -eq 0 ]]; then
  result=pass
else
  result=fail
fi

cat >"$EVIDENCE/PROOF.md" <<EOF
# Proof: $FEATURE_ID

- Feature id: \`$FEATURE_ID\`
- Entry point: offline pytest via \`scripts/drive.sh\`
- Result: \`$result\`
- Exit code: \`$status\`
- Scratch: \`$SCRATCH\`
- Evidence: \`$EVIDENCE\`
- Live CLI: **not run (owner rule: do not launch this app)**
- Side effect checked: pytest assertions on production modules with mocked
  Habitica boundary (see \`pytest.stdout.txt\`)
EOF

printf 'drive: %s feature=%s evidence=%s\n' "$result" "$FEATURE_ID" "$EVIDENCE"
exit "$status"
