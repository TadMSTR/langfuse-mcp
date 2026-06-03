# langfuse-mcp

FastMCP server wrapping the Langfuse v2 API. Read-only — no write operations are exposed.

## What it does

Provides 7 tools for querying LLM traces, generations, sessions, and scores from a Langfuse instance.

## Tools

- `list_traces` — List recent LLM traces with token counts.
- `get_trace` — Retrieve a single trace by ID.
- `list_generations` — List generation records.
- `list_sessions` — List session groupings.
- `get_session` — Retrieve a single session by ID.
- `list_scores` — List evaluation scores.

## Structure

```
langfuse_mcp/
  __init__.py       Package marker
  __main__.py       python -m langfuse_mcp entry point
  server.py         FastMCP setup, tool module registration
  observability.py  configure_logging() — structlog JSON format
  tools/
    traces.py       list_traces, get_trace
    generations.py  list_generations
    sessions.py     list_sessions, get_session
    scores.py       list_scores
  client.py         LangfuseClient — async httpx wrapper, Basic Auth
tests/              pytest tests
pyproject.toml
```

## Dependencies

| Package   | Role                        |
|-----------|-----------------------------|
| fastmcp   | MCP server framework        |
| httpx     | Async HTTP client           |
| pydantic  | Response models             |
| structlog | JSON structured logging     |

## Configuration

| Env var                  | Default                  | Purpose                        |
|--------------------------|--------------------------|--------------------------------|
| `LANGFUSE_HOST`          | `http://localhost:3000`  | Langfuse base URL              |
| `LANGFUSE_PUBLIC_KEY`    | (required)               | Langfuse public key (Basic Auth username) |
| `LANGFUSE_SECRET_KEY`    | (required)               | Langfuse secret key (Basic Auth password) |
| `LOG_LEVEL`              | `INFO`                   | Logging verbosity              |

## Key architecture decisions

- **Read-only by design** — Langfuse holds LLM observability data. No create/delete tools are exposed to limit blast radius if credentials are compromised.
- **Module-per-resource pattern** — each `tools/*.py` module exports a `register(mcp)` function. To add a tool, add a handler in the appropriate module's `register()` and a matching test in `tests/`.

## Testing

```bash
pip install -e ".[dev]"
pytest
```

## Git workflow

Branch before editing — do not commit directly to `main`.
