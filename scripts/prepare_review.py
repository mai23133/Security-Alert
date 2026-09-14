"""Prepare an unapproved review worksheet; never mark course labels reviewed."""
from collections import Counter
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    source = ROOT / "data/eval/alerts-v1.0.json"
    dataset = json.loads(source.read_text())
    ids = set(json.loads((ROOT / "data/processed/technique_ids.json").read_text()))
    report = {"status":"pending_instructor_and_independent_review", "reviewer":None, "reviewed_at":None,
        "dataset_sha256":hashlib.sha256(source.read_bytes()).hexdigest(),
        "composition":dict(Counter(a["category"] for a in dataset["alerts"])),
        "records":[{"alert_id":a["alert_id"], "narrative_sha256":hashlib.sha256(a["narrative"].encode()).hexdigest(),
            "gold_ids":a["gold_technique_ids"], "ids_in_provisional_subset":set(a["gold_technique_ids"]) <= ids,
            "label_mapping_approved":None, "review_notes":None} for a in dataset["alerts"]]}
    output = ROOT / "docs/reports/review-checklist.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2) + "\n")
    print(f"Prepared {len(report['records'])} pending review records; no labels approved.")


if __name__ == "__main__":
    main()
