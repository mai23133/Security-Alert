"""Regressions for gold isolation, offline runtime and the evaluation API."""
import json
import socket

import pytest
from fastapi.testclient import TestClient

from eval import evaluator
from eval.run_eval import (
    DEFAULT_DATASET, DEFAULT_PREDICTIONS, build_records,
    validate_dataset, validate_predictions, main,
)
from src.api.main import app
from src.api.routes import evaluate as evaluate_route
from src.schemas import ATTACKInferenceResult, InferredTechnique


@pytest.fixture
def files():
    dataset = json.loads(DEFAULT_DATASET.read_text())
    predictions = json.loads(DEFAULT_PREDICTIONS.read_text())
    allowlist = set(json.loads(evaluator.DEFAULT_ALLOWLIST.read_text()))
    return dataset, predictions, allowlist


@pytest.mark.parametrize("field,value", [
    ("gold_technique_ids", []), ("narrative", "forged"), ("category", "negative"),
])
def test_predictions_cannot_overwrite_gold(files, field, value):
    dataset, predictions, allowlist = files
    predictions["predictions"][0][field] = value
    with pytest.raises(ValueError, match="dataset-owned"):
        validate_predictions(predictions, dataset, allowlist)
    # Even direct callers bypassing validation cannot replace gold fields.
    records = build_records(dataset, predictions)
    assert records[0][field] == dataset["alerts"][0][field]


@pytest.mark.parametrize("narrative", ["", "  ", None, 42, "x" * 20001])
def test_bad_narrative_rejected(files, narrative):
    dataset, _, allowlist = files
    dataset["alerts"][0]["narrative"] = narrative
    with pytest.raises(ValueError, match="narrative"):
        validate_dataset(dataset, allowlist)


def test_snapshot_drift_rejected(tmp_path, monkeypatch):
    path = tmp_path / "snapshot.json"
    path.write_text('["T1110"]')
    monkeypatch.setattr(evaluator, "SNAPSHOT", path)
    with pytest.raises(ValueError, match="differs"):
        evaluator.create_report(mode="fixture")


def test_dataset_version_mismatch_rejected(files, tmp_path):
    dataset, _, _ = files
    dataset["metadata"]["stix_version"] = "wrong"
    path = tmp_path / "dataset.json"
    path.write_text(json.dumps(dataset))
    with pytest.raises(ValueError, match="version"):
        evaluator.create_report(dataset_path=path)


def test_fixture_and_runtime_are_distinct_and_offline(monkeypatch):
    calls = []
    def forbidden(*args, **kwargs):
        calls.append(args)
        raise AssertionError("evaluation attempted network access")

    monkeypatch.setattr(socket.socket, "connect", forbidden)
    monkeypatch.setenv("GOOGLE_API_KEY", "test-key-must-not-be-used")
    monkeypatch.setenv("GEMINI_API_KEY", "test-key-must-not-be-used")
    fixture = evaluator.create_report(mode="fixture")
    runtime = evaluator.create_report(mode="runtime")
    repeated = evaluator.create_report(mode="runtime")
    assert fixture["metadata"]["report_kind"] == "fixture_validation"
    assert fixture["metadata"]["not_a_runtime_quality_gate"] is True
    assert runtime["metadata"]["report_kind"] == "runtime_quality"
    assert runtime["metadata"]["provider_mode"] == "disabled"
    assert runtime["metadata"]["grounding_kind"] == "exact_substring_only"
    assert runtime["metrics"]["alert_count"] == 35
    assert runtime["metrics"] == repeated["metrics"]
    assert runtime["metadata"]["prediction_sha256"] == repeated["metadata"]["prediction_sha256"]
    assert fixture["acceptance_ready"] is runtime["acceptance_ready"] is False
    assert calls == []


def test_iteration_2_release_subset_is_bounded_and_reported():
    report = evaluator.create_report(
        mode="runtime", subset_path=evaluator.ITERATION_2_SUBSET
    )
    assert report["metadata"]["evaluation_scope"] == "iteration_2_v0.2.0"
    assert report["metadata"]["evaluated_alert_count"] == 10
    assert report["metrics"]["alert_count"] == 10


def test_runtime_quality_errors_reach_metrics(monkeypatch):
    import src.inference_pipeline as pipeline

    def incorrect(**kwargs):
        return ATTACKInferenceResult(
            alert_id=kwargs["alert_id"],
            inferred_techniques=[InferredTechnique(
                technique_id="T9999", technique_name="Invalid", tactic="execution",
                confidence=0.8, evidence_spans=["invented evidence"],
                mitre_url="https://attack.mitre.org/techniques/T9999/",
            )], candidates_considered=[], needs_human_review=True,
        )
    monkeypatch.setattr(pipeline, "run_inference", incorrect)
    report = evaluator.create_report(mode="runtime")
    assert report["metrics"]["hallucinated_id_rate"] == 1
    assert report["metrics"]["evidence_grounding_rate"] == 0
    assert report["numeric_gates_passed"] is False


@pytest.mark.parametrize("payload", [
    {"dataset": "/etc/passwd"}, {"output": "/tmp/report"},
    {"mode": "online"}, {"top_k": True}, {"top_k": 0}, {"top_k": 26},
])
def test_api_rejects_paths_and_unbounded_inputs(payload):
    with TestClient(app) as client:
        assert client.post("/evaluate", json=payload).status_code == 422


def test_evaluate_api_real_report():
    with TestClient(app) as client:
        response = client.post("/evaluate", json={})
    assert response.status_code == 200
    assert response.json()["metadata"]["report_kind"] == "runtime_quality"
    assert response.json()["disclaimer"]
    assert response.headers["x-request-id"]
    assert response.headers["x-mitre-attack-version"] == "enterprise-attack-19.1"


@pytest.mark.parametrize("error, status", [(FileNotFoundError("secret"), 503), (RuntimeError("secret"), 500)])
def test_evaluate_api_errors_are_safe(monkeypatch, error, status):
    def fail(**kwargs):
        raise error
    monkeypatch.setattr(evaluate_route, "create_report", fail)
    with TestClient(app) as client:
        response = client.post("/evaluate", json={})
    assert response.status_code == status
    assert "secret" not in response.text


def test_cli_quality_gate_exit_status(monkeypatch, capsys):
    monkeypatch.setattr(evaluator, "create_report", lambda **kwargs: {"numeric_gates_passed": False})
    monkeypatch.setattr("sys.argv", ["run_eval", "--mode", "runtime", "--require-quality-gates"])
    assert main() == 1
    assert "false" in capsys.readouterr().out


def test_cli_cannot_use_fixture_as_runtime_gate(monkeypatch):
    monkeypatch.setattr("sys.argv", ["run_eval", "--require-quality-gates"])
    with pytest.raises(SystemExit) as error:
        main()
    assert error.value.code == 2
