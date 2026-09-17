"""Evidence validation for ATT&CK predictions."""
from __future__ import annotations

import re
from src.agents.behavior import contextual_span_valid, clauses, safe_clause

from src.schemas import InferredTechnique


def link_evidence(
    narrative: str, inferred: list[InferredTechnique], *, require_behavior: bool = True,
) -> list[InferredTechnique]:
    """Require verbatim spans, behavior support and safe enclosing context.

    Rule validation is auditable, but not independent expert semantic review.
    """
    if not narrative:
        return []

    grounded: list[InferredTechnique] = []
    for technique in inferred:
        spans = list(
            dict.fromkeys(
                span
                for span in technique.evidence_spans
                if span and re.search(r"[A-Za-z0-9]{4,}", span)
                and (contextual_span_valid(narrative, span, technique.technique_id, technique.technique_name)
                     if require_behavior else span in clauses(narrative) and safe_clause(span))
            )
        )
        if spans:
            grounded.append(technique.model_copy(update={"evidence_spans": spans}))
    return grounded
