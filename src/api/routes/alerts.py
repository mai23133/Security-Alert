"""Alert inference endpoints backed by the integrated A+B pipeline."""
from __future__ import annotations

import logging
import uuid
from pathlib import Path

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, ConfigDict, Field, field_validator

from src.inference_pipeline import run_inference
from src.rag.retriever import BaselineRetriever
from src.schemas import ATTACKInferenceResult

router = APIRouter()
logger = logging.getLogger(__name__)
PROJECT_ROOT = Path(__file__).resolve().parents[3]
MAX_NARRATIVE_LENGTH = 20_000
MAX_BATCH_SIZE = 25
RETRIEVER = BaselineRetriever(
    PROJECT_ROOT / "data" / "processed" / "technique_candidates.json",
    PROJECT_ROOT / "data" / "processed" / "technique_ids.json",
)

class AlertRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    alert_id: str | None = Field(default=None, max_length=128)
    narrative: str = Field(min_length=1, max_length=MAX_NARRATIVE_LENGTH)

    @field_validator("alert_id")
    @classmethod
    def reject_blank_alert_id(cls, value: str | None) -> str | None:
        if value is not None and not value:
            raise ValueError("alert_id must not be blank")
        return value


class BatchAlertRequest(BaseModel):
    alerts: list[AlertRequest] = Field(min_length=1, max_length=MAX_BATCH_SIZE)


class BatchInferenceResult(BaseModel):
    results: list[ATTACKInferenceResult]


def _run_alert(request: AlertRequest) -> ATTACKInferenceResult:
    alert_id = request.alert_id or str(uuid.uuid4())
    try:
        return run_inference(
            alert_id=alert_id,
            narrative=request.narrative,
            retriever=RETRIEVER,
        )
    except TimeoutError as exc:
        logger.warning("inference timeout alert_id=%s", alert_id)
        raise HTTPException(
            status_code=504,
            detail={
                "code": "INFERENCE_TIMEOUT",
                "message": "Inference timed out. Human review is required.",
            },
        ) from exc
    except (FileNotFoundError, OSError) as exc:
        logger.warning("knowledge base unavailable alert_id=%s", alert_id)
        raise HTTPException(
            status_code=503,
            detail={
                "code": "KNOWLEDGE_BASE_UNAVAILABLE",
                "message": "Pinned ATT&CK knowledge base is unavailable.",
            },
        ) from exc
    except Exception as exc:
        logger.exception("inference failed alert_id=%s", alert_id)
        raise HTTPException(
            status_code=500,
            detail={
                "code": "INTERNAL_ERROR",
                "message": "Inference could not be completed.",
            },
        ) from exc

@router.post("/infer", response_model=ATTACKInferenceResult)
async def infer_techniques(request: AlertRequest) -> ATTACKInferenceResult:
    return _run_alert(request)


@router.post("/infer/batch", response_model=BatchInferenceResult)
async def infer_alert_batch(request: BatchAlertRequest) -> BatchInferenceResult:
    """Infer a bounded batch while preserving input order.

    A failed item becomes a safe no-match so one failure does not discard the
    remaining results. Errors never become fabricated predictions or evidence.
    """
    results: list[ATTACKInferenceResult] = []
    for alert in request.alerts:
        alert_id = alert.alert_id or str(uuid.uuid4())
        try:
            results.append(_run_alert(alert.model_copy(update={"alert_id": alert_id})))
        except HTTPException as exc:
            logger.warning(
                "batch item failed alert_id=%s error_code=%s",
                alert_id,
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
