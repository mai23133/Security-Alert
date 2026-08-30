import json
from pathlib import Path

import pytest

from eval.metrics import (
    evidence_grounding_rate,
    exact_technique_scores,
    hallucinated_id_rate,
    parent_technique_recall,
    recall_at_k,
)
from eval.run_eval import build_records, validate_dataset

ROOT = Path(__file__).resolve().parents[1]
EVAL_DIR = ROOT / "data" / "eval"


def test_metric_formulas_with_synthetic_saved_predictions():
    records = [
        {
            "narrative": "encoded PowerShell ran",
            "gold_technique_ids": ["T1059.001"],
            "inferred_techniques": [
                {"technique_id": "T1059", "evidence_spans": ["encoded PowerShell"]}
            ],
            "candidates": ["T1059.001", "T1110"],
        },
        {
            "narrative": "benign patch completed",
            "gold_technique_ids": [],
            "inferred_techniques": [],
            "candidates": [],
        },
    ]
    assert exact_technique_scores(records)["f1"] == 0.0
    assert parent_technique_recall(records) == 1.0
    assert evidence_grounding_rate(records) == 1.0
    assert hallucinated_id_rate(records, {"T1059.001"}) == 1.0
    assert recall_at_k(records, 1) == 1.0


def test_recall_at_k_rejects_non_positive_k():
    with pytest.raises(ValueError, match="at least 1"):
        recall_at_k([], 0)


def test_versioned_dataset_shape_ids_and_saved_predictions():
    dataset = json.loads((EVAL_DIR / "alerts-v1.0.json").read_text(encoding="utf-8"))
    predictions = json.loads(
        (EVAL_DIR / "saved_predictions-v1.0.json").read_text(encoding="utf-8")
    )
    allowlist = set(
        json.loads((EVAL_DIR / "technique_ids-v19.1.json").read_text(encoding="utf-8"))
    )
    validate_dataset(dataset, allowlist)
    records = build_records(dataset, predictions)
    assert len(records) == 35
    assert sum(item["category"] == "negative" for item in records) == 5
    assert sum(
        item["category"] in {"ambiguous", "multi_technique"} for item in records
    ) == 10
    for item in records:
        for prediction in item["inferred_techniques"]:
            assert 1 <= len(prediction["evidence_spans"])
