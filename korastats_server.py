#!/usr/bin/env python3
"""Simple KoraStats MCP Server - Provides Korastats football insights."""

import os
import sys
import logging
from datetime import datetime, timezone

import httpx
from mcp.server.fastmcp import FastMCP


LOG_LEVEL = os.environ.get("MCP_LOG_LEVEL", "WARNING").upper()
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.WARNING),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stderr,
)
logger = logging.getLogger("korastats-server")

mcp = FastMCP("korastats", stateless_http=True)

API_BASE_URL = os.environ.get("KORASTATS_API_BASE_URL", "https://korastats.pro/pro/api.php")
_timeout_env = os.environ.get("KORASTATS_TIMEOUT_SECONDS", "15")
try:
    DEFAULT_TIMEOUT_SECONDS = float(_timeout_env)
except ValueError:
    logger.warning("Invalid KORASTATS_TIMEOUT_SECONDS=%s, falling back to 15 seconds", _timeout_env)
    DEFAULT_TIMEOUT_SECONDS = 15.0


def _get_api_key() -> str:
    key = os.environ.get("KORASTATS_API_KEY", "")
    return key.strip()


async def _perform_request(api_name: str, extra_params: dict) -> tuple:
    api_key = _get_api_key()
    if not api_key:
        return False, "❌ Error: Missing Korastats API key. Set Docker secret KORASTATS_API_KEY."

    params = {
        "module": "api",
        "api": api_name,
        "version": "V2",
        "response": "json",
        "lang": "en",
        "key": api_key,
    }

    for key, value in extra_params.items():
        if isinstance(value, str):
            params[key] = value
        else:
            params[key] = str(value)

    logger.info("Calling API %s with params %s", api_name, {k: v for k, v in params.items() if k != "key"})

    timeout = httpx.Timeout(DEFAULT_TIMEOUT_SECONDS)

    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.get(API_BASE_URL, params=params)
            response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        logger.error("Korastats API returned %s for %s", exc.response.status_code, api_name)
        return False, f"❌ API Error: {exc.response.status_code}"
    except Exception as exc:
        logger.error("Korastats request failed for %s: %s", api_name, exc)
        return False, f"❌ Error: {str(exc)}"

    try:
        payload = response.json()
    except ValueError as exc:
        logger.error("Korastats JSON parse error for %s: %s", api_name, exc)
        return False, "❌ Error: Received invalid JSON from Korastats."

    return True, payload


def _iso_timestamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _format_score(score: dict) -> str:
    if not isinstance(score, dict):
        return "N/A"
    home = score.get("home")
    away = score.get("away")
    if home is None or away is None:
        return "N/A"
    return f"{home}-{away}"


@mcp.tool()
async def list_seasons(page_number: str = "", page_size: str = "") -> str:
    """List Korastats seasons with pagination support."""
    page_value = 1
    size_value = 20

    if page_number.strip():
        try:
            page_value = max(1, int(page_number.strip()))
        except ValueError:
            return f"❌ Error: Invalid page_number value: {page_number}"

    if page_size.strip():
        try:
            size_value = max(1, int(page_size.strip()))
        except ValueError:
            return f"❌ Error: Invalid page_size value: {page_size}"

    success, payload = await _perform_request(
        "SeasonList",
        {"page_number": str(page_value), "page_size": str(size_value)},
    )

    if not success:
        return payload

    root = payload.get("root", {})
    if not root.get("result"):
        message = root.get("message", "Korastats API returned an error.")
        return f"❌ API Error: {message}"

    obj = root.get("object", {})
    seasons = obj.get("Data", [])

    if not seasons:
        return "⚠️ No seasons found for the requested page."

    preview = seasons[: min(len(seasons), 5)]
    lines = []
    for season in preview:
        season_id = season.get("id", "N/A")
        name = season.get("name", "Unknown")
        start = season.get("startDate", "Unknown")
        end = season.get("endDate", "Unknown")
        tournament = ((season.get("tournament") or {}).get("name")) or "Unknown"
        lines.append(f"- ID {season_id}: {name} | {tournament} | {start} → {end}")

    lines_text = "\n".join(lines)

    total_records = obj.get("total_records", "Unknown")
    total_pages = obj.get("pages", "Unknown")
    current_page = obj.get("current_page", "Unknown")
    message = root.get("message", "Success")

    return f"""📊 Seasons Overview:
- Records on page: {len(seasons)}
- Total records: {total_records}
- Page: {current_page} of {total_pages}

Top seasons:
{lines_text}

Summary: {message} | Generated at {_iso_timestamp()}"""


@mcp.tool()
async def list_season_matches(season_id: str = "", page_number: str = "", page_size: str = "") -> str:
    """List matches for a Korastats season with pagination."""
    if not season_id.strip():
        return "❌ Error: season_id is required."

    try:
        season_value = int(season_id.strip())
    except ValueError:
        return f"❌ Error: Invalid season_id value: {season_id}"

    page_value = 1
    size_value = 20

    if page_number.strip():
        try:
            page_value = max(1, int(page_number.strip()))
        except ValueError:
            return f"❌ Error: Invalid page_number value: {page_number}"

    if page_size.strip():
        try:
            size_value = max(1, int(page_size.strip()))
        except ValueError:
            return f"❌ Error: Invalid page_size value: {page_size}"

    success, payload = await _perform_request(
        "SeasonMatchList",
        {
            "season_id": str(season_value),
            "page_number": str(page_value),
            "page_size": str(size_value),
        },
    )

    if not success:
        return payload

    root = payload.get("root", {})
    if not root.get("result"):
        message = root.get("message", "Korastats API returned an error.")
        return f"❌ API Error: {message}"

    obj = root.get("object", {})
    matches = obj.get("Data", [])

    if not matches:
        return "⚠️ No matches found for the supplied season."

    preview = matches[: min(len(matches), 5)]
    lines = []
    for match in preview:
        match_id = match.get("matchId", "N/A")
        home = ((match.get("home") or {}).get("name")) or "Home"
        away = ((match.get("away") or {}).get("name")) or "Away"
        kickoff = match.get("dateTime", "Unknown")
        status = ((match.get("status") or {}).get("name")) or "Unknown"
        score = _format_score(match.get("score"))
        lines.append(f"- #{match_id}: {home} vs {away} | {kickoff} | Score {score} | Status {status}")

    lines_text = "\n".join(lines)
    rows_count = obj.get("RowsCount", "Unknown")
    total_pages = obj.get("PageCount", "Unknown")
    message = root.get("message", "Success")

    return f"""📊 Match Overview:
- Matches on page: {len(matches)}
- Total matches: {rows_count}
- Page: {page_value} of {total_pages}

Upcoming details:
{lines_text}

Summary: {message} | Generated at {_iso_timestamp()}"""


@mcp.tool()
async def get_match_events(match_id: str = "", limit: str = "") -> str:
    """Summarize Korastats match events with optional limit."""
    if not match_id.strip():
        return "❌ Error: match_id is required."

    try:
        match_value = int(match_id.strip())
    except ValueError:
        return f"❌ Error: Invalid match_id value: {match_id}"

    limit_value = 10
    if limit.strip():
        try:
            limit_value = max(1, min(50, int(limit.strip())))
        except ValueError:
            return f"❌ Error: Invalid limit value: {limit}"

    success, payload = await _perform_request(
        "MatchEventList",
        {"match_id": str(match_value)},
    )

    if not success:
        return payload

    if not payload.get("result"):
        message = payload.get("message", "Korastats API returned an error.")
        return f"❌ API Error: {message}"

    data = payload.get("data", {})
    match = data.get("match")
    if not match:
        return "⚠️ No match details returned for the given match_id."

    home = ((match.get("home") or {}).get("name")) or "Home"
    away = ((match.get("away") or {}).get("name")) or "Away"
    status = ((match.get("status") or {}).get("strStatus")) or "Unknown"
    events = match.get("events", [])

    if not events:
        return f"⚠️ No events available for match {match_value}."

    preview = events[: min(len(events), limit_value)]
    lines = []
    for event in preview:
        half = event.get("half", "N/A")
        minute = event.get("min", "N/A")
        second = event.get("sec", 0)
        team = event.get("team", "Unknown")
        player = event.get("nickname") or event.get("player") or "Unknown player"
        category = event.get("category", "Event")
        action = event.get("event", "Action")
        result = event.get("result", "Unknown")
        lines.append(
            f"- {half}H {minute}'{second}\" {team}: {player} | {category} → {action} ({result})"
        )

    lines_text = "\n".join(lines)
    message = payload.get("message", "Success")

    return f"""📊 Match Events:
- Fixture: {home} vs {away}
- Status: {status}
- Total events: {len(events)}
- Showing first {len(preview)} events (limit {limit_value})

Highlights:
{lines_text}

Summary: {message} | Generated at {_iso_timestamp()}"""


if __name__ == "__main__":
    logger.info("Starting KoraStats MCP server...")
    try:
        mcp.run(transport="stdio")
    except Exception as exc:
        logger.error("Server error: %s", exc, exc_info=True)
        sys.exit(1)
