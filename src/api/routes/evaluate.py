"""Bounded evaluation of the bundled synthetic dataset only."""
import logging
from typing import Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, ConfigDict, Field

from eval.evaluator import create_report

router = APIRouter()


class EvaluationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    mode: Literal["fixture", "runtime"] = "runtime"
    top_k: int = Field(default=5, ge=1, le=25, strict=True)


@router.post("/evaluate")
def evaluate_dataset(request: EvaluationRequest) -> dict:
    """Use a worker thread; never accept paths, alerts, keys, or provider mode."""
    try:
        return create_report(mode=request.mode, top_k=request.top_k)
    except (OSError, ValueError, TypeError, KeyError):
        raise HTTPException(
            status_code=503,
            detail={"code": "EVALUATION_UNAVAILABLE", "message": "Evaluation inputs or knowledge base are unavailable or invalid."},
        ) from None
    except Exception:
        logging.getLogger(__name__).error("evaluation failed")
        raise HTTPException(
            status_code=500,
            detail={"code": "EVALUATION_FAILED", "message": "Evaluation could not be completed."},
        ) from None
