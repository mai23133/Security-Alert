"""Inspectable deterministic retrieval endpoint."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, ConfigDict, Field, field_validator

from src.api.routes.alerts import MAX_NARRATIVE_LENGTH, RETRIEVER
from src.agents.tactic_router import IN_SCOPE_TACTICS
from src.schemas import TechniqueCandidate

router = APIRouter()
MAX_TOP_K = 25


class RAGSearchRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    narrative: str = Field(min_length=1, max_length=MAX_NARRATIVE_LENGTH)
    tactic: list[str] | None = None
    top_k: int = Field(default=5, ge=1, le=MAX_TOP_K, strict=True)

    @field_validator("tactic")
    @classmethod
    def validate_tactics(cls, value: list[str] | None) -> list[str] | None:
        if not value:
            return None
        invalid = sorted(set(value) - set(IN_SCOPE_TACTICS))
        if invalid:
            raise ValueError(f"unsupported tactic: {', '.join(invalid)}")
        return list(dict.fromkeys(value))


class RAGSearchResult(BaseModel):
    candidates: list[TechniqueCandidate]


@router.post("/search", response_model=RAGSearchResult)
async def search_candidates(request: RAGSearchRequest) -> RAGSearchResult:
    try:
        candidates = RETRIEVER.search(
            request.narrative,
            tactic=request.tactic,
            top_k=request.top_k,
        )
    except (FileNotFoundError, OSError) as exc:
        raise HTTPException(
            status_code=503,
            detail={
                "code": "KNOWLEDGE_BASE_UNAVAILABLE",
                "message": "Pinned ATT&CK knowledge base is unavailable.",
            },
        ) from exc
    return RAGSearchResult(candidates=candidates)
