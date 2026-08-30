"""Run the reproducible offline evaluation from gold and saved JSON files."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from eval.metrics import evaluate

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATASET = PROJECT_ROOT / "data" / "eval" / "alerts-v1.0.json"
DEFAULT_PREDICTIONS = PROJECT_ROOT / "data" / "eval" / "saved_predictions-v1.0.json"
DEFAULT_ALLOWLIST = PROJECT_ROOT / "data" / "eval" / "technique_ids-v19.1.json"


def _load_json(path: Path) -> Any:
    with path.open(encoding="utf-8") as file:
        return json.load(file)


def build_records(dataset: dict[str, Any], predictions: dict[str, Any]) -> list[dict[str, Any]]:
    prediction_by_id = {item["alert_id"]: item for item in predictions["predictions"]}
    dataset_ids = {item["alert_id"] for item in dataset["alerts"]}
    if dataset_ids != set(prediction_by_id):
        missing = sorted(dataset_ids - set(prediction_by_id))
        extra = sorted(set(prediction_by_id) - dataset_ids)
        raise ValueError(f"prediction IDs do not match dataset; missing={missing}, extra={extra}")
    return [{**alert, **prediction_by_id[alert["alert_id"]]} for alert in dataset["alerts"]]


def validate_dataset(dataset: dict[str, Any], allowlist: set[str]) -> None:
    alerts = dataset["alerts"]
    categories = [item["category"] for item in alerts]
    special_count = sum(category in {"ambiguous", "multi_technique"} for category in categories)
    if len(alerts) != 35 or special_count != 10 or categories.count("negative") != 5:
        raise ValueError("dataset must contain 35 alerts, 10 ambiguous/multi-technique, and 5 negative")
    unknown = sorted(
        {technique_id for item in alerts for technique_id in item["gold_technique_ids"]} - allowlist
    )
    if unknown:
        raise ValueError(f"gold IDs outside pinned allowlist: {unknown}")


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
    records = build_records(dataset, predictions)
    metrics = evaluate(records, allowlist)
    report = {
        "metadata": {
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
