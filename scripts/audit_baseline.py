"""Audit an isolated baseline checkout without exporting its narratives."""
import argparse
import importlib.util
import json
from pathlib import Path
import sys


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    diagnostics_path = Path(__file__).resolve().parents[1] / "eval/diagnostics.py"
    spec = importlib.util.spec_from_file_location("completion_diagnostics", diagnostics_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    sys.path.insert(0, str(args.root.resolve()))
    from src.inference_pipeline import run_inference
    from src.agents.technique_inferencer import infer_techniques
    from src.rag.retriever import BaselineRetriever
    from eval.metrics import evaluate

    dataset = json.loads((args.root / "data/eval/alerts-v1.0.json").read_text())
    retriever = BaselineRetriever(args.root / "data/processed/technique_candidates.json",
                                  args.root / "data/processed/technique_ids.json")
    retriever.metadata = {}
    records, traces = [], {}
    for alert in dataset["alerts"]:
        result = run_inference(alert_id=alert["alert_id"], narrative=alert["narrative"], retriever=retriever, use_provider=False)
        records.append({**alert, "inferred_techniques":[t.model_dump() for t in result.inferred_techniques],
            "candidates":[c.model_dump() for c in result.candidates_considered], "needs_human_review":result.needs_human_review})
        traces[alert["alert_id"]] = {"tactics":["initial-access","execution","credential-access"],
            "before_grounding":[t.technique_id for t in infer_techniques(alert["narrative"], result.candidates_considered)],
            "after_grounding":[t.technique_id for t in result.inferred_techniques]}
    report = {"source":"baseline checkout supplied by --root", "provider_mode":"disabled",
        "metrics": evaluate(records, retriever.allowlist_ids),
        "diagnostics": module.analyze(records, traces, retriever)}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"metrics":report["metrics"], "error_counts":report["diagnostics"]["error_counts"]}, indent=2))


if __name__ == "__main__":
    main()
