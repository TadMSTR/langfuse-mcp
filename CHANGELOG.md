# Changelog

## [0.1.2] — 2026-06-06

### Fixed

- **list_generations / get_cost_summary: 405 error** — `/api/public/generations` was removed
  in Langfuse v3. Both tools now use `/api/public/observations?type=GENERATION`. Response
  structure is identical so no downstream changes are required. Fixes LFUSE-1.

## [0.1.1] — 2026-05-27

### Fixed

- **Observability: stderr routing** — `configure_logging()` was using
  `structlog.PrintLoggerFactory()` which routes to `sys.stdout`. Switched to
  `structlog.stdlib.LoggerFactory()` with an explicit `sys.stderr` stream handler.
- **Observability: default log path** — `LOG_FILE` was opt-in (defaulted to `""`).
  Now baked in: `/opt/appdata/langfuse-mcp/logs/langfuse-mcp.log`.
- **Observability: bare LOG_FILE guard** — added `if log_dir:` guard before
  `os.makedirs` to prevent `FileNotFoundError` on bare filenames.

### Added

- OTEL tracing support (opt-in via `OTEL_EXPORTER_OTLP_ENDPOINT`) with silent failure
  when `opentelemetry` packages are absent.
- `[otel]` optional dep group: `opentelemetry-sdk>=1.20`,
  `opentelemetry-exporter-otlp-proto-grpc>=1.20`.

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
