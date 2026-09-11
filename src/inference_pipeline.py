"""Deterministic orchestration of the in-scope ATT&CK inference agents."""
from __future__ import annotations

from collections.abc import Callable

from src.agents.alert_parser import parse_alert
from src.agents.evidence_linker import link_evidence
from src.agents.grounding_judge import judge_result
from src.agents.tactic_router import route_tactics
from src.agents.tactic_specialists import retrieve_with_specialists
from src.agents.technique_inferencer import infer_techniques, infer_techniques_with_provider
from src.rag.retriever import BaselineRetriever
from src.schemas import ATTACKInferenceResult


def run_inference(
    *, alert_id: str, narrative: str, retriever: BaselineRetriever, top_k: int = 5,
    use_provider: bool = True,
    provider_generate: Callable[[str], str] | None = None,
) -> ATTACKInferenceResult:
    """Run parser → router → retriever → inference → grounding.

    Parser and router failures deliberately fall back to the original narrative
    and all in-scope tactics, so the endpoint remains deterministic and does
    not require Gemini credentials to operate safely.
    """
    if use_provider:
        parsed = (
            parse_alert(narrative, generate=provider_generate)
            if provider_generate else parse_alert(narrative)
        )
        tactics = (
            route_tactics(parsed, generate=provider_generate)
            if provider_generate else route_tactics(parsed)
        )
    else:
        # Explicit offline evaluation, regardless of .env or process keys.
        def offline_generate(_prompt: str) -> str:
            raise RuntimeError("Provider disabled for offline evaluation")

        parsed = parse_alert(narrative, generate=offline_generate)
        tactics = route_tactics(parsed, generate=offline_generate)
    candidates = retrieve_with_specialists(
        parsed.narrative, tactics, retriever, top_k=top_k
    )
    inferred = (
        (
            infer_techniques_with_provider(
                parsed.narrative, candidates, generate=provider_generate
            )
            if provider_generate
            else infer_techniques_with_provider(parsed.narrative, candidates)
        )
        if use_provider
        else infer_techniques(parsed.narrative, candidates)
    )
    grounded = link_evidence(parsed.narrative, inferred)

    return ATTACKInferenceResult(
        alert_id=alert_id,
        inferred_techniques=grounded,
        candidates_considered=candidates,
        needs_human_review=judge_result(parsed.narrative, grounded, candidates),
    )
