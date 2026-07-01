"""
Pydantic schemas for the Security Alert -> ATT&CK Technique Inference project.
Matches spec section 6 exactly. Week 2 deliverable.
"""
import re
from pydantic import BaseModel, field_validator

TECHNIQUE_ID_PATTERN = re.compile(r"^T\d{4}(\.\d{3})?$")


class ParsedAlert(BaseModel):
    narrative: str
    assets: list[str]
    observed_actions: list[str]
    iocs: list[str]


class TechniqueCandidate(BaseModel):
    technique_id: str          # e.g. "T1110"
    technique_name: str
    tactic: str
    description_excerpt: str
    stix_version: str          # e.g. "19.1"

    @field_validator("technique_id")
    @classmethod
    def validate_technique_id(cls, v: str) -> str:
        if not TECHNIQUE_ID_PATTERN.match(v):
            raise ValueError(f"Invalid technique_id format: {v} (expected T#### or T####.###)")
        return v


class InferredTechnique(BaseModel):
    technique_id: str
    technique_name: str
    tactic: str
    confidence: float
    evidence_spans: list[str]  # quotes from input
    mitre_url: str

    @field_validator("technique_id")
    @classmethod
    def validate_technique_id(cls, v: str) -> str:
        if not TECHNIQUE_ID_PATTERN.match(v):
            raise ValueError(f"Invalid technique_id format: {v} (expected T#### or T####.###)")
        return v

    @field_validator("confidence")
    @classmethod
    def validate_confidence(cls, v: float) -> float:
        if not 0.0 <= v <= 1.0:
            raise ValueError(f"confidence must be in [0, 1], got {v}")
        return v


class ATTACKInferenceResult(BaseModel):
    alert_id: str
    inferred_techniques: list[InferredTechnique]
    candidates_considered: list[TechniqueCandidate]
    needs_human_review: bool
    disclaimer: str = "Advisory tagging only. Not autonomous SOC action. Verify with senior analyst."


if __name__ == "__main__":
    # Smoke test using the worked example from spec section 7
    sample = ATTACKInferenceResult(
        alert_id="demo-001",
        inferred_techniques=[
            InferredTechnique(
                technique_id="T1110",
                technique_name="Brute Force",
                tactic="credential-access",
                confidence=0.91,
                evidence_spans=["847 failed RDP authentication attempts"],
                mitre_url="https://attack.mitre.org/techniques/T1110/",
            ),
            InferredTechnique(
                technique_id="T1059.001",
                technique_name="PowerShell",
                tactic="execution",
                confidence=0.87,
                evidence_spans=["execution of encoded PowerShell"],
                mitre_url="https://attack.mitre.org/techniques/T1059/001/",
            ),
        ],
        candidates_considered=[],
        needs_human_review=False,
    )
    print(sample.model_dump_json(indent=2))
