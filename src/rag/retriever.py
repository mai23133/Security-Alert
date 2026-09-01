import json
from typing import List, Optional

from src.schemas import TechniqueCandidate
from rank_bm25 import BM25Okapi
from src.rag.embedder import TextEmbedder

class BaselineRetriever:
    def __init__(self, candidates_path: str, allowlist_path: str, embedder: Optional[TextEmbedder] = None):
        self.candidates = self._load_candidates(candidates_path)
        self.allowlist_ids = set(self._load_json(allowlist_path))
        
        # ผูก Embedder เข้ากับ Retriever
        self.embedder = embedder or TextEmbedder()
        
        # ใช้ Embedder ในการตัดคำเตรียม Index แทนการใช้ .lower().split()
        corpus = [
            self.embedder.tokenize(f"{c.technique_name} {c.description_excerpt}")
            for c in self.candidates
        ]
        self.bm25 = BM25Okapi(corpus) if corpus else None

    def _load_json(self, path: str):
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def _load_candidates(self, path: str) -> List[TechniqueCandidate]:
        raw_data = self._load_json(path)
        return [TechniqueCandidate(**item) for item in raw_data]

    def search(self, narrative: str, tactic: Optional[str] = None, top_k: int = 5) -> List[TechniqueCandidate]:
        if not self.bm25 or not self.candidates:
            return []

        # ใช้ Embedder ตัดคำค้นหา
        tokenized_query = self.embedder.tokenize(narrative)
        
        # ดักจับกรณีที่ตัดคำแล้วไม่เหลือข้อความ (เช่น ใส่มาแต่เครื่องหมายวรรคตอน)
        if not tokenized_query:
            return []

        scores = self.bm25.get_scores(tokenized_query)

        scored_candidates = []
        for score, candidate in zip(scores, self.candidates):
            if candidate.technique_id not in self.allowlist_ids:
                continue
            if tactic and candidate.tactic != tactic:
                continue
            
            if score > 0:
                scored_candidates.append((score, candidate))

        scored_candidates.sort(key=lambda x: (-x[0], x[1].technique_id))

        return [item[1] for item in scored_candidates[:top_k]]