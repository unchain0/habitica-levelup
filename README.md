# Habitica Level Up Bot

CLI tool for auto-leveling Habitica characters. Farms XP automatically until level 999.

## Features

- **Automatic Task Creation**: Creates "Auto Farm XP" habit automatically
- **Maximum Rewards**: HARD difficulty (2.0x XP/Gold multiplier)
- **Concurrent API Calls**: Parallel quest farming and stat allocation
- **Rate Limiting**: Built-in delays to avoid API bans
- **Fault Tolerance**: Exponential backoff retry logic
- **Graceful Shutdown**: Handles SIGINT/SIGTERM properly
- **Comprehensive Logging**: Console + file logs with rotation

## Quick Start

### Requirements

- Docker and Docker Compose (recommended)
- Or Python >=3.12

### Docker (Recommended)

```bash
# Clone repo
git clone https://github.com/unchain0/habitica-levelup.git
cd habitica-levelup

# Setup environment
cp .env.example .env
# Edit .env with your Habitica credentials

# Start bot
docker-compose up -d

# View logs
docker-compose logs -f
```

To stop: `docker-compose down`

### Python

```bash
# Clone and setup
git clone https://github.com/unchain0/habitica-levelup.git
cd habitica-levelup

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install
pip install -e .

# Configure
cp .env.example .env
# Edit .env with your Habitica credentials

# Run
python main.py
```

## Configuration

Create `.env` file from template:

```bash
cp .env.example .env
```

### Required Variables

| Variable | Description | Source |
|----------|-------------|--------|
| `USER_ID` | Habitica User ID | https://habitica.com/user/settings/api |
| `API_TOKEN` | Habitica API Token | https://habitica.com/user/settings/api |

### Optional Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `LOG_LEVEL` | Logging verbosity | `INFO` |

### Example .env

```bash
USER_ID=a1b2c3d4-e5f6-7890-abcd-ef1234567890
API_TOKEN=abcd1234-ef56-7890-abcd-ef1234567890
LOG_LEVEL=INFO
```

**Security**: Never commit `.env`. It's already in `.gitignore`.

## Usage

### Running

```bash
# Docker
docker-compose up -d
docker-compose logs -f

# Python
python main.py
```

Bot will:
1. Validate configuration
2. Create "Auto Farm XP" task (HARD difficulty) if missing
3. Farm quests and allocate stats until level 999
4. Log progress every 10 levels

### Stop Bot

Press `Ctrl+C` (Python) or run `docker-compose down` (Docker).

Bot completes current iteration before stopping.

## Logging

- **Console**: Colored output
- **File**: `~/.local/share/habitica-levelup/app.log`
  - Rotates at 10 MB
  7 days retention
  - Compressed archives

View logs:
```bash
# Docker
docker-compose logs -f

# File
tail -f ~/.local/share/habitica-levelup/app.log
```

## Troubleshooting

### Configuration Error

```
Configuration error: 1 validation error for Settings
USER_ID
  Value cannot be a placeholder: your-user-id-here
```

**Fix**: Replace placeholder values in `.env` with real credentials from https://habitica.com/user/settings/api

### Rate Limiting

Bot retries automatically with exponential backoff. This is normal behavior.

### Task Creation Failed

- Check API credentials
- Verify account permissions
- Check logs: `docker-compose logs -f` or `tail -f ~/.local/share/habitica-levelup/app.log`

### Logs Location

```bash
# View latest
tail -f ~/.local/share/habitica-levelup/app.log

# Search errors
grep ERROR ~/.local/share/habitica-levelup/app.log
```

## Security

- Credentials via environment variables only
- `.env` never committed
- API tokens validated at startup
- No sensitive data in logs

## License

[Your License Here]
