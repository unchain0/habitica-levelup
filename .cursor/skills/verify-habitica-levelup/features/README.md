# habitica-levelup verification map

This directory is the maintained source for verifying user-facing behavior of
the habitica-levelup CLI bot. Read this index before driving, then use the
matching feature file as the recipe.

## Baseline preconditions

- Work from the repository root on a clean checkout.
- Run `.cursor/skills/verify-habitica-levelup/scripts/launch.sh` to create a
  disposable scratch dir under `/tmp/verify-habitica-levelup/<run-id>/` with a
  fake `.env` only.
- Run `.cursor/skills/verify-habitica-levelup/scripts/doctor.sh "$SCRATCH"` and
  require `doctor: ok`.
- Owner rule: do not launch this app. Do not run `uv run python main.py`,
  `uv run task run`, or Docker. Do not call the Habitica API.
- Drive through offline pytest helpers only. Use fake credentials from scratch.
- Never drive a human-started bot process or a production `.env`.

## Driving conventions

- Start every recipe from a doctor-healthy scratch dir.
- Prefer exact pytest node ids and file paths from this map over ad-hoc scripts.
- Treat every command as literal. Keep flags and module paths unchanged.
- Run drives through
  `.cursor/skills/verify-habitica-levelup/scripts/drive.sh "$SCRATCH" <feature-id>`.
- Copy pytest output into the skill `evidence/` tree. Cleanup must not remove it.
- Live CLI proof is **not run (owner rule: do not launch this app)** on every
  feature until that rule is lifted by the repository owner.

## Proof and skip reporting

- Capture the pytest command, exit code, and failing/passing node ids.
- Mutation-style proof in this codebase is mock call counts and pure return
  values (settings validation, level decisions, shutdown flags).
- Record the feature id and entry point with every artifact.
- Report an unreachable path with the unmet precondition.
- Do not report a skipped live launch as verified through tests alone without
  the static note.

## Feature entry contract

Each feature file starts with an H1 title and one paragraph describing the
user-visible behavior. It then uses exactly four H2 sections in this order.

1. `Sub-features` lists short IDs with one line for each behavior.
2. `How to get to it (user POV)` lists every user entry point.
3. `Driving it with verify-habitica-levelup` starts with `Preconditions:` and
   uses labeled bullets that pair each user action with an exact command and
   observable result.
4. `Gotchas` lists traps that can waste or invalidate a verification run.

Keep implementation details that are not user-observable out of the map. Name
user paths, stable env keys, commands, constants from source, and proof.

## Features

- [Config validation](./config-validation.md) covers required env vars,
  placeholder rejection, logging setup, and CLI config failure exit.
- [Farm loop](./farm-loop.md) covers Auto Farm XP task creation, scoring,
  progress logging, rate-limit delay, and stop at level 999.
- [Account maintenance](./account-maintenance.md) covers strength allocation,
  party quest accept, and Enchanted Armoire purchase above gold threshold.
- [Auth and resilience](./auth-and-resilience.md) covers fatal auth errors,
  rate-limit retry, and circuit breaker open/close.
- [Graceful shutdown](./graceful-shutdown.md) covers SIGINT/SIGTERM,
  shutdown_event stop, and no work when shutdown is already set.
