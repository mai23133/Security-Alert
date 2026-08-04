import json

from src.rag import ingest_stix


def create_attack_pattern(
    technique_id="T1110",
    tactic="credential-access",
    platform="Windows",
    deprecated=False,
    revoked=False,
):
    # สร้างข้อมูล STIX จำลองเพื่อไม่ต้องใช้ไฟล์ MITRE จริง
    return {
        "type": "attack-pattern",
        "name": "Brute Force",
        "description": "Adversaries may use brute force techniques.",
        "external_references": [
            {
                "source_name": "mitre-attack",
                "external_id": technique_id,
            }
        ],
        "kill_chain_phases": [
            {
                "kill_chain_name": "mitre-attack",
                "phase_name": tactic,
            }
        ],
        "x_mitre_platforms": [platform],
        "x_mitre_deprecated": deprecated,
        "revoked": revoked,
    }


def test_in_scope_accepts_supported_technique():
    # Windows และ credential-access อยู่ในขอบเขตของโปรเจกต์
    stix_object = create_attack_pattern()

    assert ingest_stix.in_scope(stix_object) is True


def test_in_scope_rejects_unsupported_tactic():
    # persistence ไม่ได้อยู่ในสาม tactics ที่กำหนด
    stix_object = create_attack_pattern(tactic="persistence")

    assert ingest_stix.in_scope(stix_object) is False


def test_in_scope_rejects_unsupported_platform():
    # macOS ไม่ได้อยู่ในขอบเขต Windows และ Linux
    stix_object = create_attack_pattern(platform="macOS")

    assert ingest_stix.in_scope(stix_object) is False


def test_in_scope_rejects_deprecated_technique():
    # Technique ที่ deprecated ต้องไม่ถูกนำมาใช้
    stix_object = create_attack_pattern(deprecated=True)

    assert ingest_stix.in_scope(stix_object) is False


def test_in_scope_rejects_revoked_technique():
    # Technique ที่ถูก revoked ต้องไม่ถูกนำมาใช้
    stix_object = create_attack_pattern(revoked=True)

    assert ingest_stix.in_scope(stix_object) is False


def test_main_writes_files_to_processed_directory(
    tmp_path,
    monkeypatch,
):
    # สร้าง STIX bundle จำลองในพื้นที่ชั่วคราวของ pytest
    raw_file = tmp_path / "enterprise-attack-19.1.json"
    output_directory = tmp_path / "processed"
    ids_file = output_directory / "technique_ids.json"
    candidates_file = output_directory / "technique_candidates.json"

    bundle = {
        "type": "bundle",
        "objects": [
            create_attack_pattern(),
            create_attack_pattern(
                technique_id="T9999",
                tactic="persistence",
            ),
        ],
    }

    raw_file.write_text(
        json.dumps(bundle),
        encoding="utf-8",
    )

    # เปลี่ยน path เฉพาะตอนทดสอบเพื่อไม่เขียนทับข้อมูลจริง
    monkeypatch.setattr(ingest_stix, "STIX_PATH", raw_file)
    monkeypatch.setattr(
        ingest_stix,
        "OUTPUT_DIR",
        output_directory,
    )
    monkeypatch.setattr(
        ingest_stix,
        "TECHNIQUE_IDS_PATH",
        ids_file,
    )
    monkeypatch.setattr(
        ingest_stix,
        "TECHNIQUE_CANDIDATES_PATH",
        candidates_file,
    )

    ingest_stix.main()

    # ตรวจว่า ingestion สร้างไฟล์ครบในโฟลเดอร์ที่กำหนด
    assert output_directory.is_dir()
    assert ids_file.is_file()
    assert candidates_file.is_file()

    technique_ids = json.loads(
        ids_file.read_text(encoding="utf-8")
    )
    candidates = json.loads(
        candidates_file.read_text(encoding="utf-8")
    )

    # T1110 ผ่านเงื่อนไข ส่วน T9999 ถูกตัดเพราะ tactic ไม่รองรับ
    assert technique_ids == ["T1110"]
    assert len(candidates) == 1
    assert candidates[0]["technique_id"] == "T1110"
    assert candidates[0]["tactic"] == "credential-access"
