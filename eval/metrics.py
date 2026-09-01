"""Deterministic, provider-independent metrics for saved ATT&CK predictions."""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence

PARENT_MATCH_CREDIT = 0.5


def _ids(items: Iterable[object]) -> set[str]:
    result: set[str] = set()
    for item in items:
        if isinstance(item, str):
            result.add(item)
        elif isinstance(item, Mapping) and isinstance(item.get("technique_id"), str):
            result.add(item["technique_id"])
    return result


def _safe_div(numerator: int | float, denominator: int | float) -> float:
    return float(numerator / denominator) if denominator else 0.0


def exact_technique_scores(records: Sequence[Mapping[str, object]]) -> dict[str, float]:
    """Return micro precision/recall/F1 for exact multi-label technique IDs."""
    true_positive = false_positive = false_negative = 0
    for record in records:
        gold = _ids(record.get("gold_technique_ids", []))
        predicted = _ids(record.get("inferred_techniques", []))
        true_positive += len(gold & predicted)
        false_positive += len(predicted - gold)
        false_negative += len(gold - predicted)

    precision = _safe_div(true_positive, true_positive + false_positive)
    recall = _safe_div(true_positive, true_positive + false_negative)
    f1 = _safe_div(2 * precision * recall, precision + recall)
    return {"precision": precision, "recall": recall, "f1": f1}


def parent_technique_recall(records: Sequence[Mapping[str, object]]) -> float:
    """Return recall with 1.0 for exact and 0.5 for parent-only matches.

    The partial-credit weight is intentionally explicit and versioned with the
    evaluation code so reports remain reproducible.
    """
    credit = 0.0
    total = 0
    for record in records:
        predicted = _ids(record.get("inferred_techniques", []))
        for gold_id in _ids(record.get("gold_technique_ids", [])):
            total += 1
            parent_id = gold_id.split(".", 1)[0]
            if gold_id in predicted:
                credit += 1.0
            elif "." in gold_id and parent_id in predicted:
                credit += PARENT_MATCH_CREDIT
    return _safe_div(credit, total)


def evidence_grounding_rate(records: Sequence[Mapping[str, object]]) -> float:
    """Measure predictions whose non-empty evidence spans all occur verbatim."""
    grounded = total = 0
    for record in records:
        narrative = str(record.get("narrative", ""))
        for prediction in record.get("inferred_techniques", []):
            if not isinstance(prediction, Mapping):
                continue
            total += 1
            spans = prediction.get("evidence_spans", [])
            valid_spans = (
                isinstance(spans, list)
                and bool(spans)
                and all(isinstance(span, str) and span and span in narrative for span in spans)
            )
            grounded += valid_spans
    return _safe_div(grounded, total)


def hallucinated_id_rate(
    records: Sequence[Mapping[str, object]], allowlist: set[str]
) -> float:
    predicted_ids = [
        technique_id
        for record in records
        for technique_id in _ids(record.get("inferred_techniques", []))
    ]
    return _safe_div(
        sum(technique_id not in allowlist for technique_id in predicted_ids),
        len(predicted_ids),
    )


def false_positive_rate(records: Sequence[Mapping[str, object]]) -> float:
    negatives = [record for record in records if record.get("category") == "negative"]
    false_positives = sum(bool(_ids(record.get("inferred_techniques", []))) for record in negatives)
    return _safe_div(false_positives, len(negatives))


def human_review_rate(records: Sequence[Mapping[str, object]]) -> float:
    return _safe_div(
        sum(bool(record.get("needs_human_review")) for record in records),
        len(records),
    )


def recall_at_k(records: Sequence[Mapping[str, object]], k: int) -> float:
    """Return micro gold-label recall among the first k saved candidates."""
    if k < 1:
        raise ValueError("k must be at least 1")
    hits = total = 0
    for record in records:
        gold = _ids(record.get("gold_technique_ids", []))
        candidates = list(record.get("candidates", []))[:k]
        candidate_ids = _ids(candidates)
        hits += len(gold & candidate_ids)
        total += len(gold)
    return _safe_div(hits, total)


def evaluate(records: Sequence[Mapping[str, object]], allowlist: set[str]) -> dict[str, object]:
    exact = exact_technique_scores(records)
    return {
        "alert_count": len(records),
        "exact_technique": exact,
        "parent_technique_recall": parent_technique_recall(records),
        "evidence_grounding_rate": evidence_grounding_rate(records),
        "hallucinated_id_rate": hallucinated_id_rate(records, allowlist),
        "false_positive_rate": false_positive_rate(records),
        "human_review_rate": human_review_rate(records),
        "recall_at_1": recall_at_k(records, 1),
        "recall_at_3": recall_at_k(records, 3),
        "recall_at_5": recall_at_k(records, 5),
    }
