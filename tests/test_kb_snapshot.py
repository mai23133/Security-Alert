import json
from pathlib import Path

import pytest

from src.api.runtime import SNAPSHOT_PATH, load_knowledge_base
from src.rag import ingest_stix
from src.rag.retriever import BaselineRetriever


def test_snapshot_verifies_canonical_ids_metadata_and_version(tmp_path):
    original = json.loads(SNAPSHOT_PATH.read_text())
    for mutate in (
        lambda s: s.update(stix_sha256="wrong"),
        lambda s: s["candidates"][0].update(technique_name="forged"),
        lambda s: s["metadata"][s["technique_ids"][0]].update(platforms=["forged"]),
    ):
        snapshot = json.loads(json.dumps(original))
        mutate(snapshot)
        path = tmp_path / "snapshot.json"
        path.write_text(json.dumps(snapshot))
        with pytest.raises(ValueError):
            load_knowledge_base(path)


def test_running_retriever_keeps_snapshot_when_disk_changes(tmp_path):
    path = tmp_path / "snapshot.json"
    path.write_bytes(SNAPSHOT_PATH.read_bytes())
    retriever = load_knowledge_base(path)
    expected = retriever.search("executed PowerShell")
    path.write_text("corrupt replacement")
    assert retriever.search("executed PowerShell") == expected
    with pytest.raises(ValueError):
        load_knowledge_base(path)


def test_atomic_write_failure_preserves_previous_generation(tmp_path, monkeypatch):
    path = tmp_path / "snapshot.json"
    path.write_text('{"previous":true}')
    def fail(*args):
        raise OSError("simulated disk failure")
    monkeypatch.setattr(ingest_stix.os, "replace", fail)
    with pytest.raises(OSError):
        ingest_stix.atomic_json(path, {"new": True})
    assert json.loads(path.read_text()) == {"previous": True}
    assert not list(tmp_path.glob(".kb-*"))


def test_pending_subset_cannot_be_used_for_ingestion():
    template = Path(__file__).resolve().parents[1] / "data/subset/approval-template.json"
    with pytest.raises(ValueError, match="approval"):
        ingest_stix.main(template)


def test_filter_uses_all_tactics_and_retains_canonical_schema(tmp_path):
    snapshot = json.loads(SNAPSHOT_PATH.read_text())
    candidate = snapshot["candidates"][0]
    target = sorted(ingest_stix.IN_SCOPE_TACTICS - {candidate["tactic"]})[0]
    # Synthetic multi-tactic fixture: the actual pinned subset currently has
    # no technique with two of these three tactics, so don't assume it does.
    snapshot["metadata"][candidate["technique_id"]]["tactics"].append(target)
    path = tmp_path / "multi-tactic.json"
    path.write_text(json.dumps(snapshot))
    retriever = BaselineRetriever(path, path, snapshot_path=path)
    found = retriever.search(candidate["technique_name"], tactic=target, top_k=127)
    assert any(c.technique_id == candidate["technique_id"] and c.tactic == target for c in found)


def test_manifest_filters_all_generated_views_consistently(tmp_path, monkeypatch):
    ids = json.loads(SNAPSHOT_PATH.read_text())["technique_ids"][:30]
    manifest = tmp_path / "test-manifest.json"
    manifest.write_text(json.dumps({"status":"approved", "approved_by":"test-fixture-only",
        "approved_at":"2026-09-14", "approval_reference":"synthetic test",
        "stix_version":"enterprise-attack-19.1", "technique_ids":ids}))
    output = tmp_path / "processed"
    monkeypatch.setattr(ingest_stix, "OUTPUT_DIR", output)
    monkeypatch.setattr(ingest_stix, "TECHNIQUE_IDS_PATH", output / "technique_ids.json")
    monkeypatch.setattr(ingest_stix, "TECHNIQUE_CANDIDATES_PATH", output / "technique_candidates.json")
    ingest_stix.main(manifest)
    snapshot = json.loads((output / "kb_snapshot.json").read_text())
    assert snapshot["technique_ids"] == ids
    assert set(snapshot["metadata"]) == set(ids)
    assert {c["technique_id"] for c in snapshot["candidates"]} == set(ids)
    assert snapshot["subset_status"] == "approved"
