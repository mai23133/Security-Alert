import json
from typing import List, Optional

# สมมติว่าตั้งค่า PYTHONPATH ใน .env ไว้แล้ว
from src.schemas import TechniqueCandidate
from rank_bm25 import BM25Okapi

class BaselineRetriever:
    def __init__(self, candidates_path: str, allowlist_path: str):
        self.candidates = self._load_candidates(candidates_path)
        self.allowlist_ids = set(self._load_json(allowlist_path))
        
        # สร้าง Index สำหรับ BM25 โดยใช้ชื่อเทคนิคและคำอธิบาย
        corpus = [
            f"{c.technique_name} {c.description_excerpt}".lower().split() 
            for c in self.candidates
        ]
        self.bm25 = BM25Okapi(corpus) if corpus else None

    def _load_json(self, path: str):
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def _load_candidates(self, path: str) -> List[TechniqueCandidate]:
        raw_data = self._load_json(path)
        # แปลง Dict เป็น Pydantic Model ทันที เพื่อความปลอดภัยของข้อมูล
        return [TechniqueCandidate(**item) for item in raw_data]

    def search(self, narrative: str, tactic: Optional[str] = None, top_k: int = 5) -> List[TechniqueCandidate]:
        if not self.bm25 or not self.candidates:
            return []

        # 1. คำนวณคะแนน BM25 จาก Narrative
        tokenized_query = narrative.lower().split()
        scores = self.bm25.get_scores(tokenized_query)

        scored_candidates = []
        for score, candidate in zip(scores, self.candidates):
            # 2. กรองผลลัพธ์ (Filtering)
            if candidate.technique_id not in self.allowlist_ids:
                continue
            if tactic and candidate.tactic != tactic:
                continue
            
            # เก็บเฉพาะตัวที่มีความเกี่ยวข้องบ้าง
            if score > 0:
                scored_candidates.append((score, candidate))

        # 3. จัดเรียงแบบทำซ้ำได้ (Deterministic Sort)
        # -x[0] คือเรียงคะแนนจากมากไปน้อย, x[1].technique_id คือถ้าคะแนนเท่ากันให้เรียงตาม ID
        scored_candidates.sort(key=lambda x: (-x[0], x[1].technique_id))

        # 4. คืนค่าตามจำนวนที่ขอ (Top-K)
        return [item[1] for item in scored_candidates[:top_k]]