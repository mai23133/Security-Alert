"""
Ingest the pinned MITRE ATT&CK STIX 2.1 enterprise bundle and filter down
to the in-scope subset defined in spec section 3 and 7:
  - Tactics: Initial Access, Execution, Credential Access
  - Platforms: Windows, Linux
  - Exclude deprecated/revoked techniques
Week 2 deliverable.
"""
import json
import argparse
import hashlib
import os
import tempfile

from pathlib import Path
from src.schemas import TechniqueCandidate

PROJECT_ROOT = Path(__file__).resolve().parents[2]
STIX_PATH = PROJECT_ROOT / "data" / "raw" / "enterprise-attack-19.1.json"
OUTPUT_DIR = PROJECT_ROOT / "data" / "processed"

TECHNIQUE_IDS_PATH = OUTPUT_DIR / "technique_ids.json"
TECHNIQUE_CANDIDATES_PATH = OUTPUT_DIR / "technique_candidates.json"

STIX_VERSION = "19.1"
PINNED_STIX_SHA256 = "bdf1ce86a4e604214c5076d37ae4dcb322678afc528df8492e6fdc1b554f5da3"


IN_SCOPE_TACTICS = {"initial-access", "execution", "credential-access"}
IN_SCOPE_PLATFORMS = {"Windows", "Linux"}


def load_stix_objects(path: str) -> list[dict]:
    with open(path) as f:
        return json.load(f)["objects"]


def external_id(obj: dict) -> str | None:
    for ref in obj.get("external_references", []):
        if ref.get("source_name") == "mitre-attack":
            return ref.get("external_id")
    return None


def in_scope(obj: dict) -> bool:
    if obj["type"] != "attack-pattern":
        return False
    if obj.get("x_mitre_deprecated", False) or obj.get("revoked", False):
        return False
    tactics = {p["phase_name"] for p in obj.get("kill_chain_phases", [])}
    if not tactics & IN_SCOPE_TACTICS:
        return False
    platforms = set(obj.get("x_mitre_platforms", []))
    if not platforms & IN_SCOPE_PLATFORMS:
        return False
    if not external_id(obj):
        return False
    return True


def to_candidate(obj: dict) -> TechniqueCandidate:
    tactics = {p["phase_name"] for p in obj.get("kill_chain_phases", [])}
    # an object can map to >1 in-scope tactic; pick the first in-scope match
    tactic = sorted(tactics & IN_SCOPE_TACTICS)[0]
    return TechniqueCandidate(
        technique_id=external_id(obj),
        technique_name=obj["name"],
        tactic=tactic,
        description_excerpt=obj["description"][:300],
        stix_version=STIX_VERSION,
    )


def atomic_json(path: Path, value: object) -> None:
    """Publish a complete JSON file with one atomic replace on the same volume."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=".kb-", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as file:
            json.dump(value, file, ensure_ascii=False, indent=2)
            file.write("\n")
            file.flush()
            os.fsync(file.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def metadata_for(obj: dict) -> dict:
    return {
        "tactics": sorted({p["phase_name"] for p in obj.get("kill_chain_phases", [])}),
        "platforms": sorted(obj.get("x_mitre_platforms", [])),
        "stix_object_id": obj.get("id"),
        "external_references": obj.get("external_references", []),
        "description": obj.get("description", ""),
        "source": "MITRE ATT&CK Enterprise STIX 2.1",
    }


def main(manifest_path: Path | None = None):
    if Path(STIX_PATH) == PROJECT_ROOT / "data/raw/enterprise-attack-19.1.json":
        if hashlib.sha256(Path(STIX_PATH).read_bytes()).hexdigest() != PINNED_STIX_SHA256:
            raise ValueError("Pinned STIX source checksum mismatch")
    objects = load_stix_objects(STIX_PATH)
    in_scope_objs = [o for o in objects if in_scope(o)]
    manifest = None
    if manifest_path is not None:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        ids = manifest.get("technique_ids")
        if (manifest.get("status") != "approved" or not manifest.get("approved_by")
            or not manifest.get("approved_at") or not manifest.get("approval_reference")
            or manifest.get("stix_version") != "enterprise-attack-19.1"
            or not isinstance(ids, list) or any(not isinstance(i, str) for i in ids)
            or len(ids) != len(set(ids)) or not 30 <= len(ids) <= 50):
            raise ValueError("Manifest requires documented approval and 30-50 unique pinned IDs")
        if not set(ids) <= {external_id(o) for o in in_scope_objs}:
            raise ValueError("Manifest contains IDs outside the pinned in-scope taxonomy")
        in_scope_objs = [o for o in in_scope_objs if external_id(o) in set(ids)]
    candidates = [to_candidate(o) for o in in_scope_objs]

    print(f"Total STIX objects: {len(objects)}")
    print(
        "In-scope techniques "
        f"(3 tactics, Win/Linux, non-deprecated/revoked): {len(candidates)}"
    )

    by_tactic = {}

    for candidate in candidates:
        by_tactic.setdefault(candidate.tactic, []).append(
            candidate.technique_id
        )

    for tactic, technique_ids in sorted(by_tactic.items()):
        print(f"  {tactic}: {len(technique_ids)} techniques")

    ids = {candidate.technique_id for candidate in candidates}

    for expected in ["T1110", "T1059.001"]:
        print(f"  {expected} present: {expected in ids}")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    rows = [candidate.model_dump() for candidate in candidates]
    metadata = {external_id(o): metadata_for(o) for o in in_scope_objs}
    atomic_json(TECHNIQUE_IDS_PATH, sorted(ids))
    atomic_json(TECHNIQUE_CANDIDATES_PATH, rows)
    atomic_json(OUTPUT_DIR / "technique_metadata.json", metadata)
    # Runtime reads this single file, never a mix of compatibility exports.
    # Publishing it last commits the new generation. Running servers keep
    # their startup snapshot until restart.
    atomic_json(OUTPUT_DIR / "kb_snapshot.json", {
        "stix_version": "enterprise-attack-19.1",
        "stix_sha256": hashlib.sha256(Path(STIX_PATH).read_bytes()).hexdigest(),
        "subset_status": "approved" if manifest else "provisional_full_in_scope",
        "manifest_sha256": hashlib.sha256(manifest_path.read_bytes()).hexdigest() if manifest else None,
        "technique_ids": sorted(ids), "candidates": rows, "metadata": metadata,
    })

    print(f"\nWrote {TECHNIQUE_IDS_PATH}")
    print(f"Wrote {TECHNIQUE_CANDIDATES_PATH}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path)
    main(parser.parse_args().manifest)
