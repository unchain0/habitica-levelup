# Farm loop

The farm loop creates or reuses the HARD habit `Auto Farm XP`, scores it each
iteration, refreshes level from the API, logs progress every 10 levels, sleeps
30 seconds between successful iterations, and stops at level 999.

## Sub-features

- `farm-task-reuse` returns an existing task whose text is `Auto Farm XP`.
- `farm-task-create` creates a HARD habit with that title when missing.
- `farm-score` scores the farm task up each successful iteration.
- `farm-progress-log` logs `Progress: Level <n>/999` when level % 10 == 0.
- `farm-rate-limit-delay` sleeps `RATE_LIMIT_DELAY` (30.0s) after success.
- `farm-max-level` stops when `current_level >= MAX_LEVEL` (999).
- `farm-already-max` returns immediately with `Already at maximum level!`.

## How to get to it (user POV)

- Run `uv run python main.py` with valid config (live path blocked here).
- Leave the process running; it loops until 999 or a stop signal.
- Watch console or `~/.local/share/habitica-levelup/app.log` for progress lines.

## Driving it with verify-habitica-levelup

Preconditions:

- Scratch dir from `scripts/launch.sh`; `scripts/doctor.sh` is ok.
- Owner rule: do not launch this app. Live proof is
  **not run (owner rule: do not launch this app)**.
- Tests mock `HabiticaGateway`; no network.

- **Engine decisions.** Run
  `.cursor/skills/verify-habitica-levelup/scripts/drive.sh "$SCRATCH" farm-loop`.
  `tests/test_engines.py` asserts `extract_level`, `should_continue_leveling`,
  `should_log_progress`, and `is_max_level` against literal levels.
- **Task create/reuse.** `tests/test_tasks.py::TestHabiticaGatewayFarmTask`
  covers existing task id return, create on miss, HARD priority, and empty list.
- **Iteration success.** `TestLevelUpService::test_run_iteration_success`
  records circuit success when farm + maintain complete.
- **Service run.** `TestLevelUpServiceRun` covers already-at-max, reach max,
  progress interval logging, level refresh after success, and short sleep on
  iteration failure (0.5s).
- **Constants.** Doctor already pinned `MAX_LEVEL=999`, `PROGRESS_INTERVAL=10`,
  `RATE_LIMIT_DELAY=30.0`, title `Auto Farm XP`.
- **Proof.** Evidence holds pytest exit 0, transcript, and `PROOF.md`.
  `STATIC_NOTE.md` states **not run (owner rule: do not launch this app)**.

## Gotchas

- Live spacing is 30 seconds per successful iteration (`RATE_LIMIT_DELAY`). Do
  not treat unit tests that patch `asyncio.sleep` as proof of wall-clock delay.
- Progress logs only when `current_level % PROGRESS_INTERVAL == 0` after a
  successful iteration refresh.
- Farm task match is exact text equality on `Auto Farm XP`, not a fuzzy title.
- Never call `get_or_create_farm_task` against the real API from this skill.
