"""
Langfuse HTTP client — Basic Auth (public key : secret key).

4xx/5xx responses raise LangfuseError. Configuration errors raise LangfuseConfigError.
"""

from __future__ import annotations

import os
from typing import Any, Optional

import httpx
import structlog

log = structlog.get_logger(__name__)


class LangfuseError(Exception):
    """Raised when Langfuse returns an error response."""

    def __init__(self, status_code: int, message: str) -> None:
        self.status_code = status_code
        super().__init__(f"Langfuse error {status_code}: {message}")


class LangfuseConfigError(Exception):
    """Raised for missing or invalid configuration (not an HTTP error)."""


class LangfuseClient:
    """
    Async HTTP client for the Langfuse v2 API.

    A single instance is reused for the lifetime of the MCP server
    so the httpx connection pool is shared across tool calls.
    """

    def __init__(self) -> None:
        base_url = os.environ.get("LANGFUSE_BASE_URL", "http://localhost:3000").rstrip("/")

        public_key = os.environ.get("LANGFUSE_PUBLIC_KEY", "")
        if not public_key:
            raise RuntimeError("LANGFUSE_PUBLIC_KEY is required")

        secret_key = os.environ.get("LANGFUSE_SECRET_KEY", "")
        if not secret_key:
            raise RuntimeError("LANGFUSE_SECRET_KEY is required")

        self._default_project_id = os.environ.get("LANGFUSE_DEFAULT_PROJECT_ID", "")

        self._http = httpx.AsyncClient(
            base_url=base_url,
            auth=httpx.BasicAuth(public_key, secret_key),
            timeout=30.0,
            headers={"Accept": "application/json"},
            trust_env=False,
        )

    async def close(self) -> None:
        await self._http.aclose()

    def default_project_id(self) -> str:
        if not self._default_project_id:
            raise LangfuseConfigError(
                "LANGFUSE_DEFAULT_PROJECT_ID is required for this operation. "
                "Set it to your Langfuse project ID (Settings → Projects in the UI)."
            )
        return self._default_project_id

    async def get(self, path: str, **kwargs: Any) -> httpx.Response:
        resp = await self._http.get(path, **kwargs)
        _raise_for_status(resp)
        return resp


def _raise_for_status(resp: httpx.Response) -> None:
    """Raise LangfuseError for 4xx/5xx, preserving the JSON error message."""
    if resp.is_success:
        return
    try:
        body = resp.json()
        msg = body.get("error") or body.get("message") or resp.text
    except Exception:
        msg = resp.text or resp.reason_phrase
    raise LangfuseError(resp.status_code, msg)


# Module-level singleton
_client: Optional[LangfuseClient] = None


def get_client() -> LangfuseClient:
    global _client
    if _client is None:
        _client = LangfuseClient()
    return _client
