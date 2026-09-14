"""Exercise the five specification demo steps without an external provider."""
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from fastapi.testclient import TestClient
from src.api.main import create_app
from src.agents.evidence_linker import link_evidence
from src.agents.grounding_judge import judge_result
from src.schemas import ATTACKInferenceResult


def main():
    narrative = "Host WIN-SRV-04 logged 847 failed RDP authentication attempts from IP 203.0.113.44 between 02:00–04:00 UTC, followed by a successful login and execution of encoded PowerShell."
    with TestClient(create_app(api_key="")) as client:
        response = client.post("/alerts/infer", json={"alert_id":"demo-spec", "narrative":narrative})
        response.raise_for_status()
        result = ATTACKInferenceResult.model_validate(response.json())
        assert {t.technique_id for t in result.inferred_techniques} == {"T1110", "T1059.001"}
        candidates = client.post("/rag/search", json={"narrative":narrative,"top_k":5})
        candidates.raise_for_status()
        assert len(candidates.json()["candidates"]) == 5
        benign = client.post("/alerts/infer", json={"narrative":"Routine patch management executed an approved PowerShell maintenance script."})
        benign.raise_for_status()
        assert not benign.json()["inferred_techniques"] and benign.json()["needs_human_review"]
        removed = [t.model_copy(update={"evidence_spans":[]}) for t in result.inferred_techniques]
        assert link_evidence(narrative, removed) == []
        assert judge_result(narrative, removed, result.candidates_considered)
        evaluation = client.post("/evaluate", json={})
        evaluation.raise_for_status()
        report = {"functional_demo_passed":True, "provider_mode":"disabled",
            "steps":["brute_force_and_powershell", "top_five_candidates", "benign_no_match_review", "judge_rejects_removed_evidence", "display_full_runtime_metrics"],
            "metrics":evaluation.json()["metrics"], "quality_gates_passed":evaluation.json()["numeric_gates_passed"],
            "acceptance_ready":False}
        output = ROOT / "docs/reports/demo.json"
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(report, indent=2) + "\n")
        print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
