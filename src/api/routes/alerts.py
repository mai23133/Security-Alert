"""
POST /alerts/infer — deterministic ATT&CK retrieval and inference pipeline.
"""
import uuid
from pathlib import Path

from fastapi import APIRouter
from pydantic import BaseModel

from src.inference_pipeline import run_inference
from src.rag.retriever import BaselineRetriever
from src.schemas import ATTACKInferenceResult

router = APIRouter()
PROJECT_ROOT = Path(__file__).resolve().parents[3]
RETRIEVER = BaselineRetriever(
    PROJECT_ROOT / "data" / "processed" / "technique_candidates.json",
    PROJECT_ROOT / "data" / "processed" / "technique_ids.json",
)

class AlertRequest(BaseModel):
    alert_id: str | None = None
    narrative: str

@router.post("/infer", response_model=ATTACKInferenceResult)
async def infer_techniques(req: AlertRequest):
    alert_id = req.alert_id or str(uuid.uuid4())[:8]
    return run_inference(alert_id=alert_id, narrative=req.narrative, retriever=RETRIEVER)
