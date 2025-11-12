# KoraStats MCP Server Notes

## Overview
- **Service name:** KoraStats
- **Server binary:** `korastats_server.py`
- **Purpose:** Query Korastats API for season, match, and event data.

## Authentication & Configuration
- Requires Docker secret `KORASTATS_API_KEY`; exposed as environment variable in the container.
- Optional overrides:
  - `KORASTATS_API_BASE_URL` (default `https://korastats.pro/pro/api.php`)
  - `KORASTATS_TIMEOUT_SECONDS` (default `15`)
- If the API key is missing or blank, tools return a user-facing error (`❌`).

## Tools
- `list_seasons(page_number="", page_size="")`
  - Validates numeric inputs (defaults page=1, size=20).
  - Returns a formatted summary of season metadata.
- `list_season_matches(season_id="", page_number="", page_size="")`
  - Requires `season_id`; validates pagination inputs.
  - Summarizes match listings with score and status.
- `get_match_events(match_id="", limit="")`
  - Requires `match_id`; optional `limit` (default 10, max 50).
  - Condenses the event timeline into readable bullet points.

## Logging & Error Handling
- Logging configured at INFO level to `stderr` via `logging.basicConfig`.
- Every tool returns human-readable strings with emoji markers for status.
- HTTP failures handled with status-aware messaging; JSON parsing errors surfaced with a friendly explanation.

## Docker Runtime
- Based on `python:3.11-slim`.
- Installs dependencies from `requirements.txt`.
- Runs as non-root user `mcpuser`.
- Entrypoint executes `python korastats_server.py`.

## Testing Tips
```bash
export KORASTATS_API_KEY="your-api-key"
python korastats_server.py  # stdio server
```
- Use `echo '{"jsonrpc":"2.0","method":"tools/list","id":1}' | python korastats_server.py` to validate MCP wiring.

## Maintenance Guidelines
- Keep tool docstrings to a single line.
- Ensure new tools follow the same error-handling and formatting conventions.
- Update documentation (README, catalogs) whenever a new tool is added.
