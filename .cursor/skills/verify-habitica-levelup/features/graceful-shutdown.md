# Graceful shutdown

SIGINT and SIGTERM mark `shutdown_event` so the leveling loop stops after the
current iteration machinery observes the flag. A bot that already has shutdown
set does not call `service.run`.

## Sub-features

- `shutdown-signal-handlers` registers SIGINT and SIGTERM on the running loop.
- `shutdown-windows-noop` swallows `NotImplementedError` when signal handlers
  are unavailable.
- `shutdown-sets-event` signal callback sets `service.shutdown_event`.
- `shutdown-stops-loop` `should_continue_leveling` is false when
  `shutdown_requested` is true.
- `shutdown-skips-run` bot main loop does not await `service.run` when the event
  is already set.
- `shutdown-final-log` final status logs `Stopped at level <n>` when shutdown
  was requested.

## How to get to it (user POV)

- Press Ctrl+C while `python main.py` is running (live path blocked here).
- Send SIGTERM to the process (for example `docker-compose stop` or kill on the
  recorded pid).
- The bot finishes the in-flight iteration path and exits without an immediate
  hard crash from the signal handler itself.

## Driving it with verify-habitica-levelup

Preconditions:

- Doctor-healthy scratch from `scripts/launch.sh`.
- Owner rule: do not launch this app. Live Ctrl+C against `main.py` is
  **not run (owner rule: do not launch this app)**.
- Tests register handlers on the pytest event loop with a mocked service.

- **Drive suite.** Run
  `.cursor/skills/verify-habitica-levelup/scripts/drive.sh "$SCRATCH" graceful-shutdown`.
- **Engine flag.** `tests/test_engines.py::test_should_continue_leveling` includes
  the case `(1, 10, True) is False`.
- **Handlers on Windows path.**
  `test_setup_signal_handlers_windows` patches `add_signal_handler` to raise
  `NotImplementedError` and still returns.
- **Handler sets event.** `test_signal_handler_sets_shutdown_event` invokes the
  registered callback and expects `shutdown_event.is_set()`.
- **Already stopped.** `test_bot_does_not_run_when_shutdown_already_requested`
  never awaits `service.run`.
- **Cancelled path.** `TestLevelUpServiceRun::test_run_cancelled_error` re-raises
  `asyncio.CancelledError` after initialize.
- **Proof.** Evidence transcript exit 0 and `PROOF.md`. `STATIC_NOTE.md` records
  **not run (owner rule: do not launch this app)**.

## Gotchas

- The handler only sets an event. It does not call `sys.exit` itself.
  `main.py` maps outer `KeyboardInterrupt` to exit 0 separately.
- Do not `pkill -f main.py` during verification; that can kill unrelated human
  sessions. Cleanup only signals a pid recorded in scratch `state.env`.
- Integration signal tests depend on loop `_signal_handlers`; they are the
  supported offline proof, not a substitute for a live Ctrl+C capture while the
  owner rule stands.
