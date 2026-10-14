# Auth and resilience

Bad credentials fail fast with no retry. Rate limits retry with backoff. Repeated
iteration failures open a circuit breaker that pauses work before trying again.

## Sub-features

- `auth-no-retry` re-raises `NotAuthorizedError` inside `with_retry` immediately.
- `auth-init-fatal` logs credential failure on service initialize and re-raises.
- `auth-bot-stop` sets `shutdown_event` and skips the 30s restart delay when the
  service raises `NotAuthorizedError`.
- `retry-rate-limit` retries `TooManyRequestsError` up to `RetryConfig.MAX_RETRIES`
  (3) with exponential delay capped by `MAX_DELAY` (60.0).
- `circuit-open` opens after `max_failures` (default 5) recorded failures.
- `circuit-reset` clears after `reset_timeout` (default one minute).
- `iteration-timeout` records failure on 30s iteration timeout.
- `iteration-rate-limit` records failure and sleeps 1.0s on
  `TooManyRequestsError` bubbling from an iteration.

## How to get to it (user POV)

- Start the bot with wrong API credentials (live path blocked here); process
  should stop after authorize failure without looping restarts.
- Under heavy API use the bot backs off; after enough iteration failures it
  logs `Circuit breaker open, waiting...`.

## Driving it with verify-habitica-levelup

Preconditions:

- Doctor-healthy scratch from `scripts/launch.sh`.
- Owner rule: do not launch this app. Live proof is
  **not run (owner rule: do not launch this app)**.
- No real tokens; tests build `NotAuthorizedError` with fake
  `HabiticaErrorResponse` bodies.

- **Drive suite.** Run
  `.cursor/skills/verify-habitica-levelup/scripts/drive.sh "$SCRATCH" auth-and-resilience`.
- **Retry auth.** `tests/test_infrastructure.py::TestWithRetry::test_no_retry_on_not_authorized`
  raises without sleeping through retries.
- **Retry rate limit.** `test_retry_on_too_many_requests` succeeds after mocked
  sleeps; exhausted retries re-raise.
- **Circuit unit.** `tests/test_core.py::TestCircuitBreaker` covers open/close
  and success reset; `TestRetryConfig` pins retry constants.
- **Bot auth stop.**
  `tests/integration/test_bot_integration.py::TestBotInfrastructureIntegration::test_bot_stops_on_auth_failure_without_restart`
  asserts one `service.run`, no restart sleep, and `shutdown_event` set.
- **Service init auth.** `TestLevelUpServiceRun::test_run_initialize_fails_with_auth_error`.
- **Iteration faults.** timeout and rate-limit tests on `run_iteration` record
  circuit failures.
- **Unexpected end restart.** integration test retries after unexpected service
  return uses `RESTART_DELAY` 30.0 only when the error is not auth.
- **Proof.** Evidence transcript exit 0 and `PROOF.md`. `STATIC_NOTE.md` states
  **not run (owner rule: do not launch this app)**.

## Gotchas

- Auth is fatal at two layers: `with_retry` and `LevelUpBot.run`. Do not expect
  a restart loop after 401-class failures.
- Soft `NotAuthorizedError` for missing stat points is only handled inside
  allocate, not as a global auth failure.
- Circuit open causes a 60 second wait inside `run_iteration` before returning
  False; tests mock `asyncio.sleep`.
- Never log or echo API tokens when demonstrating a human auth failure.
