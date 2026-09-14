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
    *, alert_id: str, narrative: str, retriever: BaselineRetriever, top_k: int = 5,
    use_provider: bool = False,
    trace: dict | None = None,
) -> ATTACKInferenceResult:
    """Run parser → router → retriever → inference → grounding.

    Parser and router failures deliberately fall back to the original narrative
    and all in-scope tactics, so the endpoint remains deterministic and does
    not require Gemini credentials to operate safely.
    """
    if use_provider:
        parsed = parse_alert(narrative)
        tactics = route_tactics(parsed)
    else:
        # Explicit offline evaluation, regardless of .env or process keys.
        def offline_generate(_prompt: str) -> str:
            raise RuntimeError("Provider disabled for offline evaluation")

        parsed = parse_alert(narrative, generate=offline_generate)
        tactics = route_tactics(parsed, generate=offline_generate)
    candidates = retriever.search(parsed.narrative, tactic=tactics, top_k=top_k,
                                  observed_actions=parsed.observed_actions, iocs=parsed.iocs)
    proposed = infer_techniques(parsed.narrative, candidates)
    candidate_by_id = {c.technique_id: c for c in candidates}
    inferred = []
    seen = set()
    rejected = False
    for prediction in proposed:
        candidate = candidate_by_id.get(prediction.technique_id)
        if (candidate is None or prediction.technique_id in seen
            or prediction.technique_name != candidate.technique_name
            or prediction.tactic != candidate.tactic
            or prediction.mitre_url != "https://attack.mitre.org/techniques/" + prediction.technique_id.replace(".", "/") + "/"
            or len(inferred) >= 3):
            rejected = True
            continue
        inferred.append(prediction)
        seen.add(prediction.technique_id)
    grounded = link_evidence(parsed.narrative, inferred)
    if trace is not None:
        trace.update(tactics=tactics, before_grounding=[t.technique_id for t in inferred],
                     after_grounding=[t.technique_id for t in grounded])

    return ATTACKInferenceResult(
        alert_id=alert_id,
        inferred_techniques=grounded,
        candidates_considered=candidates,
        needs_human_review=rejected or len(grounded) != len(inferred) or judge_result(parsed.narrative, grounded, candidates),
    )
