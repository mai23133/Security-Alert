"""Deterministic, candidate-bounded ATT&CK technique inference.

This module deliberately does not call an LLM.  It provides a safe baseline
for the pipeline: only candidates supplied by the retriever can be returned,
and an alert that has insufficient lexical support becomes a no-match.
"""
from __future__ import annotations

import re

from src.schemas import InferredTechnique, TechniqueCandidate


_TOKEN_RE = re.compile(r"[a-z0-9]+")
_STOP_WORDS = {
    "about", "after", "against", "and", "are", "been", "between", "by",
    "for", "from", "has", "have", "into", "its", "may", "not", "of",
    "on", "or", "that", "the", "their", "this", "to", "use", "was",
    "with",
}


def _tokens(value: str) -> set[str]:
    return {
        token for token in _TOKEN_RE.findall(value.lower())
        if len(token) >= 4 and token not in _STOP_WORDS
    }


def _mitre_url(technique_id: str) -> str:
    """Return the canonical MITRE technique page for an allowlisted ID."""
    return "https://attack.mitre.org/techniques/" + technique_id.replace(".", "/") + "/"


def _evidence_sentences(narrative: str, terms: set[str]) -> list[str]:
    """Return complete alert sentences that contain a candidate-specific term."""
    sentences = re.split(r"(?<=[.!?])\s+", narrative.strip())
    return [sentence for sentence in sentences if _tokens(sentence) & terms]


def infer_techniques(
    narrative: str,
    candidates: list[TechniqueCandidate],
    *,
    max_results: int = 3,
) -> list[InferredTechnique]:
    """Infer at most ``max_results`` techniques from retriever candidates.

    A candidate needs at least two overlapping meaningful terms between its
    name/description and the untrusted alert narrative.  This conservative
    threshold keeps the baseline from manufacturing a technique for generic
    alerts.  Ties are sorted by technique ID so results are reproducible.
    """
    if not narrative.strip() or not candidates or not 1 <= max_results <= 3:
        return []

    alert_tokens = _tokens(narrative)
    ranked: list[tuple[float, TechniqueCandidate, list[str]]] = []
    for candidate in candidates:
        candidate_terms = _tokens(
            f"{candidate.technique_name} {candidate.description_excerpt}"
        )
        matched_terms = candidate_terms & alert_tokens
        if len(matched_terms) < 2:
            continue
        spans = _evidence_sentences(narrative, matched_terms)
        if not spans:
            continue
        # Candidate-name matches are stronger than description-only matches.
        name_matches = _tokens(candidate.technique_name) & alert_tokens
        score = min(0.90, 0.45 + 0.10 * len(matched_terms) + 0.10 * len(name_matches))
        ranked.append((score, candidate, spans))

    ranked.sort(key=lambda item: (-item[0], item[1].technique_id))
    return [
        InferredTechnique(
            technique_id=candidate.technique_id,
            technique_name=candidate.technique_name,
            tactic=candidate.tactic,
            confidence=score,
            evidence_spans=spans,
            mitre_url=_mitre_url(candidate.technique_id),
        )
        for score, candidate, spans in ranked[:max_results]
    ]
