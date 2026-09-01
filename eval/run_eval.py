"""Run the reproducible offline evaluation from gold and saved JSON files."""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any

from eval.metrics import evaluate

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATASET = PROJECT_ROOT / "data" / "eval" / "alerts-v1.0.json"
DEFAULT_PREDICTIONS = PROJECT_ROOT / "data" / "eval" / "saved_predictions-v1.0.json"
DEFAULT_ALLOWLIST = PROJECT_ROOT / "data" / "eval" / "technique_ids-v19.1.json"
ALLOWED_CATEGORIES = {"positive", "multi_technique", "ambiguous", "negative"}
CATEGORY_COUNTS = {
    "positive": 20,
    "multi_technique": 5,
    "ambiguous": 5,
    "negative": 5,
}
TECHNIQUE_ID_PATTERN = re.compile(r"^T\d{4}(?:\.\d{3})?$")


def _load_json(path: Path) -> Any:
    with path.open(encoding="utf-8") as file:
        return json.load(file)


def build_records(dataset: dict[str, Any], predictions: dict[str, Any]) -> list[dict[str, Any]]:
    alerts = dataset.get("alerts")
    saved_predictions = predictions.get("predictions")
    if not isinstance(alerts, list) or not isinstance(saved_predictions, list):
        raise ValueError("dataset alerts and saved predictions must be lists")

    dataset_alert_ids = [item.get("alert_id") for item in alerts if isinstance(item, dict)]
    prediction_alert_ids = [
        item.get("alert_id") for item in saved_predictions if isinstance(item, dict)
    ]
    _require_unique_ids(dataset_alert_ids, "dataset")
    _require_unique_ids(prediction_alert_ids, "saved predictions")

    prediction_by_id = {item["alert_id"]: item for item in saved_predictions}
    dataset_ids = set(dataset_alert_ids)
    if dataset_ids != set(prediction_by_id):
        missing = sorted(dataset_ids - set(prediction_by_id))
        extra = sorted(set(prediction_by_id) - dataset_ids)
        raise ValueError(f"prediction IDs do not match dataset; missing={missing}, extra={extra}")
    return [{**alert, **prediction_by_id[alert["alert_id"]]} for alert in alerts]


def _require_unique_ids(alert_ids: list[object], source: str) -> None:
    invalid = [alert_id for alert_id in alert_ids if not isinstance(alert_id, str) or not alert_id]
    if invalid:
        raise ValueError(f"{source} contains a missing or invalid alert_id")
    duplicates = sorted(
        alert_id for alert_id, count in Counter(alert_ids).items() if count > 1
    )
    if duplicates:
        raise ValueError(f"duplicate alert_id in {source}: {duplicates}")


def _validate_technique_ids(ids: object, allowlist: set[str], context: str) -> list[str]:
    if not isinstance(ids, list) or any(not isinstance(item, str) for item in ids):
        raise ValueError(f"{context} technique IDs must be a list of strings")
    if len(ids) != len(set(ids)):
        raise ValueError(f"duplicate technique ID in {context}")
    malformed = sorted(item for item in ids if not TECHNIQUE_ID_PATTERN.fullmatch(item))
    if malformed:
        raise ValueError(f"malformed technique IDs in {context}: {malformed}")
    unknown = sorted(set(ids) - allowlist)
    if unknown:
        raise ValueError(f"technique IDs outside pinned allowlist in {context}: {unknown}")
    return ids


def validate_dataset(dataset: dict[str, Any], allowlist: set[str]) -> None:
    alerts = dataset.get("alerts")
    if not isinstance(alerts, list):
        raise ValueError("dataset alerts must be a list")
    if any(not isinstance(item, dict) for item in alerts):
        raise ValueError("every dataset alert must be an object")
    _require_unique_ids([item.get("alert_id") for item in alerts], "dataset")

    categories = [item.get("category") for item in alerts]
    invalid_categories = sorted(
        {str(category) for category in categories if category not in ALLOWED_CATEGORIES}
    )
    if invalid_categories:
        raise ValueError(f"invalid dataset categories: {invalid_categories}")
    counts = Counter(categories)
    if len(alerts) != 35 or any(counts[name] != count for name, count in CATEGORY_COUNTS.items()):
        raise ValueError(
            "dataset must contain 20 positive, 5 multi_technique, "
            "5 ambiguous, and 5 negative alerts"
        )

    for item in alerts:
        alert_id = item["alert_id"]
        category = item["category"]
        gold_ids = _validate_technique_ids(
            item.get("gold_technique_ids"), allowlist, f"dataset alert {alert_id}"
        )
        if category == "negative" and gold_ids:
            raise ValueError(f"negative alert {alert_id} must have no gold technique IDs")
        if category != "negative" and not 1 <= len(gold_ids) <= 3:
            raise ValueError(f"{category} alert {alert_id} must have 1-3 gold technique IDs")


def validate_predictions(
    predictions: dict[str, Any], dataset: dict[str, Any], allowlist: set[str]
) -> None:
    saved_predictions = predictions.get("predictions")
    alerts = dataset.get("alerts")
    if not isinstance(saved_predictions, list) or not isinstance(alerts, list):
        raise ValueError("dataset alerts and saved predictions must be lists")
    if any(not isinstance(item, dict) for item in saved_predictions):
        raise ValueError("every saved prediction must be an object")

    prediction_ids = [item.get("alert_id") for item in saved_predictions]
    _require_unique_ids(prediction_ids, "saved predictions")
    dataset_ids = {item.get("alert_id") for item in alerts if isinstance(item, dict)}
    if len(saved_predictions) != len(alerts) or set(prediction_ids) != dataset_ids:
        missing = sorted(dataset_ids - set(prediction_ids))
        extra = sorted(set(prediction_ids) - dataset_ids)
        raise ValueError(f"prediction IDs do not match dataset; missing={missing}, extra={extra}")

    narrative_by_id = {item["alert_id"]: item.get("narrative", "") for item in alerts}
    for item in saved_predictions:
        alert_id = item["alert_id"]
        inferred = item.get("inferred_techniques")
        candidates = item.get("candidates")
        if not isinstance(inferred, list) or len(inferred) > 3:
            raise ValueError(f"prediction {alert_id} must contain 0-3 inferred techniques")
        if any(not isinstance(prediction, dict) for prediction in inferred):
            raise ValueError(f"inferred techniques for {alert_id} must be objects")
        inferred_ids = _validate_technique_ids(
            [prediction.get("technique_id") for prediction in inferred],
            allowlist,
            f"prediction {alert_id}",
        )
        candidate_ids = _validate_technique_ids(
            [candidate.get("technique_id") if isinstance(candidate, dict) else candidate
             for candidate in candidates] if isinstance(candidates, list) else candidates,
            allowlist,
            f"candidates for {alert_id}",
        )
        if not set(inferred_ids).issubset(candidate_ids):
            raise ValueError(f"prediction IDs for {alert_id} must come from its candidates")
        narrative = narrative_by_id[alert_id]
        for prediction in inferred:
            spans = prediction.get("evidence_spans")
            if not isinstance(spans, list) or not spans or any(
                not isinstance(span, str) or not span or span not in narrative for span in spans
            ):
                raise ValueError(f"prediction {alert_id} has invalid evidence spans")
        if not isinstance(item.get("needs_human_review"), bool):
            raise ValueError(f"prediction {alert_id} needs_human_review must be boolean")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, default=DEFAULT_DATASET)
    parser.add_argument("--predictions", type=Path, default=DEFAULT_PREDICTIONS)
    parser.add_argument("--allowlist", type=Path, default=DEFAULT_ALLOWLIST)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    dataset = _load_json(args.dataset)
    predictions = _load_json(args.predictions)
    allowlist = set(_load_json(args.allowlist))
    validate_dataset(dataset, allowlist)
    validate_predictions(predictions, dataset, allowlist)
    records = build_records(dataset, predictions)
    metrics = evaluate(records, allowlist)
    report = {
        "metadata": {
            "report_kind": "fixture_validation",
            "not_a_runtime_quality_gate": True,
            "dataset_version": dataset["metadata"]["dataset_version"],
            "stix_version": dataset["metadata"]["stix_version"],
            "prediction_fixture_version": predictions["metadata"]["fixture_version"],
            "model_version": predictions["metadata"]["model_version"],
            "prompt_version": predictions["metadata"]["prompt_version"],
        },
        "metrics": metrics,
        "quality_gates": {
            "exact_f1_at_least_0_70": metrics["exact_technique"]["f1"] >= 0.70,
            "parent_recall_at_least_0_90": metrics["parent_technique_recall"] >= 0.90,
            "grounding_at_least_0_85": metrics["evidence_grounding_rate"] >= 0.85,
            "hallucinated_id_rate_is_zero": metrics["hallucinated_id_rate"] == 0.0,
        },
    }
    rendered = json.dumps(report, ensure_ascii=False, indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered + "\n", encoding="utf-8")
    print(rendered)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
