"""
Tests for LangfuseClient — Basic Auth injection, error handling, config errors.
"""

import json
import pytest
import respx
import httpx

from langfuse_mcp.client import LangfuseClient, LangfuseError, LangfuseConfigError

from .conftest import (
    BASE_URL,
    PUBLIC_KEY,
    SECRET_KEY,
    TRACES_RESPONSE,
    GENERATIONS_RESPONSE,
    SESSIONS_RESPONSE,
    SCORES_RESPONSE,
)


# ---------------------------------------------------------------------------
# Auth injection
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_basic_auth_sent_on_get(mock_env):
    """GET requests include Basic Auth header with public:secret credentials."""
    import base64
    expected = "Basic " + base64.b64encode(f"{PUBLIC_KEY}:{SECRET_KEY}".encode()).decode()

    with respx.mock(base_url=BASE_URL) as mock:
        route = mock.get("/api/public/traces").mock(
            return_value=httpx.Response(200, json=TRACES_RESPONSE)
        )

        client = LangfuseClient()
        await client.get("/api/public/traces")

        req = route.calls[0].request
        assert req.headers.get("authorization") == expected
        await client.close()


@pytest.mark.asyncio
async def test_trust_env_false(mock_env):
    """Client is created with trust_env=False to prevent proxy interference."""
    client = LangfuseClient()
    assert client._http.trust_env is False
    await client.close()


# ---------------------------------------------------------------------------
# Error handling
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_4xx_raises_langfuse_error(mock_env):
    """4xx responses raise LangfuseError with status code and message."""
    with respx.mock(base_url=BASE_URL) as mock:
        mock.get("/api/public/traces/nonexistent").mock(
            return_value=httpx.Response(404, json={"error": "Trace not found"})
        )

        client = LangfuseClient()
        with pytest.raises(LangfuseError) as exc_info:
            await client.get("/api/public/traces/nonexistent")

        assert exc_info.value.status_code == 404
        assert "Trace not found" in str(exc_info.value)
        await client.close()


@pytest.mark.asyncio
async def test_5xx_raises_langfuse_error(mock_env):
    """5xx responses raise LangfuseError."""
    with respx.mock(base_url=BASE_URL) as mock:
        mock.get("/api/public/traces").mock(
            return_value=httpx.Response(500, json={"error": "Internal server error"})
        )

        client = LangfuseClient()
        with pytest.raises(LangfuseError) as exc_info:
            await client.get("/api/public/traces")

        assert exc_info.value.status_code == 500
        await client.close()


@pytest.mark.asyncio
async def test_missing_public_key_raises(monkeypatch):
    """Missing LANGFUSE_PUBLIC_KEY raises RuntimeError."""
    monkeypatch.setenv("LANGFUSE_BASE_URL", BASE_URL)
    monkeypatch.delenv("LANGFUSE_PUBLIC_KEY", raising=False)
    monkeypatch.setenv("LANGFUSE_SECRET_KEY", SECRET_KEY)

    with pytest.raises(RuntimeError, match="LANGFUSE_PUBLIC_KEY"):
        LangfuseClient()


@pytest.mark.asyncio
async def test_missing_secret_key_raises(monkeypatch):
    """Missing LANGFUSE_SECRET_KEY raises RuntimeError."""
    monkeypatch.setenv("LANGFUSE_BASE_URL", BASE_URL)
    monkeypatch.setenv("LANGFUSE_PUBLIC_KEY", PUBLIC_KEY)
    monkeypatch.delenv("LANGFUSE_SECRET_KEY", raising=False)

    with pytest.raises(RuntimeError, match="LANGFUSE_SECRET_KEY"):
        LangfuseClient()


@pytest.mark.asyncio
async def test_missing_project_id_raises_config_error(monkeypatch):
    """Missing LANGFUSE_DEFAULT_PROJECT_ID raises LangfuseConfigError when accessed."""
    monkeypatch.setenv("LANGFUSE_BASE_URL", BASE_URL)
    monkeypatch.setenv("LANGFUSE_PUBLIC_KEY", PUBLIC_KEY)
    monkeypatch.setenv("LANGFUSE_SECRET_KEY", SECRET_KEY)
    monkeypatch.delenv("LANGFUSE_DEFAULT_PROJECT_ID", raising=False)

    client = LangfuseClient()
    with pytest.raises(LangfuseConfigError) as exc_info:
        client.default_project_id()

    assert "LANGFUSE_DEFAULT_PROJECT_ID" in str(exc_info.value)
    await client.close()


# ---------------------------------------------------------------------------
# Query param encoding
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_params_encoded_not_fstring(mock_env):
    """Query parameters are sent via httpx params dict (not f-string interpolation)."""
    with respx.mock(base_url=BASE_URL) as mock:
        route = mock.get("/api/public/traces").mock(
            return_value=httpx.Response(200, json=TRACES_RESPONSE)
        )

        client = LangfuseClient()
        await client.get("/api/public/traces", params={"projectId": "proj-1&injected=x"})

        req = route.calls[0].request
        # httpx encodes & in param values — injected should NOT be a separate query key
        from urllib.parse import parse_qs, urlparse
        query = parse_qs(urlparse(str(req.url)).query)
        assert "injected" not in query
        assert "projectId" in query
        await client.close()


# ---------------------------------------------------------------------------
# Endpoint routing
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_list_generations_calls_correct_endpoint(mock_env):
    """list_generations uses GET /api/public/generations."""
    with respx.mock(base_url=BASE_URL) as mock:
        route = mock.get("/api/public/generations").mock(
            return_value=httpx.Response(200, json=GENERATIONS_RESPONSE)
        )

        client = LangfuseClient()
        resp = await client.get("/api/public/generations", params={"page": 1, "limit": 20})

        assert route.call_count == 1
        assert resp.json() == GENERATIONS_RESPONSE
        await client.close()


@pytest.mark.asyncio
async def test_list_scores_calls_correct_endpoint(mock_env):
    """list_scores uses GET /api/public/scores."""
    with respx.mock(base_url=BASE_URL) as mock:
        route = mock.get("/api/public/scores").mock(
            return_value=httpx.Response(200, json=SCORES_RESPONSE)
        )

        client = LangfuseClient()
        resp = await client.get("/api/public/scores", params={"page": 1, "limit": 20})

        assert route.call_count == 1
        assert resp.json() == SCORES_RESPONSE
        await client.close()
