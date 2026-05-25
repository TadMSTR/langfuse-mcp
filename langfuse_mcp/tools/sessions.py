"""Tools: list_sessions, get_session."""

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
    async def list_sessions(
        project_id: Optional[str] = None,
        from_timestamp: Optional[str] = None,
        to_timestamp: Optional[str] = None,
        limit: int = 20,
        page: int = 1,
    ) -> dict:
        """List recent Langfuse sessions.

        Returns session_id, trace count, first/last seen timestamp, and aggregate cost.

        Args:
            project_id: Filter by project ID.
            from_timestamp: Start of time range (ISO 8601).
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
            if from_timestamp:
                params["fromTimestamp"] = from_timestamp
            if to_timestamp:
                params["toTimestamp"] = to_timestamp

            t0 = time.perf_counter()
            resp = await client.get("/api/public/sessions", params=params)
            duration = time.perf_counter() - t0
            data = resp.json()
            sessions = data.get("data", [])
            meta = data.get("meta", {})
            log.info(
                "list_sessions",
                count=len(sessions),
                total=meta.get("totalItems"),
                duration_s=round(duration, 3),
            )
            await emit_metric(
                "langfuse_tool",
                {"tool": "list_sessions"},
                {"duration_s": duration, "count": len(sessions)},
            )
            return data
        except (LangfuseError, LangfuseConfigError) as e:
            return _tool_error("list_sessions", e)

    @mcp.tool
    async def get_session(session_id: str, limit: int = 50) -> dict:
        """Get all traces in a session, in chronological order.

        Returns session metadata and the ordered list of traces with their
        costs and latencies.

        Args:
            session_id: Session ID from list_sessions.
            limit: Max traces to return (default 50, max 100).
        """
        if not _SAFE_ID.match(session_id):
            return {"error": f"Invalid session_id: {session_id!r}"}

        client = get_client()
        try:
            t0 = time.perf_counter()
            resp = await client.get(
                "/api/public/traces",
                params={"sessionId": session_id, "limit": min(limit, 100), "page": 1},
            )
            duration = time.perf_counter() - t0
            data = resp.json()
            traces = data.get("data", [])
            log.info(
                "get_session",
                session_id=session_id,
                trace_count=len(traces),
                duration_s=round(duration, 3),
            )
            await emit_metric(
                "langfuse_tool",
                {"tool": "get_session"},
                {"duration_s": duration, "trace_count": len(traces)},
            )
            return {"session_id": session_id, "traces": traces, "meta": data.get("meta", {})}
        except (LangfuseError, LangfuseConfigError) as e:
            return _tool_error("get_session", e)
