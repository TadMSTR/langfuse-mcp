# Changelog

## [0.1.0] — 2026-05-25

### Added

- Initial release of `langfuse-mcp` — read-only FastMCP Python MCP server wrapping the Langfuse v2 API
- 7 tools covering the full observability query surface:
  - `list_traces` — Recent traces with timestamp, latency, cost, and input/output preview
  - `get_trace` — Full trace by ID with all spans, observations, token counts, and model info
  - `list_generations` — LLM generation events with prompt/completion tokens and cost per call
  - `get_cost_summary` — Aggregate cost and token usage grouped by model for a time range (paginates all generations)
  - `list_sessions` — Sessions with trace count and aggregate cost
  - `get_session` — All traces in a session in chronological order
  - `list_scores` — Quality scores attached to traces (accuracy, helpfulness, etc.)
- HTTP Basic Auth via `LANGFUSE_PUBLIC_KEY:LANGFUSE_SECRET_KEY` (credentials stored in httpx.BasicAuth, never logged)
- `LangfuseError` (HTTP error) and `LangfuseConfigError` (missing env var) exception hierarchy
- `httpx.AsyncClient` with `trust_env=False` — prevents ALL_PROXY/SOCKS interference
- Structured JSON logging via structlog; optional InfluxDB and NATS telemetry
- All list endpoints support `project_id`, `from_timestamp`, `to_timestamp` filters
- ID validation before URL path construction (`trace_id`, `session_id`)
- Query parameters encoded via httpx `params=` dict throughout
- PM2 ecosystem config for forge deployment
- 10 unit tests covering auth, error handling, config validation, and query encoding
