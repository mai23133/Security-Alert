"""Error taxonomy and confidence audit, without exporting raw alert text."""
from collections import Counter
import hashlib


def analyze(records, traces, retriever):
    rows = []
    counts = Counter()
    bins = {}
    for record in records:
        gold = set(record["gold_technique_ids"])
        predicted = {p["technique_id"] for p in record["inferred_techniques"]}
        candidates = [c["technique_id"] for c in record["candidates"]]
        trace = traces.get(record["alert_id"], {})
        by_id = {c.technique_id: c for c in retriever.candidates}
        errors = set()
        for missing in gold - predicted:
            if missing not in candidates:
                tactics = set(retriever.metadata.get(missing, {}).get("tactics", [by_id[missing].tactic]))
                routed = set(trace.get("tactics", []))
                errors.add("router_filter" if routed and not tactics & routed else "retrieval_miss")
            elif missing in trace.get("before_grounding", []):
                errors.add("grounding_rejection")
            else:
                errors.add("inference_miss")
            if any(p.split(".")[0] == missing.split(".")[0] for p in predicted):
                errors.add("parent_subtechnique_mismatch")
        if predicted - gold:
            errors.add("benign_false_positive" if record["category"] == "negative" else "extra_prediction")
        if record["category"] == "ambiguous" and not record["needs_human_review"]:
            errors.add("ambiguity_without_review")
        counts.update(errors)
        evidence = []
        for item in record["inferred_techniques"]:
            key = str(item["confidence"])
            bucket = bins.setdefault(key, {"count": 0, "correct": 0})
            bucket["count"] += 1
            bucket["correct"] += int(item["technique_id"] in gold)
            evidence.append({"technique_id": item["technique_id"], "spans": [
                {"start": record["narrative"].find(span), "length": len(span),
                 "sha256": hashlib.sha256(span.encode()).hexdigest()} for span in item["evidence_spans"]]})
        rows.append({"alert_id": record["alert_id"], "category": record["category"],
            "gold_ids": sorted(gold), "retrieved_ids": candidates, "predicted_ids": sorted(predicted),
            "needs_human_review": record["needs_human_review"], "errors": sorted(errors), "evidence": evidence,
            "stages": trace})
    for bucket in bins.values():
        bucket["empirical_precision"] = bucket["correct"] / bucket["count"]
    return {"error_counts": dict(sorted(counts.items())),
        "error_rates": {key: count / len(records) for key, count in sorted(counts.items())},
        "confidence_bins": bins, "records": rows,
        "confidence_note": "Rule scores are not calibrated probabilities; these bins audit development precision only."}
