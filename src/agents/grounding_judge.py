"""Guardrails that decide when an inference must be reviewed by a human."""
from __future__ import annotations

from src.agents.evidence_linker import link_evidence
from src.schemas import InferredTechnique, TechniqueCandidate


LOW_CONFIDENCE_THRESHOLD = 0.65


def judge_result(
    narrative: str,
    inferred: list[InferredTechnique],
    candidates: list[TechniqueCandidate],
    *,
    low_confidence_threshold: float = LOW_CONFIDENCE_THRESHOLD,
) -> bool:
    """Return whether the result requires human review.

    Review is mandatory for no-match, more than three predictions, any ID or
    tactic/name mismatch with retriever candidates, missing exact evidence, or
    low confidence.  Callers should discard ungrounded predictions before
    exposing them; this boolean is the final conservative review signal.
    """
    if not 0.0 <= low_confidence_threshold <= 1.0:
        raise ValueError("low_confidence_threshold must be in [0, 1]")
    if not inferred or len(inferred) > 3:
        return True

    candidate_by_id = {candidate.technique_id: candidate for candidate in candidates}
    grounded_ids = {item.technique_id for item in link_evidence(narrative, inferred)}
    seen_ids: set[str] = set()
    for technique in inferred:
        candidate = candidate_by_id.get(technique.technique_id)
        if (
            candidate is None
            or technique.technique_id in seen_ids
            or technique.technique_name != candidate.technique_name
            or technique.tactic != candidate.tactic
            or technique.technique_id not in grounded_ids
            or technique.confidence < low_confidence_threshold
        ):
            return True
        seen_ids.add(technique.technique_id)
    return False
