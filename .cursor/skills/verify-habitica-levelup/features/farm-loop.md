## Sub-features
- CLI start; signal handling (SIGINT/SIGTERM); circuit breaker

## How to get to it (user POV)
Run `uv run python main.py` with `.env` set to real Habitica credentials.

## Driving it with harness
Launch CLI, confirm process starts, check log appears at `~/.local/share/habitica-levelup/app.log`.

## Gotchas
Auth token must exist at runtime (generate, never hardcode); bot stops immediately on `NotAuthorizedError`.
