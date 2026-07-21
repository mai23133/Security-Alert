"""
POST /alerts/infer  — Week 3 stub
The inference pipeline is not integrated yet, so this route returns a
deterministic no-match result for human review without calling an LLM.
"""
import uuid
from fastapi import APIRouter
from pydantic import BaseModel

from src.schemas import ATTACKInferenceResult

router = APIRouter()

class AlertRequest(BaseModel):
    alert_id: str | None = None
    narrative: str

@router.post("/infer", response_model=ATTACKInferenceResult)
async def infer_techniques(req: AlertRequest):
    alert_id = req.alert_id or str(uuid.uuid4())[:8]

    return ATTACKInferenceResult(
        alert_id=alert_id,
        inferred_techniques=[],
        candidates_considered=[],
        needs_human_review=True,
    )
