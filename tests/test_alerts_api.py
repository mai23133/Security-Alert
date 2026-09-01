import pytest
from httpx import ASGITransport, AsyncClient

from src.api.main import app


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
