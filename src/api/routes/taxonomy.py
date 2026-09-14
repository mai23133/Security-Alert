"""
GET /taxonomy/techniques       — list in-scope techniques
GET /taxonomy/techniques/{id}  — technique detail from pinned STIX
Week 3 deliverable.
"""
from fastapi import APIRouter, HTTPException, Depends
from src.api.runtime import get_retriever

router = APIRouter()

@router.get("/techniques")
async def list_techniques(tactic: str | None = None, retriever=Depends(get_retriever)):
    candidates = retriever.candidates
    if tactic:
        candidates = [c for c in candidates if c.tactic == tactic]
    return {"count": len(candidates), "techniques": [c.model_dump() for c in candidates]}

@router.get("/techniques/{technique_id}")
async def get_technique(technique_id: str, retriever=Depends(get_retriever)):
    candidates = retriever.candidates
    match = next((c for c in candidates if c.technique_id == technique_id.upper()), None)
    if not match:
        raise HTTPException(status_code=404, detail="Technique not found in pinned subset")
    return match.model_dump()
