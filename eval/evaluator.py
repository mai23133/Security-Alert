"""Offline fixture and runtime evaluation against the pinned course dataset."""
from __future__ import annotations

import hashlib
import json
import subprocess
import platform
from importlib.metadata import distributions
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
ITERATION_2_SUBSET = PROJECT_ROOT / "data/eval/iteration-2-v0.2.0-subset.json"
STIX_VERSION = "enterprise-attack-19.1"
DISCLAIMER = "Advisory evaluation only. Dataset labels require review. Verbatim and behavior-rule checks are not independent expert semantic validation."


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


def runtime_predictions(dataset: dict, retriever, *, top_k: int = 5, traces: dict | None = None) -> dict:
    from src.inference_pipeline import run_inference

    predictions = []
    for alert in dataset["alerts"]:
        trace = {}
        result = run_inference(
            alert_id=alert["alert_id"], narrative=alert["narrative"],
            retriever=retriever, top_k=top_k, use_provider=False,
            **({"trace": trace} if traces is not None else {}),
        )
        if traces is not None:
            traces[alert["alert_id"]] = trace
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


def _select_iteration_subset(
    dataset: dict, predictions: dict, subset_path: Path | None
) -> tuple[dict, dict, dict]:
    """Return a validated 5--10 item release subset, or the complete pack."""
    if subset_path is None:
        return dataset, predictions, {"scope": "full_course_pack", "alert_count": len(dataset["alerts"])}
    subset = _json(subset_path)
    alert_ids = subset.get("alert_ids")
    if (
        not isinstance(alert_ids, list)
        or not 5 <= len(alert_ids) <= 10
        or any(not isinstance(alert_id, str) or not alert_id for alert_id in alert_ids)
        or len(alert_ids) != len(set(alert_ids))
    ):
        raise ValueError("evaluation subset must contain 5-10 unique nonempty alert IDs")
    dataset_by_id = {alert["alert_id"]: alert for alert in dataset["alerts"]}
    prediction_by_id = {prediction["alert_id"]: prediction for prediction in predictions["predictions"]}
    missing = set(alert_ids) - set(dataset_by_id)
    if missing:
        raise ValueError("evaluation subset references an unknown alert ID")
    return (
        {**dataset, "alerts": [dataset_by_id[alert_id] for alert_id in alert_ids]},
        {**predictions, "predictions": [prediction_by_id[alert_id] for alert_id in alert_ids]},
        {
            "scope": subset.get("scope", "named_subset"),
            "version": subset.get("version", "unspecified"),
            "alert_count": len(alert_ids),
            "sha256": _hash(subset_path),
        },
    )


def create_report(
    *, mode: Literal["fixture", "runtime"] = "runtime", top_k: int = 5,
    dataset_path: Path = DEFAULT_DATASET,
    predictions_path: Path = DEFAULT_PREDICTIONS,
    allowlist_path: Path = DEFAULT_ALLOWLIST,
    subset_path: Path | None = None,
    retriever=None, development: bool = False, diagnostics: bool = False,
) -> dict:
    if mode not in {"fixture", "runtime"}:
        raise ValueError("mode must be fixture or runtime")
    if isinstance(top_k, bool) or not isinstance(top_k, int) or not 1 <= top_k <= 25:
        raise ValueError("top_k must be an integer from 1 to 25")
    dataset = _json(dataset_path)
    if development and (mode != "runtime" or subset_path is not None):
        raise ValueError("Development evaluation requires runtime mode and the full development set")
    canonical_ids = sorted(retriever.allowlist_ids) if retriever else _json(DEFAULT_ALLOWLIST)
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
    validate_dataset(dataset, allowlist, course_pack=not development)
    traces = {}

    if mode == "fixture":
        predictions = _json(predictions_path)
        validate_predictions(predictions, dataset, allowlist)
        model_version = predictions.get("metadata", {}).get("model_version", "unspecified")
        prompt_version = predictions.get("metadata", {}).get("prompt_version", "none")
        prediction_hash = _hash(predictions_path)
    else:
        from src.rag.retriever import BaselineRetriever
        if retriever is None:
            from src.api.runtime import load_knowledge_base, SNAPSHOT_PATH
            retriever = load_knowledge_base(SNAPSHOT_PATH)
        if {item.technique_id for item in retriever.candidates} != allowlist:
            raise ValueError("candidate IDs differ from pinned allowlist")
        if any(item.stix_version != "19.1" for item in retriever.candidates):
            raise ValueError("candidate version differs from pinned STIX")
        predictions = runtime_predictions(dataset, retriever, top_k=top_k, traces=traces if diagnostics else None)
        from src.agents.behavior import VERSION
        model_version = VERSION
        prompt_version = "provider-disabled"
        prediction_hash = hashlib.sha256(
            json.dumps(predictions, sort_keys=True).encode()
        ).hexdigest()
    selected_dataset, selected_predictions, subset_metadata = _select_iteration_subset(
        dataset, predictions, subset_path
    )
    records = build_records(selected_dataset, selected_predictions)
    metrics = evaluate(records, allowlist)
    if mode == "runtime":
        from src.agents.behavior import contextual_span_valid
        predictions_flat = [(r, p) for r in records for p in r["inferred_techniques"]]
        metrics["behavior_evidence_rate"] = sum(bool(p["evidence_spans"]) and all(
            contextual_span_valid(r["narrative"], span, p["technique_id"], p["technique_name"])
            for span in p["evidence_spans"]) for r, p in predictions_flat) / max(1, len(predictions_flat))
        by_id = {c.technique_id: c for c in retriever.candidates}
        metrics["tactic_accuracy"] = sum(
            {p["tactic"] for p in r["inferred_techniques"]} == {by_id[t].tactic for t in r["gold_technique_ids"]}
            for r in records) / max(1, len(records))
        metrics["negative_control_count"] = sum(r["category"] == "negative" for r in records)
    case_results = []
    for record in records:
        gold = set(record["gold_technique_ids"])
        predicted = {item["technique_id"] for item in record["inferred_techniques"]}
        if predicted == gold:
            match = "Exact"
        elif any("." in technique_id and technique_id.split(".", 1)[0] in predicted
                 for technique_id in gold):
            match = "Parent"
        else:
            match = "Miss"
        predictions_for_case = record["inferred_techniques"]
        grounded = None if not predictions_for_case else all(
            isinstance(item.get("evidence_spans"), list)
            and bool(item["evidence_spans"])
            and all(isinstance(span, str) and span and span in record["narrative"]
                    for span in item["evidence_spans"])
            for item in predictions_for_case
        )
        case_results.append({
            "alert_id": record["alert_id"],
            "category": record["category"],
            "gold_technique_ids": sorted(gold),
            "predicted_technique_ids": sorted(predicted),
            "match": match,
            "grounded": grounded,
            "needs_human_review": record["needs_human_review"],
            "out_of_subset_ids": sorted(predicted - allowlist),
        })
    gates = {
        "exact_f1_at_least_0_70": metrics["exact_technique"]["f1"] >= 0.70,
        "parent_recall_at_least_0_90": metrics["parent_technique_recall"] >= 0.90,
        "grounding_at_least_0_85": metrics["evidence_grounding_rate"] >= 0.85,
        "hallucinated_id_rate_is_zero": metrics["hallucinated_id_rate"] == 0.0,
    }
    if mode == "runtime":
        gates["behavior_evidence_at_least_0_85"] = metrics["behavior_evidence_rate"] >= 0.85
    report = {
        "metadata": {
            "report_kind": "fixture_validation" if mode == "fixture" else "runtime_quality",
            "not_a_runtime_quality_gate": mode == "fixture",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "commit": _commit(),
            "code_sha256": _code_hash(),
            "dataset_version": metadata["dataset_version"],
            "dataset_sha256": _hash(dataset_path),
            "evaluation_scope": "development" if development else subset_metadata["scope"],
            "evaluated_alert_count": subset_metadata["alert_count"],
            "evaluation_subset_version": subset_metadata.get("version"),
            "evaluation_subset_sha256": subset_metadata.get("sha256"),
            "label_review_status": metadata.get("label_review_status", "unspecified"),
            "stix_version": STIX_VERSION,
            "stix_sha256": _hash(PROJECT_ROOT / "data/raw/enterprise-attack-19.1.json"),
            "allowlist_sha256": _hash(DEFAULT_ALLOWLIST),
            "candidates_sha256": _hash(PROJECT_ROOT / "data/processed/technique_candidates.json"),
            "prediction_sha256": prediction_hash,
            "model_version": model_version,
            "prompt_version": prompt_version,
            "provider_mode": "disabled",
            "category_counts": {
                category: sum(record["category"] == category for record in records)
                for category in ("positive", "multi_technique", "ambiguous", "negative")
            },
            "python_version": platform.python_version(),
            "dependency_versions": dict(sorted((d.metadata["Name"], d.version) for d in distributions())),
            "prompt_sha256": {str(p.relative_to(PROJECT_ROOT)): _hash(p) for p in sorted((PROJECT_ROOT / "prompts").rglob("*.txt"))},
            "snapshot_sha256": hashlib.sha256(json.dumps(retriever.snapshot, sort_keys=True).encode()).hexdigest() if retriever else None,
            "top_k": top_k if mode == "runtime" else None,
            "parent_match_credit": PARENT_MATCH_CREDIT,
            "grounding_kind": "exact_substring_only",
            "additional_grounding_kind": "clause_behavior_rules" if mode == "runtime" else None,
        },
        "metrics": metrics,
        "quality_gates": gates,
        "numeric_gates_passed": all(gates.values()),
        # Neither fixture nor substring-only evaluation constitutes course acceptance.
        "acceptance_ready": False,
        "acceptance_blockers": [
            "Gold-label approval and dataset composition require course confirmation.",
            "Independent semantic validation and final subset approval remain outstanding.",
        ],
        "disclaimer": DISCLAIMER,
        # Safe UI summary: no narratives or evidence text leave the evaluator.
        "case_results": case_results,
    }
    if diagnostics and mode == "runtime":
        from eval.diagnostics import analyze
        report["diagnostics"] = analyze(records, traces, retriever)
    return report
