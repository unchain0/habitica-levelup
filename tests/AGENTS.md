# tests/ - Test Suite

**Framework:** pytest  
**Coverage:** 100% required  
**Files:** 12 test modules

## OVERVIEW

pytest suite with contracts, integration, and unit tests.

## STRUCTURE

```
tests/
├── contracts/              # API contract tests
│   └── test_habitica_api_contracts.py
├── integration/            # E2E tests
│   └── test_bot_integration.py
├── test_architecture.py    # MASA layer checks
├── test_bot.py             # BotRunner tests
├── test_config.py          # Settings validation
├── test_core.py            # Core logic
├── test_engines.py         # Leveling engine
├── test_infrastructure.py  # Gateway, retry
├── test_logging_config.py  # Loguru setup
├── test_main.py            # Entry point
└── test_tasks.py           # Farm task creation
```

## WHERE TO LOOK

| Task | File | Notes |
|------|------|-------|
| Architecture | `test_architecture.py` | Import order, layer violations |
| Config | `test_config.py` | Placeholder rejection |
| Engines | `test_engines.py` | Level decisions, pure functions |
| Gateway | `test_infrastructure.py` | HabiticaGateway, retry |
| Bot | `test_bot.py` | Signal handling, shutdown |
| Contracts | `contracts/test_habitica_api_contracts.py` | API schemas |
| Integration | `integration/test_bot_integration.py` | Full flow |

## COMMANDS

```bash
uv run task test              # Quick test run
uv run task test-cov          # Coverage (100% required)
uv run pytest tests/integration/ -v  # Integration only
```

## CONVENTIONS

- **100% coverage** enforced (fail_under = 100)
- **asyncio_mode = auto** (pytest-asyncio)
- **Mocks** for external APIs (habiticalib)
- **Table-driven** tests where applicable

## ANTI-PATTERNS

| Violation | Why |
|-----------|-----|
| Real API calls in unit tests | Use mocks for Habitica API |
| <100% coverage | CI fails |
| Skip pre-existing failures | Document, don't skip |
