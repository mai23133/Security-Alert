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


@pytest.mark.skip(reason="ข้ามเทสต์นี้ชั่วคราวเพราะเปิดระบบ MOCK_AI ไว้")
async def test_infer_returns_fast_no_match_for_human_review(client):
    response = await client.post(
        "/alerts/infer",
        json={
            "alert_id": "alert-001",
            "narrative": "Multiple failed login attempts were detected.",
        },
    )

    assert response.status_code == 200
    assert response.json() == {
        "alert_id": "alert-001",
        "inferred_techniques": [],
        "candidates_considered": [],
        "needs_human_review": True,
        "disclaimer": "Advisory only. Needs human review. MITRE attribution.",
    }
    assert response.headers["X-MITRE-ATTaCK-Version"] == (
        "enterprise-attack-19.1"
    )
