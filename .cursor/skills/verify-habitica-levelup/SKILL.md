---
name: verify-habitica-levelup
description: "Verify habitica-levelup (unchain0/habitica-levelup): CLI bot that farms Habitica XP to level 999. Use when changes need proof against the real app."
---

# verify-habitica-levelup

- Launch: `uv run python main.py` (needs `.env` with API token, generated at runtime; never commit)
- Doctor: `pgrep -af "python main.py"` and check `.env` exists; auth fails = stop (no retry)
- Drive: CLI via `main.py`; observe console/log at `~/.local/share/habitica-levelup/app.log`
- Evidence: `tests/` output + log snippet to `/tmp/verify-habitica-levelup-evidence/` (kept out of git by `.gitignore`)
- Cleanup: kill started process; do not remove evidence dir
