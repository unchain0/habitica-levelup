# Habitica Level Up Bot

A high-performance CLI tool for auto-leveling Habitica characters with optimized async patterns, fault tolerance, comprehensive logging, automatic task creation, CI/CD pipeline, and 100% test coverage.

## Features

- **Automatic Task Creation**: Creates a "Auto Farm XP" habit automatically if it doesn't exist
- **Maximum Rewards**: Task created with HARD difficulty (2.0x XP/Gold multiplier)
- **Concurrent API Calls**: ~2x faster with parallel quest farming and stat allocation
- **Rate Limiting**: Built-in delays and exponential backoff to avoid API bans
- **Circuit Breaker**: Prevents hammering the API when experiencing issues
- **Graceful Shutdown**: Handles SIGINT/SIGTERM signals properly
- **Environment Validation**: pydantic-settings for type-safe configuration
- **Comprehensive Logging**: Console output + rotating file logs
- **Retry Logic**: Exponential backoff for transient failures
- **100% Test Coverage**: Full test suite with pytest including unit, integration, and contract tests
- **CI/CD Pipeline**: GitHub Actions with automated testing, linting, and security checks
- **Pre-commit Hooks**: Automated code quality checks before commits

## Project Structure

```
habitica-levelup/
├── src/                          # Source code
│   ├── __init__.py               # Package exports
│   ├── config.py                 # Environment configuration
│   ├── core.py                   # Circuit breaker pattern
│   ├── infrastructure.py         # HTTP client and retry logic
│   ├── logging_config.py         # Logging setup
│   ├── bot.py                    # Main application logic
│   └── tasks.py                  # Automatic task management
├── tests/                        # Test suite (100% coverage)
│   ├── __init__.py
│   ├── contracts/                # Contract tests (API contracts)
│   │   ├── __init__.py
│   │   └── test_habitica_api_contracts.py
│   ├── integration/              # Integration tests
│   │   ├── __init__.py
│   │   └── test_bot_integration.py
│   ├── test_config.py            # Unit tests
│   ├── test_core.py
│   ├── test_infrastructure.py
│   ├── test_logging_config.py
│   ├── test_tasks.py
│   ├── test_bot.py
│   └── test_main.py
├── .github/workflows/            # CI/CD pipelines
│   └── ci.yml
├── .pre-commit-config.yaml       # Pre-commit hooks
├── main.py                       # Entry point
├── .env.example                  # Environment template
├── pyproject.toml                # Dependencies and taskipy scripts
└── README.md                     # This file
```

## Installation

### Requirements

- Python >=3.12
- uv (recommended) or pip

### Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd habitica-levelup
```

2. Create and activate virtual environment:
```bash
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. Install dependencies:
```bash
uv pip install -e .
```

4. Install dev dependencies (for testing):
```bash
uv pip install -e ".[dev]"
```

5. Install pre-commit hooks:
```bash
task install-hooks
```

## Configuration

1. Copy the environment template:
```bash
cp .env.example .env
```

2. Edit `.env` with your Habitica credentials:
```bash
# Get these from: https://habitica.com/user/settings/api
USER_ID=your-user-id-here
API_TOKEN=your-api-token-here

# Optional: Set logging level (DEBUG, INFO, WARNING, ERROR)
LOG_LEVEL=INFO
```

Note: The bot automatically creates a farm task - no need to manually provide FARM_QUEST_ID anymore!

## Usage

### Running the Bot

Using taskipy (recommended):
```bash
task run
```

Or directly:
```bash
python main.py
```

The bot will:
1. Validate your configuration
2. Search for existing "Auto Farm XP" task or create one with HARD difficulty
3. Check current level
4. Farm quests and allocate stat points until level 999
5. Log progress every 10 levels

### Graceful Shutdown

Press `Ctrl+C` to stop the bot gracefully. It will:
- Complete the current iteration
- Log the final level reached
- Clean up resources

## Development

### Taskipy Commands

Available shortcuts (defined in pyproject.toml):

```bash
# Run tests
task test

# Run tests with coverage (requires 100%)
task test-cov

# Run linter
task lint

# Format code
task format

# Type checking
task type-check

# Run the bot
task run

# Install pre-commit hooks
task install-hooks

# Run pre-commit hooks manually
task pre-commit
```

### Running Tests

```bash
# Run all tests
task test

# Run with coverage report (requires 100% coverage)
task test-cov

# Run specific test file
pytest tests/test_config.py -v

# Run only unit tests
pytest tests/test_*.py -v

# Run only integration tests
pytest tests/integration/ -v

# Run only contract tests
pytest tests/contracts/ -v
```

### Code Quality

The project uses:
- **ruff**: Linting and formatting
- **mypy**: Type checking
- **bandit**: Security linting
- **pytest**: Testing framework
- **pytest-asyncio**: Async test support
- **pytest-cov**: Coverage reporting
- **pydantic**: Type-safe configuration
- **loguru**: Structured logging

## Architecture

### Layered Design

The project follows a layered architecture:

- **Configuration Layer** (`config.py`): Environment variable validation using pydantic-settings
- **Core Layer** (`core.py`): Domain utilities like circuit breaker pattern
- **Infrastructure Layer** (`infrastructure.py`): HTTP client, retry logic, session management
- **Task Management Layer** (`tasks.py`): Automatic task creation and management
- **Application Layer** (`bot.py`): Main business logic

### Key Optimizations

1. **Automatic Task Creation**: Creates "Auto Farm XP" habit with HARD difficulty automatically
2. **Async Concurrency**: Uses `asyncio.gather()` to run quest farming and stat allocation in parallel
3. **Connection Pooling**: Optimized aiohttp ClientSession with connection limits and keepalive
4. **Exponential Backoff**: Retries failed requests with 1s, 2s, 4s delays
5. **Circuit Breaker**: Stops requests after 5 consecutive failures, waits 1 minute before retrying
6. **Signal Handling**: Proper SIGINT/SIGTERM handling for graceful shutdown

## Logging

Logs are written to:
- **Console**: Colored output for development
- **File**: `~/.local/share/habitica-levelup/app.log`
  - Rotates at 10 MB
  - Keeps 7 days of history
  - Compressed old logs

## Error Handling

The bot handles various error scenarios:

- **Rate Limiting**: Exponential backoff on 429 responses
- **Authentication Errors**: Stops immediately on 401/403
- **Network Timeouts**: Retries with backoff
- **API Failures**: Circuit breaker prevents hammering

## Testing

The project maintains **100% test coverage** using pytest and pytest-asyncio.

### Test Types

1. **Unit Tests**: Test individual components in isolation
   - `test_config.py`, `test_core.py`, `test_infrastructure.py`, etc.

2. **Integration Tests**: Test component interactions
   - `tests/integration/test_bot_integration.py`

3. **Contract Tests**: Verify API contracts with Habitica
   - `tests/contracts/test_habitica_api_contracts.py`

### Test Structure

```
tests/
├── test_config.py              # Settings validation tests
├── test_core.py                # Circuit breaker tests
├── test_infrastructure.py      # HTTP client and retry tests
├── test_logging_config.py      # Logging setup tests
├── test_tasks.py               # Task creation/management tests
├── test_bot.py                 # Main bot logic tests
├── test_main.py                # Entry point tests
├── integration/                # Integration tests
│   └── test_bot_integration.py
└── contracts/                  # Contract tests
    └── test_habitica_api_contracts.py
```

### Running Coverage

```bash
# Generate coverage report with 100% requirement
task test-cov

# View HTML report
open htmlcov/index.html

# View terminal report with missing lines
pytest tests/ --cov=src --cov-report=term-missing
```

## CI/CD Pipeline

The project uses GitHub Actions for continuous integration and deployment:

### CI Workflow (`.github/workflows/ci.yml`)

Runs on every push and pull request:

1. **Lint & Format**: Runs ruff linter and formatter
2. **Type Checking**: Runs mypy type checker
3. **Tests**: Runs full test suite with 100% coverage requirement
4. **Security**: Runs bandit security audit
5. **Integration Tests**: Runs integration test suite
6. **Pre-commit Hooks**: Runs all pre-commit hooks

### Pipeline Jobs

| Job | Description |
|-----|-------------|
| `lint` | Code linting and formatting checks |
| `type-check` | Static type checking with mypy |
| `test` | Unit tests with coverage reporting |
| `security` | Security vulnerability scanning |
| `integration-test` | Integration tests |
| `pre-commit` | Pre-commit hooks validation |

### Status Checks

All jobs must pass before merging:
- 100% test coverage required
- No linting errors
- No type checking errors
- No security vulnerabilities
- All integration tests passing

## Pre-commit Hooks

Pre-commit hooks are configured to run automatically before each commit:

- **ruff-lint**: Lints Python code
- **ruff-format**: Formats Python code
- **mypy**: Type checks Python code
- **pytest-cov**: Runs tests with coverage (requires 100%)

To run hooks manually:
```bash
task pre-commit
```

To skip hooks (not recommended):
```bash
git commit --no-verify
```

## Security

- Credentials are loaded from environment variables
- `.env` file should never be committed (already in `.gitignore`)
- API tokens are validated at startup
- No sensitive data in logs
- Bandit security scanning in CI/CD pipeline

## License

[Your License Here]

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Ensure tests pass with 100% coverage: `task test-cov`
5. Run linter: `task lint`
6. Run type checker: `task type-check`
7. Run security scan: `bandit -r src/`
8. Submit a pull request

All PRs must pass CI checks before merging.

## Troubleshooting

### Configuration Errors

If you see:
```
Configuration error: 1 validation error for Settings
USER_ID
  Value cannot be a placeholder: your-user-id-here
```

Make sure you've updated `.env` with your actual credentials, not the placeholder values.

### Rate Limiting

If the bot is rate limited, it will automatically retry with exponential backoff. This is normal behavior.

### Task Creation

If the bot cannot create the farm task:
- Check your API credentials
- Ensure you have permission to create tasks
- Check the logs for specific error messages

### Logs Location

If you need to check logs:
```bash
# View latest logs
tail -f ~/.local/share/habitica-levelup/app.log

# Search for errors
grep ERROR ~/.local/share/habitica-levelup/app.log
```

### Test Failures

If tests fail:
```bash
# Run with verbose output
pytest tests/ -v --tb=short

# Run specific test
pytest tests/test_config.py::test_settings -v

# Run with coverage debugging
pytest tests/ --cov=src --cov-report=term-missing -v
```

### CI/CD Failures

If CI/CD pipeline fails:
1. Check the GitHub Actions logs
2. Run the failing job locally:
   ```bash
   task lint
   task type-check
   task test-cov
   ```
3. Fix the issues and push again

### Pre-commit Hook Failures

If pre-commit hooks fail:
```bash
# Run hooks manually to see errors
task pre-commit

# Fix auto-fixable issues
task format

# Run tests to check coverage
task test-cov
```
