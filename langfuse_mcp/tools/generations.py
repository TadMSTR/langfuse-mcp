"""Tools: list_generations, get_cost_summary."""

from __future__ import annotations

import time
from collections import defaultdict
from typing import Optional

import structlog

from ..client import LangfuseConfigError, LangfuseError, get_client
from ..observability import emit_metric

log = structlog.get_logger(__name__)

_MAX_COST_PAGES = 50  # hard cap to prevent runaway pagination


def _tool_error(tool: str, err: Exception) -> dict:
    log.error("tool_error", tool=tool, error=str(err))
    return {"error": str(err)}


def register(mcp) -> None:
    @mcp.tool
    async def list_generations(
        project_id: Optional[str] = None,
        from_timestamp: Optional[str] = None,
        to_timestamp: Optional[str] = None,
        model: Optional[str] = None,
        limit: int = 20,
        page: int = 1,
    ) -> dict:
        """List LLM generation events from Langfuse.

        Returns model, prompt tokens, completion tokens, total cost, and latency
        per generation event.

        Args:
            project_id: Filter by project ID.
            from_timestamp: Start of time range (ISO 8601).
            to_timestamp: End of time range (ISO 8601).
            model: Filter by model name (e.g. 'gpt-4o', 'claude-sonnet-4-6').
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
            if model:
                params["model"] = model

            t0 = time.perf_counter()
            # /api/public/generations removed in Langfuse v3 — use Observations API (LFUSE-1)
            params["type"] = "GENERATION"
            resp = await client.get("/api/public/observations", params=params)
            duration = time.perf_counter() - t0
            data = resp.json()
            generations = data.get("data", [])
            meta = data.get("meta", {})
            log.info(
                "list_generations",
                count=len(generations),
                total=meta.get("totalItems"),
                duration_s=round(duration, 3),
            )
            await emit_metric(
                "langfuse_tool",
                {"tool": "list_generations"},
                {"duration_s": duration, "count": len(generations)},
            )
            return data
        except (LangfuseError, LangfuseConfigError) as e:
            return _tool_error("list_generations", e)

    @mcp.tool
    async def get_cost_summary(
        project_id: Optional[str] = None,
        from_timestamp: Optional[str] = None,
        to_timestamp: Optional[str] = None,
        model: Optional[str] = None,
    ) -> dict:
        """Aggregate LLM cost and token usage for a time range, grouped by model.

        Paginates through all generation events and returns totals per model:
        prompt_tokens, completion_tokens, total_cost, call_count.

        Useful for answering "how much did last week cost by model?"

        Args:
            project_id: Filter by project ID.
            from_timestamp: Start of time range (ISO 8601, e.g. '2026-05-01T00:00:00Z').
            to_timestamp: End of time range (ISO 8601).
            model: Limit aggregation to a specific model.
        """
        client = get_client()
        try:
            params: dict = {"limit": 100, "page": 1}
            pid = project_id or (client._default_project_id or None)
            if pid:
                params["projectId"] = pid
            if from_timestamp:
                params["fromTimestamp"] = from_timestamp
            if to_timestamp:
                params["toTimestamp"] = to_timestamp
            if model:
                params["model"] = model

            t0 = time.perf_counter()
            totals: dict[str, dict] = defaultdict(
                lambda: {"prompt_tokens": 0, "completion_tokens": 0, "total_cost": 0.0, "call_count": 0}
            )
            total_items = 0
            pages_fetched = 0

            # /api/public/generations removed in Langfuse v3 — use Observations API (LFUSE-1)
            params["type"] = "GENERATION"
            while pages_fetched < _MAX_COST_PAGES:
                resp = await client.get("/api/public/observations", params=params)
                data = resp.json()
                generations = data.get("data", [])
                meta = data.get("meta", {})
                total_items = meta.get("totalItems", total_items)

                for g in generations:
                    m = g.get("model") or "unknown"
                    usage = g.get("usage") or {}
                    totals[m]["prompt_tokens"] += usage.get("input") or usage.get("promptTokens") or 0
                    totals[m]["completion_tokens"] += usage.get("output") or usage.get("completionTokens") or 0
                    totals[m]["total_cost"] += g.get("calculatedTotalCost") or g.get("totalCost") or 0.0
                    totals[m]["call_count"] += 1

                pages_fetched += 1
                total_pages = meta.get("totalPages", 1)
                if params["page"] >= total_pages or not generations:
                    break
                params["page"] += 1

            duration = time.perf_counter() - t0
            summary = dict(totals)
            grand_cost = sum(v["total_cost"] for v in summary.values())
            grand_calls = sum(v["call_count"] for v in summary.values())

            log.info(
                "get_cost_summary",
                models=len(summary),
                total_calls=grand_calls,
                grand_cost=round(grand_cost, 6),
                pages_fetched=pages_fetched,
                duration_s=round(duration, 3),
            )
            await emit_metric(
                "langfuse_tool",
                {"tool": "get_cost_summary"},
                {"duration_s": duration, "total_calls": grand_calls, "grand_cost": grand_cost},
            )
            return {
                "by_model": summary,
                "totals": {
                    "total_calls": grand_calls,
                    "grand_cost": round(grand_cost, 6),
                    "total_items": total_items,
                    "pages_fetched": pages_fetched,
                },
            }
        except (LangfuseError, LangfuseConfigError) as e:
            return _tool_error("get_cost_summary", e)
