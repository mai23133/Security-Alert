"""Candidate-bounded inference with clause-level behavior evidence."""
from src.agents.behavior import evidence, support
from src.schemas import InferredTechnique, TechniqueCandidate


def infer_techniques(narrative: str, candidates: list[TechniqueCandidate], *, max_results: int = 3) -> list[InferredTechnique]:
    if not narrative.strip() or not 1 <= max_results <= 3:
        return []
    ranked = []
    seen = set()
    for candidate in candidates:
        if candidate.technique_id in seen:
            continue
        seen.add(candidate.technique_id)
        spans = evidence(narrative, candidate.technique_id, candidate.technique_name)
        if spans:
            score = min(support(candidate.technique_id, span, candidate.technique_name) for span in spans)
            ranked.append(InferredTechnique(
                technique_id=candidate.technique_id, technique_name=candidate.technique_name,
                tactic=candidate.tactic, confidence=score, evidence_spans=spans,
                mitre_url="https://attack.mitre.org/techniques/" + candidate.technique_id.replace(".", "/") + "/",
            ))
    # Prefer supported sub-techniques over redundant parent predictions.
    ranked = [item for item in ranked if not any(
        other.technique_id.startswith(item.technique_id + ".")
        and set(other.evidence_spans) & set(item.evidence_spans) for other in ranked
    )]
    ranked.sort(key=lambda item: (-item.confidence, item.technique_id))
    return ranked[:max_results]
