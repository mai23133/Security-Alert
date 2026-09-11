"""Tactic-specific retrieval experts selected by the tactic router."""
from __future__ import annotations

from dataclasses import dataclass

from src.agents.tactic_router import IN_SCOPE_TACTICS
from src.rag.retriever import BaselineRetriever
from src.schemas import TechniqueCandidate


@dataclass(frozen=True)
class TacticSpecialist:
    name: str
    tactic: str

    def retrieve(
        self, narrative: str, retriever: BaselineRetriever, top_k: int
    ) -> list[tuple[float, TechniqueCandidate]]:
        return retriever.search_scored(narrative, tactic=self.tactic, top_k=top_k)


SPECIALISTS = {
    tactic: TacticSpecialist(name=f"{tactic}-specialist", tactic=tactic)
    for tactic in IN_SCOPE_TACTICS
}


def retrieve_with_specialists(
    narrative: str,
    tactics: list[str],
    retriever: BaselineRetriever,
    *,
    top_k: int = 5,
) -> list[TechniqueCandidate]:
    """Dispatch router choices to tactic experts and globally rank their output."""
    selected = [SPECIALISTS[tactic] for tactic in tactics if tactic in SPECIALISTS]
    if not selected:
        selected = list(SPECIALISTS.values())

    best_by_id: dict[str, tuple[float, TechniqueCandidate]] = {}
    for specialist in selected:
        for score, candidate in specialist.retrieve(narrative, retriever, top_k):
            current = best_by_id.get(candidate.technique_id)
            if current is None or score > current[0]:
                best_by_id[candidate.technique_id] = (score, candidate)

    ranked = sorted(best_by_id.values(), key=lambda item: (-item[0], item[1].technique_id))
    return [candidate for _, candidate in ranked[:top_k]]
