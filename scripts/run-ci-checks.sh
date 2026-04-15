#!/usr/bin/env bash

set -euo pipefail

target="${1:-all}"

run_lint() {
  uv run task lint
  uv run task format -- --check
}

run_type_check() {
  uv run task type-check
}

run_tests() {
  uv run task test-cov
}

run_security() {
  uv run bandit -r src/ -f json -o bandit-report.json
}

run_integration() {
  USER_ID="${USER_ID:-test-user-id}" \
    API_TOKEN="${API_TOKEN:-test-api-token}" \
    LOG_LEVEL="${LOG_LEVEL:-DEBUG}" \
    uv run pytest tests/integration/ -v --tb=short
}

case "$target" in
  lint)
    run_lint
    ;;
  type-check)
    run_type_check
    ;;
  test)
    run_tests
    ;;
  security)
    run_security
    ;;
  integration)
    run_integration
    ;;
  all)
    run_lint
    run_type_check
    run_tests
    run_security
    run_integration
    ;;
  *)
    printf 'Unknown CI target: %s\n' "$target" >&2
    exit 1
    ;;
esac
