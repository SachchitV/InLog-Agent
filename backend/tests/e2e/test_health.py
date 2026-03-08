"""E2E tests for GET /health endpoint."""

import pytest


@pytest.mark.smoke
def test_health(client):
    """GET /health returns 200 with correct schema and body."""
    resp = client.get("/health")

    # Endpoint must be reachable
    assert resp.status_code == 200

    # Response must be JSON
    assert "application/json" in resp.headers["content-type"]

    data = resp.json()

    # 'status' field must be present and a string
    assert "status" in data
    assert isinstance(data["status"], str)

    # Value must confirm the service is healthy
    assert data["status"] == "ok"
