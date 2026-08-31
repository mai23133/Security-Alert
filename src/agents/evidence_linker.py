"""Evidence validation for ATT&CK predictions."""
from __future__ import annotations

from src.schemas import InferredTechnique


def link_evidence(
    narrative: str, inferred: list[InferredTechnique]
) -> list[InferredTechnique]:
    """Keep predictions whose non-empty evidence spans occur verbatim in alert.

    Exact substring matching makes evidence independently auditable and avoids
    treating a model-generated explanation as supporting evidence.
    """
    if not narrative:
        return []

    grounded: list[InferredTechnique] = []
    for technique in inferred:
        spans = list(
            dict.fromkeys(
                span for span in technique.evidence_spans if span and span in narrative
            )
        )
        if spans:
            grounded.append(technique.model_copy(update={"evidence_spans": spans}))
    return grounded
