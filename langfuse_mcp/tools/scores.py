"""Tool: list_scores."""

from __future__ import annotations

import time
from typing import Optional

import structlog

from ..client import LangfuseConfigError, LangfuseError, get_client
from ..observability import emit_metric

log = structlog.get_logger(__name__)


def _tool_error(tool: str, err: Exception) -> dict:
    log.error("tool_error", tool=tool, error=str(err))
    return {"error": str(err)}


def register(mcp) -> None:
    @mcp.tool
    async def list_scores(
        project_id: Optional[str] = None,
        from_timestamp: Optional[str] = None,
        to_timestamp: Optional[str] = None,
        name: Optional[str] = None,
        limit: int = 20,
        page: int = 1,
    ) -> dict:
        """List quality scores attached to traces.

        Useful for evaluating agent output quality over time.

        Args:
            project_id: Filter by project ID.
            from_timestamp: Start of time range (ISO 8601).
            to_timestamp: End of time range (ISO 8601).
            name: Filter by score name (e.g. 'accuracy', 'helpfulness').
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
            if name:
                params["name"] = name

            t0 = time.perf_counter()
            resp = await client.get("/api/public/scores", params=params)
            duration = time.perf_counter() - t0
            data = resp.json()
            scores = data.get("data", [])
            meta = data.get("meta", {})
            log.info(
                "list_scores",
                count=len(scores),
                total=meta.get("totalItems"),
                duration_s=round(duration, 3),
            )
            await emit_metric(
                "langfuse_tool",
                {"tool": "list_scores"},
                {"duration_s": duration, "count": len(scores)},
            )
            return data
        except (LangfuseError, LangfuseConfigError) as e:
            return _tool_error("list_scores", e)
