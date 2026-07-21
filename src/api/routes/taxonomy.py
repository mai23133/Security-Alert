"""
GET /taxonomy/techniques       — list in-scope techniques
GET /taxonomy/techniques/{id}  — technique detail from pinned STIX
Week 3 deliverable.
"""
import json
from pathlib import Path
from fastapi import APIRouter, HTTPException
from src.schemas import TechniqueCandidate

router = APIRouter()

PROJECT_ROOT = Path(__file__).resolve().parents[3]
CANDIDATES_PATH = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "technique_candidates.json"
)

def _load_candidates() -> list[TechniqueCandidate]:
    if not CANDIDATES_PATH.exists():
        return []
    raw = json.loads(CANDIDATES_PATH.read_text())
    return [TechniqueCandidate(**r) for r in raw]

@router.get("/techniques")
async def list_techniques(tactic: str | None = None):
    candidates = _load_candidates()
    if tactic:
        candidates = [c for c in candidates if c.tactic == tactic]
    return {"count": len(candidates), "techniques": [c.model_dump() for c in candidates]}

@router.get("/techniques/{technique_id}")
async def get_technique(technique_id: str):
    candidates = _load_candidates()
    match = next((c for c in candidates if c.technique_id == technique_id.upper()), None)
    if not match:
        raise HTTPException(status_code=404, detail=f"{technique_id} not found in pinned subset")
    return match.model_dump()
