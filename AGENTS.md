# Habitica Level Up Bot

**Stack:** Python 3.14 (futuristic), uv, pydantic, loguru  
**Architecture:** MASA (5-layer unidirectional)  
**Generated:** 2026-04-19

## OVERVIEW

CLI tool for auto-leveling Habitica characters. Farms XP automatically until level 999.

## STRUCTURE

```
habitica-levelup/
├── src/                    # MASA architecture layers
│   ├── domain_models/      # UserStatus, FarmTask, PartyQuestStatus
│   ├── engines/            # Pure functions: leveling decisions
│   ├── services/           # LevelUpService, CircuitBreaker
│   ├── integrations/       # HabiticaGateway, retry logic
│   └── delivery/           # CLI, settings, logging, bot_runner
├── tests/                  # pytest with 100% coverage
│   ├── contracts/          # API contract tests
│   └── integration/        # End-to-end bot tests
├── scripts/                # CI helper scripts
├── main.py                 # Entry point (asyncio.run)
└── pyproject.toml          # uv + taskipy + ruff + mypy + pytest
```

## WHERE TO LOOK

| Task | Location | Notes |
|------|----------|-------|
| Entry point | `main.py` | Imports from `src.delivery.cli` |
| CLI logic | `src/delivery/cli.py` | Settings validation, bot init |
| Bot runner | `src/delivery/bot_runner.py` | Signal handlers, main loop |
| Core logic | `src/engines/leveling.py` | Pure functions (level, stats, armoire) |
| API client | `src/integrations/habitica_gateway.py` | Habitica API wrapper |
| Service layer | `src/services/levelup_service.py` | Orchestrates farming loop |
| Domain models | `src/domain_models/` | Dataclasses (frozen) |
| Config | `src/delivery/settings.py` | Pydantic Settings, env validation |

## COMMANDS

```bash
# Setup
uv sync --group dev          # Install dev dependencies
uv run task install-hooks    # Install pre-commit hooks

# Development
uv run task run              # python main.py
uv run task test             # pytest -v
uv run task test-cov         # pytest --cov=src (100% required)
uv run task lint             # ruff check .
uv run task format           # ruff format .
uv run task type-check       # mypy src/

# Full CI locally
bash scripts/run-ci-checks.sh all

# Docker
docker-compose up -d         # Production container
docker-compose --profile dev up -d  # Dev with live reload
```

## CONVENTIONS

- **Python 3.14** target (`>=3.14,<3.15`) - futuristic constraint
- **uv** for dependency management (not pip/poetry)
- **ruff** for lint + format (line-length 100, double quotes)
- **mypy** strict type checking
- **pytest** with asyncio_mode=auto
- **100% coverage** enforced (fail_under = 100)
- **MASA layers** strictly enforced: domain → integrations → engines → services → delivery
- **Dataclasses** frozen for domain models
- **Loguru** for logging (not stdlib logging)
- **Pydantic Settings** for config with placeholder validation

## ANTI-PATTERNS

| Forbidden | Location | Why |
|-----------|----------|-----|
| Never commit secrets | README.md:93 | Security - credentials in .env |
| Placeholder credentials | settings.py:33 | Rejects: changeme, placeholder, your-user-id, your-api-token |
| Retry auth failures | retry.py:34-36 | NotAuthorizedError re-raised immediately (no retry) |
| E501 line length | pyproject.toml:84 | Ignored - handled by formatter |
| Skip type checking | — | mypy strict mode enabled |
| <100% coverage | pyproject.toml:65 | CI fails if coverage < 100% |

## UNIQUE STYLES

- **Root main.py** - Entry point at root (not src/__main__.py)
- **Flat src/** - Namespace package directly in src/ (not src/habitica_levelup/)
- **Scripts outside src/** - CI helpers in /scripts (unusual for small projects)
- **tests/contracts/** - API contract tests (non-standard naming)
- **Circuit breaker** - Custom resilience pattern in services/
- **Rate limiting** - Built-in delays (0.5s) between iterations

## NOTES

- Bot runs until level 999 or SIGINT/SIGTERM
- Completes current iteration before shutdown
- Logs to both console and ~/.local/share/habitica-levelup/app.log
- Docker runs as non-root user (appuser, UID 1000)
