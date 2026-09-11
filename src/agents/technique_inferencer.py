"""Deterministic, candidate-bounded ATT&CK technique inference.

This module deliberately does not call an LLM.  It provides a safe baseline
for the pipeline: only candidates supplied by the retriever can be returned,
and an alert that has insufficient lexical support becomes a no-match.
"""
from __future__ import annotations

import json
import re
from collections.abc import Callable

from pydantic import BaseModel, Field

from src.agents.gemini_client import generate_text
from src.schemas import InferredTechnique, TechniqueCandidate


class ProviderTechnique(BaseModel):
    technique_id: str
    confidence: float = Field(ge=0.0, le=1.0)
    evidence_spans: list[str] = Field(min_length=1)


class ProviderInference(BaseModel):
    techniques: list[ProviderTechnique] = Field(max_length=3)


TextGenerator = Callable[[str], str]


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
    seen_candidate_ids: set[str] = set()
    for candidate in candidates:
        # A retriever should not duplicate candidates, but B must not emit
        # duplicate predictions even when it receives malformed input.
        if candidate.technique_id in seen_candidate_ids:
            continue
        seen_candidate_ids.add(candidate.technique_id)
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


def infer_techniques_with_provider(
    narrative: str,
    candidates: list[TechniqueCandidate],
    *,
    generate: TextGenerator = generate_text,
) -> list[InferredTechnique]:
    """Use an LLM for candidate selection, with a deterministic safe fallback."""
    if not candidates:
        return []
    candidate_payload = [candidate.model_dump() for candidate in candidates]
    alert_payload = json.dumps({"narrative": narrative}).replace("<", "\\u003c")
    prompt = (
        "Select zero to three MITRE ATT&CK techniques supported by the alert. "
        "Return only JSON as {\"techniques\":[{\"technique_id\":\"T####\","
        "\"confidence\":0.0,\"evidence_spans\":[\"exact quote from alert\"]}]}. "
        "IDs must come from candidates and every evidence span must be an exact alert substring.\n"
        f"<candidates>{json.dumps(candidate_payload)}</candidates>\n"
        f"<untrusted_alert>{alert_payload}</untrusted_alert>"
    )
    try:
        raw = generate(prompt).strip()
        if raw.startswith("```") and raw.endswith("```"):
            raw = raw[3:-3].strip()
            if raw.startswith("json"):
                raw = raw[4:].strip()
        response = ProviderInference.model_validate_json(raw)
        candidate_by_id = {candidate.technique_id: candidate for candidate in candidates}
        seen: set[str] = set()
        inferred: list[InferredTechnique] = []
        for item in response.techniques:
            candidate = candidate_by_id.get(item.technique_id)
            if candidate is None or item.technique_id in seen:
                continue
            spans = list(dict.fromkeys(
                span for span in item.evidence_spans
                if len(span.strip()) >= 4 and span in narrative
            ))
            if not spans:
                continue
            seen.add(item.technique_id)
            inferred.append(InferredTechnique(
                technique_id=candidate.technique_id,
                technique_name=candidate.technique_name,
                tactic=candidate.tactic,
                confidence=item.confidence,
                evidence_spans=spans,
                mitre_url=_mitre_url(candidate.technique_id),
            ))
        return inferred
    except Exception:
        return infer_techniques(narrative, candidates)
