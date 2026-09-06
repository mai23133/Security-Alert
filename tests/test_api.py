"""Product-shell scenarios adapted from the original Stream D tests."""
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
        transport=ASGITransport(app=app), base_url="http://testserver"
    ) as test_client:
        yield test_client


async def test_read_root_has_version_and_request_headers(client):
    response = await client.get("/")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "stix_version": "19.1"}
    assert response.headers["x-mitre-attack-version"] == "enterprise-attack-19.1"
    assert response.headers["x-request-id"]


async def test_infer_alert_uses_canonical_response_contract(client):
    response = await client.post(
        "/alerts/infer",
        json={"narrative": "พบการพยายามล็อกอินรหัสผ่านซ้ำหลายครั้ง"},
    )
    assert response.status_code == 200
    assert set(response.json()) == {
        "alert_id", "inferred_techniques", "candidates_considered",
        "needs_human_review", "disclaimer",
    }
    assert response.json()["needs_human_review"] is True


async def test_batch_infer_alerts_uses_specified_path_and_contract(client):
    response = await client.post(
        "/alerts/infer/batch",
        json={"alerts": [
            {"narrative": "Alert ตัวที่ 1 ทดสอบระบบ"},
            {"narrative": "Alert ตัวที่ 2 ทดสอบระบบ"},
        ]},
    )
    assert response.status_code == 200
    results = response.json()["results"]
    assert len(results) == 2
    assert all("inferred_techniques" in result for result in results)
