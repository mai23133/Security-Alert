"""Alert inference endpoints backed by the integrated A+B pipeline."""
from __future__ import annotations

import logging
import uuid
from pathlib import Path
from typing import Literal

from fastapi import APIRouter, HTTPException, Request, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field, field_validator

from src.inference_pipeline import run_inference
from src.rag.retriever import BaselineRetriever
from src.schemas import ATTACKInferenceResult
from src.api.runtime import get_retriever, run_bounded

router = APIRouter()
logger = logging.getLogger(__name__)
PROJECT_ROOT = Path(__file__).resolve().parents[3]
MAX_NARRATIVE_LENGTH = 20_000
MAX_BATCH_SIZE = 25

class AlertRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    alert_id: str | None = Field(default=None, max_length=128)
    narrative: str = Field(min_length=1, max_length=MAX_NARRATIVE_LENGTH)
    inference_mode: Literal["offline", "gemini", "openrouter"] = "offline"

    @field_validator("alert_id")
    @classmethod
    def reject_blank_alert_id(cls, value: str | None) -> str | None:
        if value is not None and not value:
            raise ValueError("alert_id must not be blank")
        return value


class BatchAlertRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    alerts: list[AlertRequest] = Field(min_length=1, max_length=MAX_BATCH_SIZE)


class BatchInferenceResult(BaseModel):
    results: list[ATTACKInferenceResult]


def _run_alert(request: AlertRequest, retriever: BaselineRetriever,
               trace: dict | None = None) -> ATTACKInferenceResult:
    alert_id = request.alert_id or str(uuid.uuid4())
    try:
        kwargs = dict(
            alert_id=alert_id,
            narrative=request.narrative,
            retriever=retriever,
        )
        if trace is not None:
            kwargs["trace"] = trace
        if request.inference_mode != "offline":
            kwargs["use_provider"] = True
            kwargs["provider"] = request.inference_mode
        return run_inference(**kwargs)
    except TimeoutError as exc:
        logger.warning("inference_timeout")
        raise HTTPException(
            status_code=504,
            detail={
                "code": "INFERENCE_TIMEOUT",
                "message": "Inference timed out. Human review is required.",
            },
        ) from exc
    except (FileNotFoundError, OSError) as exc:
        logger.warning("knowledge_base_unavailable")
        raise HTTPException(
            status_code=503,
            detail={
                "code": "KNOWLEDGE_BASE_UNAVAILABLE",
                "message": "Pinned ATT&CK knowledge base is unavailable.",
            },
        ) from exc
    except Exception as exc:
        logger.error("inference_failed")
        raise HTTPException(
            status_code=500,
            detail={
                "code": "INTERNAL_ERROR",
                "message": "Inference could not be completed.",
            },
        ) from exc

@router.post("/infer", response_model=ATTACKInferenceResult)
async def infer_techniques(request: AlertRequest, http_request: Request,
                           retriever=Depends(get_retriever)) -> JSONResponse:
    trace: dict = {}
    result = await run_bounded(http_request, _run_alert, request, retriever, trace)
    return JSONResponse(content=result.model_dump(mode="json"), headers={
        "X-AI-Parser-Status": trace.get("parser_status", "unknown"),
        "X-AI-Router-Status": trace.get("router_status", "unknown"),
        "X-AI-Judge-Status": trace.get("judge_status", "unknown"),
        "X-AI-Fallback-Used": str(bool(trace.get("fallback_used"))).lower(),
        "X-AI-Parser-Provider": trace.get("parser_provider", "unknown"),
        "X-AI-Router-Provider": trace.get("router_provider", "unknown"),
        "X-AI-Judge-Provider": trace.get("judge_provider", "unknown"),
        "X-AI-Parser-Model": trace.get("parser_model", "none"),
        "X-AI-Router-Model": trace.get("router_model", "none"),
        "X-AI-Judge-Model": trace.get("judge_model", "none"),
        "X-AI-Fallback-Reason": trace.get("fallback_reason", "none"),
        "X-AI-Judge-Fallback-Reason": trace.get("judge_fallback_reason", "none"),
        "X-AI-Inferencer-Status": trace.get("inferencer_status", "unknown"),
        "X-AI-Inferencer-Provider": trace.get("inferencer_provider", "unknown"),
        "X-AI-Inferencer-Model": trace.get("inferencer_model", "none"),
        "X-AI-Inferencer-Fallback-Reason": trace.get("inferencer_fallback_reason", "none"),
        "X-AI-Confidence-Source": trace.get("confidence_source", "unknown"),
        "X-AI-Inference-Prompt-Version": trace.get("inference_prompt_version", "none"),
    })


@router.post("/infer/batch", response_model=BatchInferenceResult)
async def infer_alert_batch(request: BatchAlertRequest, http_request: Request,
                            retriever=Depends(get_retriever)) -> BatchInferenceResult:
    """Infer a bounded batch while preserving input order.

    A failed item becomes a safe no-match so one failure does not discard the
    remaining results. Errors never become fabricated predictions or evidence.
    """
    results: list[ATTACKInferenceResult] = []
    for alert in request.alerts:
        alert_id = alert.alert_id or str(uuid.uuid4())
        try:
            results.append(await run_bounded(http_request, _run_alert,
                alert.model_copy(update={"alert_id": alert_id}), retriever))
        except HTTPException as exc:
            logger.warning(
                "batch_item_failed error_code=%s",
                exc.detail.get("code", "UNKNOWN")
                if isinstance(exc.detail, dict)
                else "UNKNOWN",
            )
            results.append(
                ATTACKInferenceResult(
                    alert_id=alert_id,
                    inferred_techniques=[],
                    candidates_considered=[],
                    needs_human_review=True,
                )
            )
    return BatchInferenceResult(results=results)
