# KoraStats MCP Server

A Model Context Protocol (MCP) server that surfaces Korastats season, match, and event data for football analytics workflows.

## Purpose

This MCP server provides a secure interface for AI assistants to explore Korastats competition data, list matches, and dig into detailed event timelines.

## Features

### Current Implementation

- **`list_seasons`** - Fetches season metadata with tournament context and schedule range.
- **`list_season_matches`** - Retrieves paginated match listings for a selected season.
- **`get_match_events`** - Summarizes granular match events with configurable preview limits.

## Prerequisites

- Docker Desktop with MCP Toolkit enabled
- Docker MCP CLI plugin (`docker mcp` command)
- Korastats API key stored as a Docker secret (`KORASTATS_API_KEY`)

## Installation

See the step-by-step instructions provided with the files.

## Usage Examples

In Claude Desktop, you can ask:

- "List the latest Korastats seasons so I can pick one."
- "Show me the first ten matches for season 560 from Korastats."
- "Summarize the key events for Korastats match 38789."

## Architecture

Claude Desktop → MCP Gateway → KoraStats MCP Server → Korastats API
↓
Docker Desktop Secrets
(KORASTATS_API_KEY)

## Development

### Local Testing

```bash
# Set environment variables for testing
export KORASTATS_API_KEY="test-value"

# Run directly
python korastats_server.py

# Test MCP protocol
echo '{"jsonrpc":"2.0","method":"tools/list","id":1}' | python korastats_server.py
```

### Adding New Tools

- Add the function to `korastats_server.py`
- Decorate with `@mcp.tool()`
- Update the catalog entry with the new tool name
- Rebuild the Docker image

### Troubleshooting

**Tools Not Appearing**
- Verify Docker image built successfully
- Check catalog and registry files
- Ensure Claude Desktop config includes custom catalog
- Restart Claude Desktop

**Authentication Errors**
- Verify secrets with `docker mcp secret list`
- Ensure secret names match in code and catalog

### Security Considerations

- All secrets stored in Docker Desktop secrets
- Never hardcode credentials
- Running as non-root user
- Sensitive data never logged

### License

MIT License
