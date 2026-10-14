# Config validation

Config validation stops the bot before any Habitica call when `USER_ID` or
`API_TOKEN` is missing, empty, or a known placeholder, and applies `LOG_LEVEL`
to console logging.

## Sub-features

- `config-required-env` requires non-empty `USER_ID` and `API_TOKEN`.
- `config-reject-placeholder` rejects `changeme`, `placeholder`, `your-user-id`,
  `your-api-token`, and empty string (case-insensitive).
- `config-default-log-level` defaults `LOG_LEVEL` to `INFO` when unset.
- `config-forbid-extra` rejects unknown settings fields (`extra = forbid`).
- `config-cli-exit` exits process status 1 on settings errors from `cli.main`.
- `config-logging-handlers` attaches stderr and
  `~/.local/share/habitica-levelup/app.log` handlers via `setup_logging`.

## How to get to it (user POV)

- Copy `.env.example` to `.env` and edit `USER_ID`, `API_TOKEN`, optional
  `LOG_LEVEL`.
- Run `uv run python main.py` or `uv run task run` (live path blocked here).
- Export the same variables in the process environment instead of a file.

## Driving it with verify-habitica-levelup

Preconditions:

- Scratch dir from `scripts/launch.sh` and `scripts/doctor.sh` reports ok.
- Owner rule: do not launch this app. Live `main.py` proof is
  **not run (owner rule: do not launch this app)**.
- No real Habitica credentials in the environment under test.

- **Valid settings.** Construct settings with fake non-placeholder values.
  Run `.cursor/skills/verify-habitica-levelup/scripts/drive.sh "$SCRATCH" config-validation`.
  `tests/test_config.py::TestSettings::test_settings_valid` passes and
  `LOG_LEVEL` can be `DEBUG`.
- **Defaults.** `test_settings_defaults` passes with `LOG_LEVEL == "INFO"`.
- **Missing / empty.** `test_settings_missing_user_id`,
  `test_settings_missing_api_token`, `test_settings_empty_user_id`, and
  `test_settings_empty_api_token` raise `ValidationError`.
- **Placeholders.** `test_settings_placeholder_changeme`,
  `test_settings_placeholder_placeholder`, and
  `test_settings_placeholder_your_user_id` raise errors mentioning placeholder.
- **CLI config error.** `tests/test_main.py::TestMain::test_main_config_error`
  exits with code 1 when `Settings` fails.
- **Logging.** `tests/test_logging_config.py` shows stderr and file handlers and
  log directory creation under the patched home.
- **Proof.** Evidence dir contains pytest transcript exit 0 and `PROOF.md`.
  `STATIC_NOTE.md` records **not run (owner rule: do not launch this app)** for
  the live CLI path.

## Gotchas

- Placeholder check is case-insensitive on the whole value, not a substring.
  `your-user-id-here` from `.env.example` is not in the exact reject set; the
  example uses `your-user-id-here` / `your-api-token-here`, while the validator
  lists `your-user-id` and `your-api-token` exactly. Drive the tested values.
- `extra = forbid` means typos in env keys fail closed.
- Never print scratch `.env` contents into evidence.
- Live launch with a bad `.env` would log `Configuration error: …` and exit 1;
  that path is not run under the owner rule.
