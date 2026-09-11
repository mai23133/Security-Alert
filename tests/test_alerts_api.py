import pytest
from httpx import ASGITransport, AsyncClient

from src.api.routes import alerts
from src.api.main import app
from src.schemas import ATTACKInferenceResult


pytestmark = pytest.mark.anyio


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture
async def client():
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://testserver",
    ) as test_client:
        yield test_client


async def test_infer_runs_deterministic_pipeline_and_returns_human_review(client):
    response = await client.post(
        "/alerts/infer",
        json={
            "alert_id": "alert-001",
            "narrative": "Multiple failed login attempts were detected.",
        },
    )

    assert response.status_code == 200
    result = response.json()
    assert result["alert_id"] == "alert-001"
    assert result["inferred_techniques"] == []
    assert result["candidates_considered"]
    assert result["needs_human_review"] is True
    assert result["disclaimer"].startswith("Advisory tagging only.")
    assert response.headers["X-MITRE-ATTaCK-Version"] == (
        "enterprise-attack-19.1"
    )
    assert response.headers["X-Request-ID"]


async def test_infer_rejects_blank_or_oversized_narrative(client):
    blank = await client.post("/alerts/infer", json={"narrative": "   "})
    oversized = await client.post(
        "/alerts/infer", json={"narrative": "x" * 20_001}
    )

    assert blank.status_code == 422
    assert oversized.status_code == 422


async def test_infer_returns_safe_typed_timeout(client, monkeypatch):
    def time_out(**_kwargs):
        raise TimeoutError("provider secret should not be returned")

    monkeypatch.setattr(alerts, "run_inference", time_out)
    response = await client.post(
        "/alerts/infer", json={"alert_id": "timeout-1", "narrative": "alert"}
    )

    assert response.status_code == 504
    assert response.json()["detail"] == {
        "code": "INFERENCE_TIMEOUT",
        "message": "Inference timed out. Human review is required.",
    }
    assert "secret" not in response.text
    assert response.headers["X-Request-ID"]


async def test_request_id_is_propagated_when_well_formed(client):
    response = await client.get("/", headers={"X-Request-ID": "test-request-123"})
    assert response.headers["X-Request-ID"] == "test-request-123"


async def test_batch_preserves_order_and_generates_missing_ids(client, monkeypatch):
    def fake_run_inference(*, alert_id, narrative, retriever):
        return ATTACKInferenceResult(
            alert_id=alert_id,
            inferred_techniques=[],
            candidates_considered=[],
            needs_human_review=True,
        )

    monkeypatch.setattr(alerts, "run_inference", fake_run_inference)
    response = await client.post(
        "/alerts/infer/batch",
        json={
            "alerts": [
                {"alert_id": "first", "narrative": "alert one"},
                {"narrative": "alert two"},
            ]
        },
    )

    assert response.status_code == 200
    results = response.json()["results"]
    assert results[0]["alert_id"] == "first"
    assert results[1]["alert_id"]
    assert results[1]["alert_id"] != "first"


async def test_batch_converts_one_timeout_to_safe_no_match(client, monkeypatch):
    def fake_run_inference(*, alert_id, narrative, retriever):
        if narrative == "timeout":
            raise TimeoutError("internal provider detail")
        return ATTACKInferenceResult(
            alert_id=alert_id,
            inferred_techniques=[],
            candidates_considered=[],
            needs_human_review=True,
        )

    monkeypatch.setattr(alerts, "run_inference", fake_run_inference)
    response = await client.post(
        "/alerts/infer/batch",
        json={
            "alerts": [
                {"alert_id": "ok", "narrative": "normal"},
                {"alert_id": "failed", "narrative": "timeout"},
            ]
        },
    )

    assert response.status_code == 200
    results = response.json()["results"]
    assert [item["alert_id"] for item in results] == ["ok", "failed"]
    assert results[1]["inferred_techniques"] == []
    assert results[1]["candidates_considered"] == []
    assert results[1]["needs_human_review"] is True
    assert "internal provider detail" not in response.text


async def test_batch_rejects_empty_or_oversized_batches(client):
    empty = await client.post("/alerts/infer/batch", json={"alerts": []})
    oversized = await client.post(
        "/alerts/infer/batch",
        json={"alerts": [{"narrative": "alert"}] * 26},
    )

    assert empty.status_code == 422
    assert oversized.status_code == 422


async def test_ui_is_served(client):
    response = await client.get("/ui")
    assert response.status_code == 200
    assert "Security Alert" in response.text
    assert "inferred_techniques" in response.text
