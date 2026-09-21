"""Tests for app.main — basic app liveness and DB connectivity."""


def test_health_check_returns_ok(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_health_check_db_confirms_connection(client):
    response = client.get("/health/db")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["database"] == "connected"


def test_docs_endpoint_is_available(client):
    # FastAPI's auto-generated interactive docs, per Phase 2 tech notes.
    response = client.get("/docs")
    assert response.status_code == 200