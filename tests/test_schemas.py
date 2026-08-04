import pytest
from pydantic import ValidationError

from src.schemas import TechniqueCandidate


def test_technique_candidate_accepts_valid_data():
    # สร้างข้อมูลที่มี field ครบตาม schema
    candidate = TechniqueCandidate(
        technique_id="T1110",
        technique_name="Brute Force",
        tactic="credential-access",
        description_excerpt="Adversaries may use brute force techniques.",
        stix_version="19.1",
    )

    # ตรวจว่าข้อมูลถูกเก็บตรงตามที่ส่งเข้าไป
    assert candidate.technique_id == "T1110"
    assert candidate.technique_name == "Brute Force"
    assert candidate.tactic == "credential-access"
    assert candidate.stix_version == "19.1"


def test_technique_candidate_rejects_missing_required_fields():
    # ข้อมูลที่ไม่มี technique_id ควรถูก schema ปฏิเสธ
    with pytest.raises(ValidationError):
        TechniqueCandidate(
            technique_name="Brute Force",
            tactic="credential-access",
            description_excerpt="Missing technique ID",
            stix_version="19.1",
        )
