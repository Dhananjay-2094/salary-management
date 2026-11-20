"""Tests for the API health endpoint."""

from app.main import app, health_check


def test_health_route_is_registered_and_returns_ok() -> None:
    route = next(route for route in app.routes if getattr(route, "path", None) == "/health")

    assert "GET" in route.methods
    assert health_check() == {"status": "ok"}
