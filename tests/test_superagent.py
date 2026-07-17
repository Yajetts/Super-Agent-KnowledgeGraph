"""Foundation tests for the FastAPI application."""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app


def test_root_endpoint_returns_running_status() -> None:
    """Ensure the root endpoint reports the service as running."""
    client = TestClient(app)

    response = client.get("/")

    assert response.status_code == 200
    assert response.json() == {
        "status": "running",
        "project": "SuperAgent Knowledge Graph",
    }
