"""Deterministic orchestration of the in-scope ATT&CK inference agents."""
from __future__ import annotations

from src.agents.alert_parser import parse_alert
from src.agents.evidence_linker import link_evidence
from src.agents.grounding_judge import judge_result
from src.agents.llm_grounding_judge import semantic_judge
from src.agents.llm_technique_inferencer import infer_with_llm, PROMPT_VERSION
from src.agents.provider_chain import ProviderChain
from src.agents.tactic_router import route_tactics
from src.agents.technique_inferencer import infer_techniques
from src.rag.retriever import BaselineRetriever
from src.schemas import ATTACKInferenceResult


def run_inference(
    *, alert_id: str, narrative: str, retriever: BaselineRetriever, top_k: int = 5,
    use_provider: bool = False,
    provider: str = "gemini",
    trace: dict | None = None,
) -> ATTACKInferenceResult:
    """Run parser → router → retriever → inference → grounding.

    Parser and router failures deliberately fall back to the original narrative
    and all in-scope tactics, so the endpoint remains deterministic and does
    not require Gemini credentials to operate safely.
    """
    parser_trace: dict = {}
    router_trace: dict = {}
    if use_provider:
        provider_chain = ProviderChain(provider=provider)
        parsed = parse_alert(
            narrative,
            generate=lambda prompt: provider_chain.generate_text(prompt, trace=parser_trace),
            trace=parser_trace,
        )
        tactics = route_tactics(
            parsed,
            generate=lambda prompt: provider_chain.generate_text(prompt, trace=router_trace),
            trace=router_trace,
        )
        parser_status = "success" if parser_trace.get("provider_succeeded") else "fallback"
        router_status = "success" if router_trace.get("provider_succeeded") else "fallback"
    else:
        # Explicit offline evaluation, regardless of .env or process keys.
        def offline_generate(_prompt: str) -> str:
            raise RuntimeError("Provider disabled for offline evaluation")

        parsed = parse_alert(narrative, generate=offline_generate)
        tactics = route_tactics(parsed, generate=offline_generate)
        parser_status = "not-used"
        router_status = "not-used"
    candidates = retriever.search(parsed.narrative, tactic=tactics, top_k=top_k,
                                  observed_actions=parsed.observed_actions, iocs=parsed.iocs)
    inferencer_trace: dict = {}
    inferencer_status = "not-used"
    confidence_source = "rule-score"
    llm_inferred = False
    if use_provider and candidates:
        llm_result = infer_with_llm(
            parsed.narrative, candidates,
            generate=lambda prompt: provider_chain.generate_text(prompt, trace=inferencer_trace),
        )
        llm_inferred = llm_result.succeeded
        if llm_inferred:
            proposed = llm_result.techniques
            confidence_source = "llm-self-assessed"
            inferencer_status = "success"
        else:
            proposed = infer_techniques(parsed.narrative, candidates)
            inferencer_status = "fallback"
            reason = inferencer_trace.get("fallback_reason", "none")
            inferencer_trace.update(provider="offline", model="none", fallback_used=True,
                                    fallback_reason=llm_result.reason if reason == "none" else reason)
    else:
        proposed = infer_techniques(parsed.narrative, candidates)
        if use_provider:
            inferencer_status = "skipped-no-candidates"
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
    grounded = link_evidence(parsed.narrative, inferred, require_behavior=not llm_inferred)
    deterministic_review = judge_result(parsed.narrative, grounded, candidates,
                                        require_behavior=not llm_inferred)
    semantic_review = False
    semantic_provider_succeeded = None
    semantic_status = "not-used" if not use_provider else "skipped-guardrail"
    judge_fallback_reason = "none"
    # Low confidence/ambiguity require review but should not prevent semantic
    # judgment of structurally valid LLM proposals. Empty results need no judge.
    if use_provider and grounded and (llm_inferred or not deterministic_review):
        judge_provider_trace: dict = {}
        semantic = semantic_judge(
            parsed.narrative, grounded, candidates,
            generate=lambda prompt: provider_chain.generate_text(prompt, trace=judge_provider_trace),
        )
        grounded = semantic.accepted
        semantic_review = semantic.needs_human_review
        semantic_provider_succeeded = semantic.provider_succeeded
        semantic_status = "success" if semantic.provider_succeeded else "fallback"
        if not semantic.provider_succeeded:
            judge_fallback_reason = judge_provider_trace.get("fallback_reason", "none")
            if judge_fallback_reason == "none":
                judge_fallback_reason = semantic.fallback_reason
            judge_provider_trace.update(provider="offline", model="none",
                                        fallback_used=True, fallback_reason=judge_fallback_reason)
            if llm_inferred:
                # A semantic judgment could not be obtained: expose only the
                # conservative rules result, explicitly labelled as such.
                grounded = link_evidence(parsed.narrative, infer_techniques(parsed.narrative, candidates))
                confidence_source = "rule-score"
    else:
        judge_provider_trace = {}
        if use_provider and llm_inferred and not grounded:
            semantic_status = "skipped-no-predictions"
    if trace is not None:
        for stage in (parser_trace, router_trace):
            if use_provider and not stage.get("provider_succeeded") and stage.get("fallback_reason", "none") == "none":
                stage.update(provider="offline", model="none", fallback_used=True,
                             fallback_reason="invalid-response")
        trace.update(tactics=tactics, before_grounding=[t.technique_id for t in inferred],
                     after_grounding=[t.technique_id for t in grounded],
                     semantic_provider_succeeded=semantic_provider_succeeded,
                     parser_status=parser_status, router_status=router_status,
                     judge_status=semantic_status,
                     inferencer_status=inferencer_status,
                     inferencer_provider=inferencer_trace.get("provider", "offline"),
                     inferencer_model=inferencer_trace.get("model", "none"),
                     inferencer_fallback_reason=inferencer_trace.get("fallback_reason", "none"),
                     confidence_source=confidence_source,
                     inference_prompt_version=PROMPT_VERSION if use_provider else "none",
                     parser_provider=parser_trace.get("provider", "offline") if use_provider else "offline",
                     router_provider=router_trace.get("provider", "offline") if use_provider else "offline",
                     judge_provider=judge_provider_trace.get("provider", "none"),
                     parser_model=parser_trace.get("model", "none") if use_provider else "none",
                     router_model=router_trace.get("model", "none") if use_provider else "none",
                     judge_model=judge_provider_trace.get("model", "none"),
                     judge_fallback_reason=judge_fallback_reason,
                     fallback_reason=next((item["fallback_reason"] for item in
                                           (judge_provider_trace, inferencer_trace, parser_trace, router_trace)
                                           if item.get("fallback_reason", "none") != "none"), "none"),
                     fallback_used=("fallback" in {parser_status, router_status, inferencer_status, semantic_status}
                                    or any(item.get("fallback_used") for item in
                                           ([parser_trace, router_trace, inferencer_trace, judge_provider_trace] if use_provider else []))))

    return ATTACKInferenceResult(
        alert_id=alert_id,
        inferred_techniques=grounded,
        candidates_considered=candidates,
        needs_human_review=(rejected or len(grounded) != len(inferred)
                            or deterministic_review or semantic_review
                            or inferencer_status == "fallback"),
    )
