"""Shared fixtures for langfuse-mcp tests."""

import pytest
import langfuse_mcp.client as client_module

BASE_URL = "http://localhost:3000"
PUBLIC_KEY = "pk-lf-test-abc123"
SECRET_KEY = "sk-lf-test-xyz789"
DEFAULT_PROJECT_ID = "proj-test-001"

TRACES_RESPONSE = {
    "data": [
        {
            "id": "trace-abc123",
            "name": "pipeline-run",
            "timestamp": "2026-05-25T10:00:00.000Z",
            "latency": 1234,
            "totalCost": 0.0042,
            "input": "What is the status?",
            "output": "All systems nominal.",
        }
    ],
    "meta": {"page": 1, "limit": 20, "totalItems": 1, "totalPages": 1},
}

TRACE_DETAIL_RESPONSE = {
    "id": "trace-abc123",
    "name": "pipeline-run",
    "timestamp": "2026-05-25T10:00:00.000Z",
    "observations": [
        {
            "id": "obs-001",
            "type": "GENERATION",
            "model": "claude-sonnet-4-6",
            "usage": {"input": 100, "output": 50},
            "calculatedTotalCost": 0.0042,
        }
    ],
}

GENERATIONS_RESPONSE = {
    "data": [
        {
            "id": "gen-001",
            "model": "claude-sonnet-4-6",
            "usage": {"input": 100, "output": 50},
            "calculatedTotalCost": 0.0042,
            "latency": 800,
        }
    ],
    "meta": {"page": 1, "limit": 20, "totalItems": 1, "totalPages": 1},
}

SESSIONS_RESPONSE = {
    "data": [
        {
            "id": "session-xyz",
            "createdAt": "2026-05-25T09:00:00.000Z",
            "countTraces": 3,
        }
    ],
    "meta": {"page": 1, "limit": 20, "totalItems": 1, "totalPages": 1},
}

SCORES_RESPONSE = {
    "data": [
        {
            "id": "score-001",
            "traceId": "trace-abc123",
            "name": "accuracy",
            "value": 0.95,
            "timestamp": "2026-05-25T10:01:00.000Z",
        }
    ],
    "meta": {"page": 1, "limit": 20, "totalItems": 1, "totalPages": 1},
}


@pytest.fixture(autouse=True)
def reset_client_singleton():
    client_module._client = None
    yield
    if client_module._client:
        import asyncio
        asyncio.get_event_loop().run_until_complete(client_module._client.close())
    client_module._client = None


@pytest.fixture
def mock_env(monkeypatch):
    monkeypatch.setenv("LANGFUSE_BASE_URL", BASE_URL)
    monkeypatch.setenv("LANGFUSE_PUBLIC_KEY", PUBLIC_KEY)
    monkeypatch.setenv("LANGFUSE_SECRET_KEY", SECRET_KEY)
    monkeypatch.setenv("LANGFUSE_DEFAULT_PROJECT_ID", DEFAULT_PROJECT_ID)
