#!/usr/bin/env bash

set -euo pipefail

target="${1:-all}"

run_auto_fix() {
  uv run ruff check --fix .
  uv run ruff format .
}

capture_python_worktree_state() {
  git status --short -- src tests
}

fail_if_auto_fix_changed_worktree() {
  local before_state="$1"
  local after_state
  after_state="$(capture_python_worktree_state)"

  if [[ "$before_state" != "$after_state" ]]; then
    printf '\nLocal hook auto-fixed files. Review, commit, then push again.\n' >&2
    GIT_PAGER=cat git diff --stat -- src tests >&2
    exit 1
  fi
}

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
  pre-push)
    before_state="$(capture_python_worktree_state)"
    run_auto_fix
    fail_if_auto_fix_changed_worktree "$before_state"
    run_lint
    run_type_check
    run_tests
    run_security
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
