"""
POST /alerts/infer  — Week 3 stub
ตอนนี้ alert_parser + tactic_router ทำงานจริง
แต่ retriever/inferencer/judge ยังเป็น mock (Week 4–8)
"""
import uuid
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from src.schemas import ATTACKInferenceResult, InferredTechnique, TechniqueCandidate
from src.agents.alert_parser import parse_alert
from src.agents.tactic_router import route_tactics

router = APIRouter()

class AlertRequest(BaseModel):
    alert_id: str | None = None
    narrative: str

@router.post("/infer", response_model=ATTACKInferenceResult)
def infer_techniques(req: AlertRequest):
    alert_id = req.alert_id or str(uuid.uuid4())[:8]

    try:
        # ขั้นตอนจริง: parse + route
        parsed = parse_alert(req.narrative)
        tactics = route_tactics(parsed)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    # --- STUB: retriever + inferencer + judge (Week 4–8) ---
    mock_candidates = [
        TechniqueCandidate(
            technique_id="T1110",
            technique_name="Brute Force",
            tactic="credential-access",
            description_excerpt="Adversaries may use brute force techniques...",
            stix_version="19.1",
        ),
        TechniqueCandidate(
            technique_id="T1059.001",
            technique_name="PowerShell",
            tactic="execution",
            description_excerpt="Adversaries may abuse PowerShell commands...",
            stix_version="19.1",
        ),
    ]
    mock_inferred = [
        InferredTechnique(
            technique_id="T1110",
            technique_name="Brute Force",
            tactic="credential-access",
            confidence=0.91,
            evidence_spans=["[STUB] evidence linking coming in Week 6–7"],
            mitre_url="https://attack.mitre.org/techniques/T1110/",
        ),
    ]
    # -------------------------------------------------------

    return ATTACKInferenceResult(
        alert_id=alert_id,
        inferred_techniques=mock_inferred,
        candidates_considered=mock_candidates,
        needs_human_review=len(mock_inferred) == 0,
    )