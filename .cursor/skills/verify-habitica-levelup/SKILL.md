---
name: verify-habitica-levelup
description: >-
  Verify habitica-levelup (CLI bot that farms Habitica XP to level 999) the way
  a user would: prepare a disposable workspace, check the tree is drive-ready,
  exercise mapped features through mocked unit and integration tests, and
  capture proof. Use when a change needs proof against the real app surface,
  when config, farm loop, account maintenance, auth, or shutdown behavior
  changes, or for /verify-habitica-levelup.
---

# Verify habitica-levelup

Primary surface: the long-running CLI entrypoint `main.py` → `src.delivery.cli.main`
→ `LevelUpBot.run`. A user copies `.env.example` to `.env`, sets `USER_ID` and
`API_TOKEN`, optionally sets `LOG_LEVEL`, then runs `uv run python main.py` (or
`uv run task run`, or Docker Compose). The bot creates or reuses the habit
`Auto Farm XP` (HARD), scores it, allocates strength, accepts party quests, buys
the Enchanted Armoire above 10000 gold, and loops until level 999 or
SIGINT/SIGTERM.

Secondary surfaces this skill does not drive live:

- Habitica HTTPS API (`habiticalib`). Never call it from verification.
- Docker image / `docker-compose` production-style runs.
- The default log file at `~/.local/share/habitica-levelup/app.log` belonging to
  a human session.

**Owner rule: do not launch this app.** Helpers must not start `main.py`,
`uv run task run`, Docker, or any process that talks to Habitica. Live step-4
proof is recorded as **not run (owner rule: do not launch this app)**. Drive
uses offline pytest with mocks only (no network, no real credentials).

Isolation: each prepare writes `/tmp/verify-habitica-levelup/<run-id>/` with a
fake `.env` and `state.env`. Never reuse a human `.env`. Never print secret
values.

## Launch

Documented user launch (do **not** run under the owner rule):

```bash
uv sync --group dev
cp .env.example .env   # then replace placeholders with real credentials (human only)
uv run python main.py  # or: uv run task run
```

Ready signals when a human does launch: stderr shows
`Habitica Level Up Bot Starting`, then `Current level: <n>`, then either
`Leveling from <n> to 999` or `Already at maximum level!`. File log path is
`~/.local/share/habitica-levelup/app.log` (`src/delivery/logging.py`).

Verification prepare (allowed; does not start the bot):

```bash
.cursor/skills/verify-habitica-levelup/scripts/launch.sh
```

`launch.sh`:

1. Resolves the repo root from its path.
2. Requires `uv` on `PATH` and runs `uv sync --group dev` when `.venv` is missing.
3. Creates `/tmp/verify-habitica-levelup/<run-id>/` with mode-safe files.
4. Writes a disposable `.env` using only fake non-placeholder values
   (`verify-user-id-0000`, `verify-api-token-0000`, `LOG_LEVEL=DEBUG`). These are
   not real Habitica credentials and must never be used against the API.
5. Writes `state.env` (`RUN_ID`, `SCRATCH`, `REPO_ROOT`, `PREPARED_AT`).
6. Refuses if it would execute `main.py`, Docker, or any network client.

Stdout ends with `SCRATCH=/tmp/verify-habitica-levelup/<run-id>`. Pass that path
to doctor, drive, and cleanup.

Teardown is Cleanup. Launch does not leave a bot process because it never
starts one.

## Doctor

Read-only. Run before driving, and again when anything looks off:

```bash
.cursor/skills/verify-habitica-levelup/scripts/doctor.sh "$SCRATCH"
```

Exits 0 only when all of these hold:

- `$SCRATCH/state.env` exists and names this repo root.
- `main.py`, `src/delivery/cli.py`, `src/delivery/settings.py`,
  `src/delivery/bot_runner.py`, `src/services/levelup_service.py`,
  `src/engines/leveling.py`, and `src/integrations/habitica_gateway.py` exist.
- `pyproject.toml` declares `requires-python = ">=3.14,<3.15"` and task
  `run = "python main.py"`.
- `.env.example` documents `USER_ID`, `API_TOKEN`, and `LOG_LEVEL`.
- `Settings.validate_not_placeholder` still rejects
  `changeme`, `placeholder`, `your-user-id`, `your-api-token`, and empty string
  (`src/delivery/settings.py`).
- Service constants match source: `MAX_LEVEL = 999`, `RATE_LIMIT_DELAY = 30.0`,
  `PROGRESS_INTERVAL = 10`, `ARMOIRE_GOLD_THRESHOLD = 10000.0`,
  `LevelUpBot.RESTART_DELAY = 30.0`, farm title `Auto Farm XP`.
- Scratch `.env` uses fake verify-* values only (no production-shaped secrets
  required). Values are never printed.
- No bot pid was recorded (owner rule: prepare must not start the app).
- `uv run python -c "import src.delivery.cli"` succeeds (import only).

Passing doctor prints `doctor: ok scratch=… repo=…`. Do not drive a scratch
dir that fails doctor. Do not attach to a human-started `python main.py`.

## Drive

Drive mapped behavior offline through the real test modules that call production
code with mocks. Never hit Habitica. Never export real `USER_ID` / `API_TOKEN`.

```bash
.cursor/skills/verify-habitica-levelup/scripts/drive.sh "$SCRATCH" <feature-id>
```

Feature ids and pytest targets (paths confirmed in `tests/`):

| Feature id | pytest selection |
| --- | --- |
| `config-validation` | `tests/test_config.py` `tests/test_main.py` `tests/test_logging_config.py` |
| `farm-loop` | `tests/test_engines.py` `tests/test_tasks.py` `tests/test_bot.py::TestLevelUpService` `tests/test_bot.py::TestLevelUpServiceRun` |
| `account-maintenance` | `tests/test_bot.py` `-k` allocate or armoire or party_quest or maintain |
| `auth-and-resilience` | `tests/test_infrastructure.py` `tests/test_core.py` `tests/integration/test_bot_integration.py` `-k` auth or NotAuthorized or circuit or retry |
| `graceful-shutdown` | `tests/integration/test_bot_integration.py` `-k` signal or shutdown `tests/test_engines.py` `-k` continue_leveling |

Or one-shot helpers:

```bash
.cursor/skills/verify-habitica-levelup/scripts/drive-config-validation.sh "$SCRATCH"
.cursor/skills/verify-habitica-levelup/scripts/drive-farm-loop.sh "$SCRATCH"
.cursor/skills/verify-habitica-levelup/scripts/drive-account-maintenance.sh "$SCRATCH"
.cursor/skills/verify-habitica-levelup/scripts/drive-auth-and-resilience.sh "$SCRATCH"
.cursor/skills/verify-habitica-levelup/scripts/drive-graceful-shutdown.sh "$SCRATCH"
```

Stable handles from this repo (not invented):

| Handle | Source |
| --- | --- |
| Env `USER_ID`, `API_TOKEN`, `LOG_LEVEL` | `src/delivery/settings.py`, `.env.example` |
| Entry `uv run python main.py` / task `run` | `main.py`, `pyproject.toml` `[tool.taskipy.tasks]` |
| Farm habit text `Auto Farm XP`, priority HARD | `src/domain_models/farm_task.py`, `HabiticaGateway.get_or_create_farm_task` |
| Max level 999, progress every 10 levels | `LevelUpService.MAX_LEVEL`, `PROGRESS_INTERVAL` |
| Armoire when gold > 10000 | `ARMOIRE_GOLD_THRESHOLD`, `should_buy_armoire` |
| Auth fail stops bot, no restart sleep | `LevelUpBot.run` + `NotAuthorizedError` |
| SIGINT/SIGTERM → `shutdown_event` | `LevelUpBot.setup_signal_handlers` |
| Log dir `~/.local/share/habitica-levelup/app.log` | `setup_logging` |

Per-feature recipes: `features/`. Drive the feature your change touches. One
feature proof does not cover the rest of the map.

## Evidence

Write proof under:

```text
.cursor/skills/verify-habitica-levelup/evidence/<feature-id>-<run-id>/
```

Cleanup never deletes that tree. Each drive should leave:

- `transcript.txt` — exact pytest command, exit code, summary line
- `pytest.stdout.txt` / `pytest.stderr.txt` — full captured output (no secrets)
- `PROOF.md` — feature id, entry point, pass/fail, and the side effect checked
- `STATIC_NOTE.md` stating **not run (owner rule: do not launch this app)** for
  the live CLI path (`uv run python main.py`)

Standards:

- Exercise production modules through their public tests (settings, engines,
  service, bot runner, gateway helpers), not ad-hoc internal monkeypatching that
  the suite does not already own.
- Capture the action and the resulting assertion (for example placeholder
  rejection raises `ValidationError`; auth failure sets `shutdown_event` and
  skips `RESTART_DELAY` sleep).
- Side effects in tests are mock call counts and pure function return values.
  Do not require files under a human log dir as proof.
- Mocks stand in only at the Habitica boundary (`HabiticaGateway` / session
  factories), which is the production isolation line.
- Live Habitica or a real `main.py` process: **not run (owner rule: do not launch this app)**.

## Cleanup

```bash
.cursor/skills/verify-habitica-levelup/scripts/cleanup.sh "$SCRATCH"
```

Removes only `/tmp/verify-habitica-levelup/<run-id>/` after confirming
`state.env` points at that path. Does not delete
`.cursor/skills/verify-habitica-levelup/evidence/`. Does not `pkill` by name.
Does not touch a human `.env` or `~/.local/share/habitica-levelup/`.

Because launch never starts a bot, cleanup has no pid to signal. If a future
operator disables the owner rule and records a pid in `state.env`, cleanup
sends SIGTERM then SIGKILL only to that exact pid after verifying the command
line contains `main.py`.

Run cleanup after a failed drive too once evidence is copied.

## Helpers

| Script | Invocation |
| --- | --- |
| `scripts/common.sh` | Sourced by the others. Do not run it alone. |
| `scripts/launch.sh` | `.cursor/skills/verify-habitica-levelup/scripts/launch.sh` |
| `scripts/doctor.sh` | `.cursor/skills/verify-habitica-levelup/scripts/doctor.sh "$SCRATCH"` |
| `scripts/drive.sh` | `.cursor/skills/verify-habitica-levelup/scripts/drive.sh "$SCRATCH" <feature-id>` |
| `scripts/drive-config-validation.sh` | `.cursor/skills/verify-habitica-levelup/scripts/drive-config-validation.sh "$SCRATCH"` |
| `scripts/drive-farm-loop.sh` | `.cursor/skills/verify-habitica-levelup/scripts/drive-farm-loop.sh "$SCRATCH"` |
| `scripts/drive-account-maintenance.sh` | `.cursor/skills/verify-habitica-levelup/scripts/drive-account-maintenance.sh "$SCRATCH"` |
| `scripts/drive-auth-and-resilience.sh` | `.cursor/skills/verify-habitica-levelup/scripts/drive-auth-and-resilience.sh "$SCRATCH"` |
| `scripts/drive-graceful-shutdown.sh` | `.cursor/skills/verify-habitica-levelup/scripts/drive-graceful-shutdown.sh "$SCRATCH"` |
| `scripts/cleanup.sh` | `.cursor/skills/verify-habitica-levelup/scripts/cleanup.sh "$SCRATCH"` |

All helpers are executable bash. They never print `API_TOKEN` or `USER_ID`
values. Feature map: `features/README.md`. Keep the map honest with
`/maintain-verification-skill` as the app changes.
