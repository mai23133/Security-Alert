import json
from pathlib import Path
from collections.abc import Collection

from src.schemas import TechniqueCandidate
from rank_bm25 import BM25Okapi
from src.rag.embedder import TextEmbedder
from src.agents.behavior import evidence

class BaselineRetriever:
    def __init__(
        self,
        candidates_path: str | Path,
        allowlist_path: str | Path,
        embedder: TextEmbedder | None = None,
        *, snapshot_path: str | Path | None = None,
    ):
        self.snapshot = self._load_json(snapshot_path) if snapshot_path else None
        self.candidates = ([TechniqueCandidate(**item) for item in self.snapshot["candidates"]]
                           if self.snapshot else self._load_candidates(candidates_path))
        ids = self.snapshot["technique_ids"] if self.snapshot else self._load_json(allowlist_path)
        if not isinstance(ids, list) or any(not isinstance(i, str) for i in ids) or len(set(ids)) != len(ids):
            raise ValueError("Invalid allowlist")
        self.allowlist_ids = set(ids)
        if len({c.technique_id for c in self.candidates}) != len(self.candidates):
            raise ValueError("Duplicate candidate IDs")
        if any(c.stix_version != "19.1" for c in self.candidates):
            raise ValueError("Invalid candidate STIX version")
        metadata_path = Path(candidates_path).with_name("technique_metadata.json")
        self.metadata = self.snapshot["metadata"] if self.snapshot else (self._load_json(metadata_path) if metadata_path.exists() else {})
        # ผูก Embedder เข้ากับ Retriever
        self.embedder = embedder or TextEmbedder()
        # ใช้ Embedder ในการตัดคำเตรียม Index แทนการใช้ .lower().split()
        corpus = [
            self.embedder.tokenize(f"{c.technique_id} {c.technique_name} {c.technique_name} "
                + self.metadata.get(c.technique_id, {}).get("description", c.description_excerpt))
            for c in self.candidates
        ]
        self.bm25 = BM25Okapi(corpus) if corpus else None

    def _load_json(self, path: str | Path) -> object:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _load_candidates(self, path: str | Path) -> list[TechniqueCandidate]:
        raw_data = self._load_json(path)
        return [TechniqueCandidate(**item) for item in raw_data]

    def search(
        self, narrative: str, tactic: str | Collection[str] | None = None, top_k: int = 5,
        *, observed_actions: Collection[str] = (), iocs: Collection[str] = (),
    ) -> list[TechniqueCandidate]:
        return [candidate for _, candidate in self.search_scored(
            narrative, tactic, top_k,
            observed_actions=observed_actions, iocs=iocs,
        )]

    def search_scored(
        self, narrative: str, tactic: str | Collection[str] | None = None, top_k: int = 5,
        *, observed_actions: Collection[str] = (), iocs: Collection[str] = (),
    ) -> list[tuple[float, TechniqueCandidate]]:
        """Return ranked candidates with BM25 scores for specialist aggregation."""
        if isinstance(top_k, bool) or not isinstance(top_k, int) or top_k < 1:
            raise ValueError("top_k must be a positive integer")
        if not self.bm25 or not self.candidates:
            return []

        # ใช้ Embedder ตัดคำค้นหา
        tokenized_query = self.embedder.tokenize(narrative)
        # Provider annotations can only weight verbatim input, never inject
        # new search instructions or discard the original narrative.
        for action in observed_actions:
            if action and action in narrative:
                tokenized_query += self.embedder.tokenize(action) * 2
        for ioc in iocs:
            if ioc and ioc in narrative:
                tokenized_query += self.embedder.tokenize(ioc)
        # ดักจับกรณีที่ตัดคำแล้วไม่เหลือข้อความ (เช่น ใส่มาแต่เครื่องหมายวรรคตอน)
        if not tokenized_query:
            return []

        scores = self.bm25.get_scores(tokenized_query)
        allowed_tactics = (
            {tactic} if isinstance(tactic, str) else set(tactic) if tactic else None
        )

        scored_candidates = []
        for score, candidate in zip(scores, self.candidates):
            if candidate.technique_id not in self.allowlist_ids:
                continue
            tactics = set(self.metadata.get(candidate.technique_id, {}).get("tactics", [candidate.tactic]))
            if allowed_tactics is not None and not tactics & allowed_tactics:
                continue
            if allowed_tactics is not None and candidate.tactic not in allowed_tactics:
                candidate = candidate.model_copy(update={"tactic": sorted(tactics & allowed_tactics)[0]})
            # A bounded behavior reranker complements lexical retrieval. It
            # cannot introduce an ID outside this already filtered index.
            if evidence(narrative, candidate.technique_id, candidate.technique_name):
                score += 100.0
            if score > 0:
                scored_candidates.append((score, candidate))

        scored_candidates.sort(key=lambda x: (-x[0], x[1].technique_id))

        return scored_candidates[:top_k]
