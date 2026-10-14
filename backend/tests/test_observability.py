"""Phase 11 observability tests."""

import json
import logging

import pytest

from app.core import metrics
from app.core.config import settings
from app.core.logging_config import JsonFormatter, request_id_var
from app.core.observability import metrics_authorized

PW = "correcthorsebattery"


@pytest.fixture(autouse=True)
def _clean_metrics():
    metrics.reset()
    yield
    metrics.reset()


def _auth(client, email="o@example.com"):
    client.post("/auth/register", json={"email": email, "password": PW})
    t = client.post("/auth/login", json={"email": email, "password": PW}).json()["access_token"]
    return {"Authorization": f"Bearer {t}"}


def _counter(name, **labels):
    for c in metrics.snapshot()["counters"]:
        if c["name"] == name and all(c["labels"].get(k) == v for k, v in labels.items()):
            return c["value"]
    return 0


def _hist(name, **labels):
    for h in metrics.snapshot()["histograms"]:
        if h["name"] == name and all(h["labels"].get(k) == v for k, v in labels.items()):
            return h
    return None


# ---- metrics primitives ---------------------------------------------------
def test_percentiles_nearest_rank():
    for v in range(1, 101):
        metrics.observe("t", v / 1000)
    h = _hist("t")
    assert (h["p50"], h["p95"], h["p99"], h["max"]) == (0.05, 0.095, 0.099, 0.1)
    assert h["count"] == 100


def test_prometheus_output_has_buckets_and_escapes_labels():
    metrics.observe("lat", 0.02, {"route": 'a"b'})
    metrics.inc("c_total", {"x": "1"}, 3)
    text = metrics.render_prometheus()
    assert 'c_total{x="1"} 3' in text
    assert 'lat_bucket{route="a\\"b",le="0.025"} 1' in text
    assert 'lat_bucket{route="a\\"b",le="0.01"} 0' in text
    assert 'lat_count{route="a\\"b"} 1' in text


def test_reservoir_is_bounded():
    for _ in range(metrics.RESERVOIR + 500):
        metrics.observe("b", 0.001)
    assert len(metrics._histograms[("b", ())].recent) == metrics.RESERVOIR
    assert _hist("b")["count"] == metrics.RESERVOIR + 500


# ---- request id + http metrics ---------------------------------------------
def test_response_has_request_id_and_it_is_propagated(client):
    assert len(client.get("/health").headers["x-request-id"]) >= 8
    r = client.get("/health", headers={"X-Request-ID": "trace-abc-12345"})
    assert r.headers["x-request-id"] == "trace-abc-12345"


def test_hostile_request_id_is_replaced(client):
    r = client.get("/health", headers={"X-Request-ID": "bad id\twith spaces"})
    assert r.headers["x-request-id"] != "bad id\twith spaces"


def test_http_metrics_use_route_template_not_raw_url(client):
    h = _auth(client)
    ws = client.post("/workspaces", json={"name": "w"}, headers=h).json()["id"]
    client.get(f"/workspaces/{ws}", headers=h)
    routes = {x["labels"]["route"] for x in metrics.snapshot()["histograms"] if x["name"] == "ember_http_request_seconds"}
    assert "/workspaces/{workspace_id}" in routes
    assert not any(ws in r for r in routes)
    assert _counter("ember_http_requests_total", route="/workspaces/{workspace_id}", status="2xx") == 1


def test_health_is_not_counted(client):
    client.get("/health")
    assert _hist("ember_http_request_seconds") is None


def test_unhandled_exception_returns_json_500_with_request_id(client, monkeypatch, caplog):
    from app.main import app

    @app.get("/__boom")
    def boom():
        raise RuntimeError("secret internal detail")

    try:
        with caplog.at_level(logging.ERROR):
            r = client.get("/__boom")
    finally:
        app.router.routes[:] = [x for x in app.router.routes if getattr(x, "path", "") != "/__boom"]
    assert r.status_code == 500
    body = r.json()
    assert body["detail"] == "Internal server error." and body["request_id"] == r.headers["x-request-id"]
    assert "secret internal detail" not in r.text
    assert _counter("ember_http_errors_total", route="/__boom") == 1
    assert any("unhandled exception" in rec.message for rec in caplog.records)


# ---- /metrics access -------------------------------------------------------
def test_metrics_open_in_dev_without_token(client):
    client.get("/auth/me")
    r = client.get("/metrics")
    assert r.status_code == 200 and "ember_http_requests_total" in r.text
    assert "histograms" in client.get("/metrics?format=json").json()


def test_metrics_requires_token_when_configured(client, monkeypatch):
    monkeypatch.setattr(settings, "metrics_token", "s3cret-token-value")
    assert client.get("/metrics").status_code == 404
    assert client.get("/metrics", headers={"Authorization": "Bearer nope"}).status_code == 404
    assert client.get("/metrics", headers={"Authorization": "Bearer s3cret-token-value"}).status_code == 200


def test_metrics_hidden_in_production_without_token():
    assert metrics_authorized(None, "", "production") is False
    assert metrics_authorized(None, "", "development") is True
    assert metrics_authorized("Bearer t", "t", "production") is True


# ---- domain metrics --------------------------------------------------------
def _upload(client, h, ws, name, data, ctype="text/plain"):
    return client.post(f"/workspaces/{ws}/documents", files={"file": (name, data, ctype)}, headers=h)


def test_upload_search_and_indexing_metrics(client):
    h = _auth(client)
    ws = client.post("/workspaces", json={"name": "w"}, headers=h).json()["id"]
    assert _upload(client, h, ws, "a.txt", b"observability rocks").status_code == 201
    assert _upload(client, h, ws, "a.txt", b"observability rocks").json()["is_duplicate"] is True
    assert _upload(client, h, ws, "bad.exe", b"MZ").status_code == 400
    client.post(f"/workspaces/{ws}/search", json={"query": "observability"}, headers=h)
    client.post(f"/workspaces/{ws}/search", json={"query": "zzzz"}, headers=h)
    client.post(f"/workspaces/{ws}/search", json={"query": '"observability rocks"'}, headers=h)
    client.get(f"/workspaces/{ws}/search/autocomplete?prefix=obs", headers=h)

    assert _counter("ember_uploads_total", outcome="accepted") == 1
    assert _counter("ember_uploads_total", outcome="duplicate") == 1
    assert _counter("ember_upload_failures_total", reason="validation") == 1
    assert _counter("ember_documents_processed_total", outcome="ready") == 1
    assert _hist("ember_indexing_seconds")["count"] == 1
    assert _hist("ember_extraction_seconds", kind="txt")["count"] == 1
    assert _counter("ember_searches_total", kind="keyword", outcome="hit") == 1
    assert _counter("ember_searches_total", kind="keyword", outcome="empty") == 1
    assert _counter("ember_searches_total", kind="phrase", outcome="hit") == 1
    assert _hist("ember_search_seconds", kind="keyword")["count"] == 2
    assert _hist("ember_autocomplete_seconds")["count"] == 1


def test_extraction_failure_is_counted(client):
    h = _auth(client)
    ws = client.post("/workspaces", json={"name": "w"}, headers=h).json()["id"]
    # valid PDF magic but no extractable content -> extraction fails in the worker
    bad_pdf = b"%PDF-1.4\n%%EOF\n"
    try:
        _upload(client, h, ws, "empty.pdf", bad_pdf, "application/pdf")
    except Exception:  # synchronous test queue re-raises the worker error
        pass
    assert _counter("ember_documents_processed_total", outcome="failed") == 1
    assert _counter("ember_extraction_failures_total", kind="pdf") == 1
    assert _counter("ember_worker_failures_total", stage="extract") == 1


def test_index_rebuild_metrics(client):
    h = _auth(client)
    ws = client.post("/workspaces", json={"name": "w"}, headers=h).json()["id"]
    _upload(client, h, ws, "a.txt", b"alpha beta")
    assert client.post(f"/workspaces/{ws}/index/rebuild", headers=h).status_code in (200, 202)
    assert _counter("ember_index_rebuilds_total", outcome="ok") >= 1
    assert _hist("ember_index_rebuild_seconds")["count"] >= 1


# ---- logging ---------------------------------------------------------------
def test_json_formatter_includes_request_id_and_extras():
    token = request_id_var.set("req-1234567")
    try:
        rec = logging.LogRecord("ember.x", logging.INFO, __file__, 1, "hello %s", ("w",), None)
        rec.duration_ms = 12.5
        out = json.loads(JsonFormatter().format(rec))
    finally:
        request_id_var.reset(token)
    assert out["msg"] == "hello w" and out["request_id"] == "req-1234567" and out["duration_ms"] == 12.5
    assert out["level"] == "INFO" and out["ts"].endswith("+00:00")
