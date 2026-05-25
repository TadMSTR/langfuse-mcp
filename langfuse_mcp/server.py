"""
langfuse-mcp — FastMCP server wrapping the Langfuse v2 API (read-only).

Tool surface:
  list_traces       — Recent traces with cost/latency overview
  get_trace         — Full trace by ID (spans, observations, tokens)
  list_generations  — LLM generation events with token/cost breakdown
  get_cost_summary  — Aggregate cost + token usage grouped by model
  list_sessions     — Recent sessions with trace counts and aggregate cost
  get_session       — All traces in a session, in order
  list_scores       — Quality scores attached to traces
"""

from __future__ import annotations

from fastmcp import FastMCP

from .observability import configure_logging
from .tools import generations, scores, sessions, traces

configure_logging()

mcp = FastMCP(
    name="langfuse",
    instructions=(
        "Langfuse MCP server. Read-only access to LLM observability data on forge. "
        "Use list_traces to browse recent pipeline runs. Use get_trace for full span details. "
        "Use list_generations / get_cost_summary for token usage and cost analysis. "
        "Use list_sessions / get_session to follow a multi-turn interaction. "
        "Use list_scores to review agent output quality metrics. "
        "All tools are read-only — no writes are possible through this server."
    ),
)

traces.register(mcp)
generations.register(mcp)
sessions.register(mcp)
scores.register(mcp)


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
