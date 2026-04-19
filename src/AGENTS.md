# src/ - MASA Implementation

**Layer:** Domain → Integrations → Engines → Services → Delivery  
**Lines:** ~600  
**Files:** 15 Python modules

## OVERVIEW

MASA 5-layer architecture with strict unidirectional dependencies.

## STRUCTURE

```
src/
├── domain_models/          # Frozen dataclasses
│   ├── user_status.py      # Level, gold, stat points
│   ├── farm_task.py        # Task ID for XP farming
│   └── party_quest_status.py  # Quest acceptance state
├── engines/                # Pure business logic
│   └── leveling.py         # Level decisions, stat allocation rules
├── integrations/           # External APIs
│   ├── habitica_gateway.py # Habitica client wrapper
│   ├── retry.py            # Exponential backoff
│   ├── retry_policy.py     # Retry configuration
│   └── session.py          # HTTP session management
├── services/               # Orchestration
│   ├── levelup_service.py  # Main farming loop
│   └── resilience.py       # Circuit breaker pattern
└── delivery/               # Entry points
    ├── cli.py              # main() function
    ├── bot_runner.py       # Signal handlers
    ├── settings.py         # Pydantic configuration
    └── logging.py          # Loguru setup
```

## WHERE TO LOOK

| Task | File | Notes |
|------|------|-------|
| Entry | `delivery/cli.py` | main() → LevelUpBot |
| Config | `delivery/settings.py` | USER_ID, API_TOKEN validation |
| Bot loop | `delivery/bot_runner.py` | SIGINT/SIGTERM handling |
| Level logic | `engines/leveling.py` | Pure functions, no side effects |
| API calls | `integrations/habitica_gateway.py` | habiticalib wrapper |
| Service | `services/levelup_service.py` | Farm loop, 999 target |
| Resilience | `services/resilience.py` | Circuit breaker |
| Domain | `domain_models/*.py` | Frozen dataclasses only |

## CONVENTIONS

- **Frozen dataclasses** for all domain models (immutable)
- **Pure functions** in engines/ (no I/O, no state)
- **Async throughout** (asyncio, async/await)
- **Unidirectional deps**: domain → engines → services → integrations → delivery
- **Never import upward**: services cannot import from delivery

## ANTI-PATTERNS

| Violation | Location | Fix |
|-----------|----------|-----|
| Business logic in delivery | delivery/cli.py | Keep thin, delegate to services |
| API calls in engines | engines/leveling.py | Only pure logic, no I/O |
| Domain models in integrations | integrations/ | Use models from domain_models/ |
| Upward imports | Any | Import only from lower layers |
| Mutable domain models | domain_models/ | Must use frozen=True |
