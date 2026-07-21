"""
Ingest the pinned MITRE ATT&CK STIX 2.1 enterprise bundle and filter down
to the in-scope subset defined in spec section 3 and 7:
  - Tactics: Initial Access, Execution, Credential Access
  - Platforms: Windows, Linux
  - Exclude deprecated/revoked techniques
Week 2 deliverable.
"""
import json

from pathlib import Path
from src.schemas import TechniqueCandidate

PROJECT_ROOT = Path(__file__).resolve().parents[2]
STIX_PATH = PROJECT_ROOT / "data" / "raw" / "enterprise-attack-19.1.json"
OUTPUT_DIR = PROJECT_ROOT / "data" / "processed"

TECHNIQUE_IDS_PATH = OUTPUT_DIR / "technique_ids.json"
TECHNIQUE_CANDIDATES_PATH = OUTPUT_DIR / "technique_candidates.json"

STIX_VERSION = "19.1"


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


def main():
    objects = load_stix_objects(STIX_PATH)
    in_scope_objs = [o for o in objects if in_scope(o)]
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

    with TECHNIQUE_IDS_PATH.open("w", encoding="utf-8") as file:
        json.dump(
            sorted(ids),
            file,
            ensure_ascii=False,
            indent=2,
        )

    with TECHNIQUE_CANDIDATES_PATH.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            [candidate.model_dump() for candidate in candidates],
            file,
            ensure_ascii=False,
            indent=2,
        )

    print(f"\nWrote {TECHNIQUE_IDS_PATH}")
    print(f"Wrote {TECHNIQUE_CANDIDATES_PATH}")


if __name__ == "__main__":
    main()



