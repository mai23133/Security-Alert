"""Offline fixture and runtime evaluation against the pinned course dataset."""
from __future__ import annotations

import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

from eval.metrics import PARENT_MATCH_CREDIT, evaluate
from eval.run_eval import (
    DEFAULT_ALLOWLIST, DEFAULT_DATASET, DEFAULT_PREDICTIONS, PROJECT_ROOT,
    build_records, validate_dataset, validate_predictions,
)
from src.schemas import ATTACKInferenceResult

SNAPSHOT = PROJECT_ROOT / "data/eval/technique_ids-v19.1.json"
STIX_VERSION = "enterprise-attack-19.1"
DISCLAIMER = "Advisory evaluation only. Dataset labels require review; substring grounding is not semantic validation."


def _json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def _hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _code_hash() -> str:
    digest = hashlib.sha256()
    for base in ("src", "eval"):
        for path in sorted((PROJECT_ROOT / base).rglob("*.py")):
            digest.update(str(path.relative_to(PROJECT_ROOT)).encode())
            digest.update(path.read_bytes())
    return digest.hexdigest()


def _commit() -> str | None:
    try:
        return subprocess.check_output(
            ["git", "-C", str(PROJECT_ROOT), "rev-parse", "HEAD"],
            text=True, stderr=subprocess.DEVNULL, timeout=2,
        ).strip()
    except (OSError, subprocess.SubprocessError):
        return None


def runtime_predictions(dataset: dict, retriever, *, top_k: int = 5) -> dict:
    from src.inference_pipeline import run_inference

    predictions = []
    for alert in dataset["alerts"]:
        result = run_inference(
            alert_id=alert["alert_id"], narrative=alert["narrative"],
            retriever=retriever, top_k=top_k, use_provider=False,
        )
        # Validate structure, but retain quality errors (e.g. unknown IDs) for metrics.
        checked = ATTACKInferenceResult.model_validate(result).model_dump()
        if checked["alert_id"] != alert["alert_id"]:
            raise ValueError("runtime prediction alert_id mismatch")
        predictions.append({
            "alert_id": checked["alert_id"],
            "inferred_techniques": checked["inferred_techniques"],
            "candidates": checked["candidates_considered"],
            "needs_human_review": checked["needs_human_review"],
        })
    return {"predictions": predictions}


def create_report(
    *, mode: Literal["fixture", "runtime"] = "runtime", top_k: int = 5,
    dataset_path: Path = DEFAULT_DATASET,
    predictions_path: Path = DEFAULT_PREDICTIONS,
    allowlist_path: Path = DEFAULT_ALLOWLIST,
) -> dict:
    if mode not in {"fixture", "runtime"}:
        raise ValueError("mode must be fixture or runtime")
    if isinstance(top_k, bool) or not isinstance(top_k, int) or not 1 <= top_k <= 25:
        raise ValueError("top_k must be an integer from 1 to 25")
    dataset = _json(dataset_path)
    canonical_ids = _json(DEFAULT_ALLOWLIST)
    supplied_ids = _json(allowlist_path)
    snapshot_ids = _json(SNAPSHOT)
    for ids in (canonical_ids, supplied_ids, snapshot_ids):
        if not isinstance(ids, list) or any(not isinstance(item, str) for item in ids):
            raise ValueError("allowlist must be a list of strings")
        if len(set(ids)) != len(ids):
            raise ValueError("duplicate allowlist IDs")
    allowlist = set(canonical_ids)
    if set(supplied_ids) != allowlist or set(snapshot_ids) != allowlist:
        raise ValueError("evaluation allowlist differs from generated pinned allowlist")
    metadata = dataset.get("metadata", {})
    if metadata.get("stix_version") != STIX_VERSION or not metadata.get("dataset_version"):
        raise ValueError("dataset requires version metadata matching pinned STIX")
    validate_dataset(dataset, allowlist)

    if mode == "fixture":
        predictions = _json(predictions_path)
        validate_predictions(predictions, dataset, allowlist)
        model_version = predictions.get("metadata", {}).get("model_version", "unspecified")
        prompt_version = predictions.get("metadata", {}).get("prompt_version", "none")
        prediction_hash = _hash(predictions_path)
    else:
        from src.rag.retriever import BaselineRetriever
        retriever = BaselineRetriever(
            PROJECT_ROOT / "data/processed/technique_candidates.json", DEFAULT_ALLOWLIST,
        )
        if {item.technique_id for item in retriever.candidates} != allowlist:
            raise ValueError("candidate IDs differ from pinned allowlist")
        if any(item.stix_version != "19.1" for item in retriever.candidates):
            raise ValueError("candidate version differs from pinned STIX")
        predictions = runtime_predictions(dataset, retriever, top_k=top_k)
        model_version = "lexical-baseline-offline"
        prompt_version = "provider-disabled"
        prediction_hash = hashlib.sha256(
            json.dumps(predictions, sort_keys=True).encode()
        ).hexdigest()
    records = build_records(dataset, predictions)
    metrics = evaluate(records, allowlist)
    gates = {
        "exact_f1_at_least_0_70": metrics["exact_technique"]["f1"] >= 0.70,
        "parent_recall_at_least_0_90": metrics["parent_technique_recall"] >= 0.90,
        "grounding_at_least_0_85": metrics["evidence_grounding_rate"] >= 0.85,
        "hallucinated_id_rate_is_zero": metrics["hallucinated_id_rate"] == 0.0,
    }
    return {
        "metadata": {
            "report_kind": "fixture_validation" if mode == "fixture" else "runtime_quality",
            "not_a_runtime_quality_gate": mode == "fixture",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "commit": _commit(),
            "code_sha256": _code_hash(),
            "dataset_version": metadata["dataset_version"],
            "dataset_sha256": _hash(dataset_path),
            "label_review_status": metadata.get("label_review_status", "unspecified"),
            "stix_version": STIX_VERSION,
            "stix_sha256": _hash(PROJECT_ROOT / "data/raw/enterprise-attack-19.1.json"),
            "allowlist_sha256": _hash(DEFAULT_ALLOWLIST),
            "candidates_sha256": _hash(PROJECT_ROOT / "data/processed/technique_candidates.json"),
            "prediction_sha256": prediction_hash,
            "model_version": model_version,
            "prompt_version": prompt_version,
            "provider_mode": "disabled",
            "top_k": top_k if mode == "runtime" else None,
            "parent_match_credit": PARENT_MATCH_CREDIT,
            "grounding_kind": "exact_substring_only",
        },
        "metrics": metrics,
        "quality_gates": gates,
        "numeric_gates_passed": all(gates.values()),
        # Neither fixture nor substring-only evaluation constitutes course acceptance.
        "acceptance_ready": False,
        "acceptance_blockers": [
            "Gold-label approval and dataset composition require course confirmation.",
            "Semantic grounding and final subset approval remain outstanding.",
        ],
        "disclaimer": DISCLAIMER,
    }
