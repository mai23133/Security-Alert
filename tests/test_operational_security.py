import asyncio
import json
import logging
import threading

import pytest
from httpx import ASGITransport, AsyncClient

from src.api.main import create_app
from src.api.routes import alerts

pytestmark = pytest.mark.anyio


@pytest.fixture
def anyio_backend():
    return "asyncio"


async def test_missing_kb_starts_and_fails_safely(tmp_path):
    app = create_app(snapshot_path=tmp_path / "missing.json")
    async with app.router.lifespan_context(app), AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        assert (await client.get("/")).status_code == 200
        for method, path, body in [("GET", "/ready", None), ("GET", "/taxonomy/techniques", None),
            ("POST", "/alerts/infer", {"narrative":"alert"}), ("POST", "/rag/search", {"narrative":"alert"}),
            ("POST", "/evaluate", {})]:
            response = await client.request(method, path, json=body)
            assert response.status_code == 503
            assert "missing.json" not in response.text


async def test_auth_rate_limit_and_cors():
    app = create_app(api_key="test-key", rate_limit=1)
    async with app.router.lifespan_context(app), AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        assert (await client.post("/alerts/infer", json={"narrative":"alert"})).status_code == 401
        headers = {"X-API-Key":"test-key", "Origin":"http://localhost:8000"}
        first = await client.post("/alerts/infer", json={"narrative":"alert"}, headers=headers)
        assert first.status_code == 200
        assert first.headers["access-control-allow-origin"] == headers["Origin"]
        limited = await client.post("/alerts/infer", json={"narrative":"alert"}, headers=headers)
        assert limited.status_code == 429
        assert limited.headers["retry-after"]
        denied = await client.get("/", headers={"Origin":"https://untrusted.invalid"})
        assert "access-control-allow-origin" not in denied.headers


async def test_errors_validation_and_logs_do_not_echo_untrusted_data(caplog, monkeypatch):
    sentinel = "PRIVATE_SENTINEL_VALUE"
    def fail(**kwargs):
        raise RuntimeError(sentinel)
    monkeypatch.setattr(alerts, "run_inference", fail)
    app = create_app()
    caplog.set_level(logging.INFO, logger="security_alert.api")
    async with app.router.lifespan_context(app), AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        failed = await client.post("/alerts/infer", json={"narrative":sentinel,"alert_id":sentinel}, headers={"X-Request-ID":sentinel})
        assert failed.status_code == 500
        invalid = await client.post("/alerts/infer", json={"narrative": {"secret":sentinel}})
        assert invalid.status_code == 422
        unknown = await client.get("/taxonomy/techniques/" + sentinel)
        assert unknown.status_code == 404
        assert all(sentinel not in r.text for r in (failed, invalid, unknown))
    own_logs = [r.getMessage() for r in caplog.records if r.name.startswith(("security_alert", "src.api"))]
    assert sentinel not in " ".join(own_logs)
    assert any(json.loads(r).get("event") == "request" for r in own_logs if r.startswith("{"))


async def test_total_deadline_does_not_block_health_or_release_worker_early(monkeypatch):
    started, release = threading.Event(), threading.Event()
    def slow(**kwargs):
        started.set()
        release.wait(2)
        raise TimeoutError()
    monkeypatch.setattr(alerts, "run_inference", slow)
    app = create_app(request_timeout=0.1)
    async with app.router.lifespan_context(app), AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        try:
            response = await client.post("/alerts/infer", json={"narrative":"test"})
            assert started.is_set()
            assert response.status_code == 504
            assert app.state.worker_slots._value == 3
            assert (await client.get("/")).status_code == 200
        finally:
            release.set()
            await asyncio.sleep(0.02)


async def test_body_limit_and_unknown_fields():
    app = create_app()
    async with app.router.lifespan_context(app), AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        assert (await client.post("/alerts/infer", content=b"x" * 600001)).status_code == 413
        assert (await client.post("/alerts/infer", json={"narrative":"alert", "provider":True})).status_code == 422


def test_deployment_requires_key_and_explicit_cors(monkeypatch):
    monkeypatch.setenv("APP_ENV", "deployment")
    with pytest.raises(ValueError):
        create_app(api_key="")
    monkeypatch.setenv("CORS_ALLOWED_ORIGINS", "*")
    with pytest.raises(ValueError):
        create_app(api_key="x" * 32)
