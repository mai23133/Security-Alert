import json

import pytest
from fastapi.testclient import TestClient

from src.api.routes import taxonomy
from src.api.main import app


client = TestClient(app)


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


def test_health_endpoint():
    # ตรวจว่า API หลักยังทำงานและบอก STIX version ถูกต้อง
    response = client.get("/")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "stix_version": "19.1",
    }


def test_response_contains_mitre_header():
    # ทุก response ต้องมี MITRE attribution header
    response = client.get("/")

    assert response.headers["X-MITRE-ATTaCK-Version"] == (
        "enterprise-attack-19.1"
    )


def test_list_techniques(candidates_file):
    # ตรวจว่า endpoint คืน Technique ทั้งหมด
    response = client.get("/taxonomy/techniques")

    assert response.status_code == 200

    body = response.json()

    assert body["count"] == 2
    assert len(body["techniques"]) == 2
    assert body["techniques"][0]["technique_id"] == "T1110"
    assert body["techniques"][1]["technique_id"] == "T1059.001"


def test_list_techniques_filters_by_tactic(candidates_file):
    # ตรวจการกรอง Technique ด้วย tactic
    response = client.get(
        "/taxonomy/techniques",
        params={"tactic": "execution"},
    )

    assert response.status_code == 200

    body = response.json()

    assert body["count"] == 1
    assert len(body["techniques"]) == 1
    assert body["techniques"][0]["technique_id"] == "T1059.001"
    assert body["techniques"][0]["tactic"] == "execution"


def test_get_technique_by_id(candidates_file):
    # ตรวจการเรียก Technique รายตัว
    response = client.get("/taxonomy/techniques/T1110")

    assert response.status_code == 200

    body = response.json()

    assert body["technique_id"] == "T1110"
    assert body["technique_name"] == "Brute Force"
    assert body["tactic"] == "credential-access"


def test_get_technique_accepts_lowercase_id(candidates_file):
    # Route แปลง Technique ID เป็นตัวพิมพ์ใหญ่ก่อนค้นหา
    response = client.get("/taxonomy/techniques/t1110")

    assert response.status_code == 200
    assert response.json()["technique_id"] == "T1110"


def test_get_unknown_technique_returns_404(candidates_file):
    # Technique ที่ไม่มีใน pinned subset ต้องคืน 404
    response = client.get("/taxonomy/techniques/T9999")

    assert response.status_code == 404
    assert response.json() == {
        "detail": "T9999 not found in pinned subset"
    }


def test_list_techniques_returns_empty_when_file_missing(
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

    response = client.get("/taxonomy/techniques")

    assert response.status_code == 200
    assert response.json() == {
        "count": 0,
        "techniques": [],
    }