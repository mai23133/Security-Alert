"""Collect reproducible release evidence, preserving outstanding blockers."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from eval.evaluator import _code_hash


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    report_dir = ROOT / "docs/reports"
    report = json.loads((report_dir / "runtime-final.json").read_text())
    if report["metadata"]["code_sha256"] != _code_hash():
        raise RuntimeError("Runtime report is stale; regenerate it before collecting release evidence")
    suite = ET.parse(report_dir / "tests.xml").getroot()[0]
    tests = {key:int(suite.attrib[key]) for key in ("tests", "failures", "errors", "skipped")}
    paths = [p for directory in ("src", "eval", "prompts", "ui", "tests", "scripts", "data/dev", "data/eval", "data/subset")
             for p in (ROOT / directory).rglob("*") if p.is_file() and "__pycache__" not in p.parts]
    paths += [ROOT / "requirements.lock", ROOT / "security-alert-attack-technique-inference.md",
              ROOT / "data/raw/enterprise-attack-19.1.json"]
    files = {str(p.relative_to(ROOT)):sha(p) for p in sorted(paths)}
    snapshot = json.loads((ROOT / "data/processed/kb_snapshot.json").read_text())
    result = {"base_commit":subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "source_kind":"uncommitted_working_tree", "code_sha256":_code_hash(),
        "files_sha256":files, "test_summary":tests,
        "stix_version":report["metadata"]["stix_version"],
        "subset_status":snapshot["subset_status"], "subset_count":len(snapshot["technique_ids"]),
        "approved_manifest_sha256":snapshot.get("manifest_sha256"),
        "dataset_version":report["metadata"]["dataset_version"],
        "label_review_status":report["metadata"]["label_review_status"],
        "model_version":report["metadata"]["model_version"],
        "numeric_gates_passed":report["numeric_gates_passed"], "acceptance_ready":False,
        "blockers":report["acceptance_blockers"] + [key for key, passed in report["quality_gates"].items() if not passed],
        "evidence_sha256":{p.name:sha(p) for p in sorted(report_dir.glob("*"))
            if p.is_file() and p.name != "release-manifest.json"}}
    (report_dir / "release-manifest.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"test_summary":tests, "numeric_gates_passed":result["numeric_gates_passed"],
                      "acceptance_ready":False, "blockers":result["blockers"]}, indent=2))


if __name__ == "__main__":
    main()
