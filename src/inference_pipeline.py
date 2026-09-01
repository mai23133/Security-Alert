"""Deterministic orchestration of the in-scope ATT&CK inference agents."""
from __future__ import annotations

from src.agents.alert_parser import parse_alert
from src.agents.evidence_linker import link_evidence
from src.agents.grounding_judge import judge_result
from src.agents.tactic_router import route_tactics
from src.agents.technique_inferencer import infer_techniques
from src.rag.retriever import BaselineRetriever
from src.schemas import ATTACKInferenceResult


def run_inference(
    *, alert_id: str, narrative: str, retriever: BaselineRetriever, top_k: int = 5
) -> ATTACKInferenceResult:
    """Run parser → router → retriever → inference → grounding.

    Parser and router failures deliberately fall back to the original narrative
    and all in-scope tactics, so the endpoint remains deterministic and does
    not require Gemini credentials to operate safely.
    """
    parsed = parse_alert(narrative)
    tactics = route_tactics(parsed)
    candidates = retriever.search(parsed.narrative, tactic=tactics, top_k=top_k)
    inferred = infer_techniques(parsed.narrative, candidates)
    grounded = link_evidence(parsed.narrative, inferred)

    return ATTACKInferenceResult(
        alert_id=alert_id,
        inferred_techniques=grounded,
        candidates_considered=candidates,
        needs_human_review=judge_result(parsed.narrative, grounded, candidates),
    )
