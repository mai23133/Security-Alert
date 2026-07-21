import json

import pytest
from httpx import ASGITransport, AsyncClient

from src.api.routes import taxonomy
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


@pytest.fixture
def candidates_file(tmp_path, monkeypatch):
    # สร้างข้อมูลจำลองโดยไม่ใช้ไฟล์ data/processed ของจริง
    test_file = tmp_path / "technique_candidates.json"

    candidates = [
        {
            "technique_id": "T1110",
            "technique_name": "Brute Force",
            "tactic": "credential-access",
            "description_excerpt": "Adversaries may use brute force techniques.",
            "stix_version": "19.1",
        },
        {
            "technique_id": "T1059.001",
            "technique_name": "PowerShell",
            "tactic": "execution",
            "description_excerpt": "Adversaries may abuse PowerShell commands.",
            "stix_version": "19.1",
        },
    ]

    test_file.write_text(
        json.dumps(candidates),
        encoding="utf-8",
    )

    # เปลี่ยน path ของ taxonomy เฉพาะระหว่างทดสอบ
    monkeypatch.setattr(
        taxonomy,
        "CANDIDATES_PATH",
        test_file,
    )

    return test_file


async def test_health_endpoint(client):
    # ตรวจว่า API หลักยังทำงานและบอก STIX version ถูกต้อง
    response = await client.get("/")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "stix_version": "19.1",
    }


async def test_response_contains_mitre_header(client):
    # ทุก response ต้องมี MITRE attribution header
    response = await client.get("/")

    assert response.headers["X-MITRE-ATTaCK-Version"] == (
        "enterprise-attack-19.1"
    )


async def test_list_techniques(client, candidates_file):
    # ตรวจว่า endpoint คืน Technique ทั้งหมด
    response = await client.get("/taxonomy/techniques")

    assert response.status_code == 200

    body = response.json()

    assert body["count"] == 2
    assert len(body["techniques"]) == 2
    assert body["techniques"][0]["technique_id"] == "T1110"
    assert body["techniques"][1]["technique_id"] == "T1059.001"


async def test_list_techniques_filters_by_tactic(client, candidates_file):
    # ตรวจการกรอง Technique ด้วย tactic
    response = await client.get(
        "/taxonomy/techniques",
        params={"tactic": "execution"},
    )

    assert response.status_code == 200

    body = response.json()

    assert body["count"] == 1
    assert len(body["techniques"]) == 1
    assert body["techniques"][0]["technique_id"] == "T1059.001"
    assert body["techniques"][0]["tactic"] == "execution"


async def test_get_technique_by_id(client, candidates_file):
    # ตรวจการเรียก Technique รายตัว
    response = await client.get("/taxonomy/techniques/T1110")

    assert response.status_code == 200

    body = response.json()

    assert body["technique_id"] == "T1110"
    assert body["technique_name"] == "Brute Force"
    assert body["tactic"] == "credential-access"


async def test_get_technique_accepts_lowercase_id(client, candidates_file):
    # Route แปลง Technique ID เป็นตัวพิมพ์ใหญ่ก่อนค้นหา
    response = await client.get("/taxonomy/techniques/t1110")

    assert response.status_code == 200
    assert response.json()["technique_id"] == "T1110"


async def test_get_unknown_technique_returns_404(client, candidates_file):
    # Technique ที่ไม่มีใน pinned subset ต้องคืน 404
    response = await client.get("/taxonomy/techniques/T9999")

    assert response.status_code == 404
    assert response.json() == {
        "detail": "T9999 not found in pinned subset"
    }


async def test_list_techniques_returns_empty_when_file_missing(
    client,
    tmp_path,
    monkeypatch,
):
    # หากยังไม่มีไฟล์ processed API ต้องคืนรายการว่างและไม่พัง
    missing_file = tmp_path / "missing.json"

    monkeypatch.setattr(
        taxonomy,
        "CANDIDATES_PATH",
        missing_file,
    )

    response = await client.get("/taxonomy/techniques")

    assert response.status_code == 200
    assert response.json() == {
        "count": 0,
        "techniques": [],
    }
