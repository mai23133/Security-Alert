"""Bounded evaluation of the bundled synthetic dataset only."""
import logging
from typing import Literal

from fastapi import APIRouter, HTTPException, Depends, Request
from functools import partial
from src.api.runtime import get_retriever, run_bounded
from pydantic import BaseModel, ConfigDict, Field

from eval.evaluator import create_report

router = APIRouter()


class EvaluationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    mode: Literal["fixture", "runtime"] = "runtime"
    top_k: int = Field(default=5, ge=1, le=25, strict=True)
    diagnostics: bool = False


@router.post("/evaluate")
async def evaluate_dataset(request: EvaluationRequest, http_request: Request,
                           retriever=Depends(get_retriever)) -> dict:
    """Use a worker thread; never accept paths, alerts, keys, or provider mode."""
    try:
        return await run_bounded(http_request, partial(create_report, mode=request.mode,
            top_k=request.top_k, retriever=retriever, diagnostics=request.diagnostics))
    except HTTPException:
        raise
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
