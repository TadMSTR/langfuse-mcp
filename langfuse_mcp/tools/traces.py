"""Tools: list_traces, get_trace."""

from __future__ import annotations

import time
from typing import Optional

import structlog

from ..client import LangfuseConfigError, LangfuseError, get_client
from ..observability import emit_metric

log = structlog.get_logger(__name__)

_SAFE_ID = __import__("re").compile(r"^[a-zA-Z0-9][a-zA-Z0-9_\-\.]*$")


def _tool_error(tool: str, err: Exception) -> dict:
    log.error("tool_error", tool=tool, error=str(err))
    return {"error": str(err)}


def register(mcp) -> None:
    @mcp.tool
    async def list_traces(
        project_id: Optional[str] = None,
        session_id: Optional[str] = None,
        user_id: Optional[str] = None,
        name: Optional[str] = None,
        from_timestamp: Optional[str] = None,
        to_timestamp: Optional[str] = None,
        limit: int = 20,
        page: int = 1,
    ) -> dict:
        """List recent LLM traces from Langfuse.

        Returns trace id, name, timestamp, latency, total_cost, and input/output preview.

        Args:
            project_id: Filter by project ID (defaults to LANGFUSE_DEFAULT_PROJECT_ID if set).
            session_id: Filter by session ID.
            user_id: Filter by user ID.
            name: Filter by trace name.
            from_timestamp: Start of time range (ISO 8601, e.g. '2026-05-01T00:00:00Z').
            to_timestamp: End of time range (ISO 8601).
            limit: Number of results per page (default 20, max 100).
            page: Page number (default 1).
        """
        client = get_client()
        try:
            params: dict = {"page": page, "limit": min(limit, 100)}
            pid = project_id or (client._default_project_id or None)
            if pid:
                params["projectId"] = pid
            if session_id:
                params["sessionId"] = session_id
            if user_id:
                params["userId"] = user_id
            if name:
                params["name"] = name
            if from_timestamp:
                params["fromTimestamp"] = from_timestamp
            if to_timestamp:
                params["toTimestamp"] = to_timestamp

            t0 = time.perf_counter()
            resp = await client.get("/api/public/traces", params=params)
            duration = time.perf_counter() - t0
            data = resp.json()
            traces = data.get("data", [])
            meta = data.get("meta", {})
            log.info(
                "list_traces",
                count=len(traces),
                total=meta.get("totalItems"),
                duration_s=round(duration, 3),
            )
            await emit_metric(
                "langfuse_tool",
                {"tool": "list_traces"},
                {"duration_s": duration, "count": len(traces)},
            )
            return data
        except (LangfuseError, LangfuseConfigError) as e:
            return _tool_error("list_traces", e)

    @mcp.tool
    async def get_trace(trace_id: str) -> dict:
        """Get a full trace by ID, including all spans and observations.

        Returns all spans/observations with input, output, latency, model, and token counts.

        Args:
            trace_id: Trace ID from list_traces.
        """
        if not _SAFE_ID.match(trace_id):
            return {"error": f"Invalid trace_id: {trace_id!r}"}

        client = get_client()
        try:
            t0 = time.perf_counter()
            resp = await client.get(f"/api/public/traces/{trace_id}")
            duration = time.perf_counter() - t0
            data = resp.json()
            log.info("get_trace", trace_id=trace_id, duration_s=round(duration, 3))
            await emit_metric(
                "langfuse_tool",
                {"tool": "get_trace"},
                {"duration_s": duration},
            )
            return data
        except (LangfuseError, LangfuseConfigError) as e:
            return _tool_error("get_trace", e)
