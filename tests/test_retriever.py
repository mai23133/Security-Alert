import pytest
import os
from src.rag.retriever import BaselineRetriever

CANDIDATES_PATH = "data/processed/technique_candidates.json"
ALLOWLIST_PATH = "data/processed/technique_ids.json"

@pytest.fixture
def retriever():
    if not os.path.exists(CANDIDATES_PATH) or not os.path.exists(ALLOWLIST_PATH):
        pytest.skip("Missing mock data files, skipping test.")
    return BaselineRetriever(CANDIDATES_PATH, ALLOWLIST_PATH)

def test_retriever_initialization(retriever):
    """1. ทดสอบว่าโหลดข้อมูลสำเร็จ"""
    assert len(retriever.candidates) > 0
    assert len(retriever.allowlist_ids) > 0

def test_retriever_tactic_filter(retriever):
    """2. ทดสอบว่าระบบกรอง Tactic ได้ถูกต้อง"""
    results = retriever.search("brute force password login", tactic="credential-access", top_k=5)
    for result in results:
        assert result.tactic == "credential-access"

def test_retriever_allowlist_enforcement(retriever):
    """3. ทดสอบว่าต้องไม่มี ID นอก Allowlist หลุดออกมาเด็ดขาด"""
    results = retriever.search("powershell execution cmd", top_k=10)
    for result in results:
        assert result.technique_id in retriever.allowlist_ids

def test_retriever_deterministic_ordering(retriever):
    """4. ทดสอบว่ารันคำค้นหาเดิม 2 ครั้ง ลำดับและผลลัพธ์ต้องเหมือนกันเป๊ะ 100%"""
    query = "malicious script execution via powershell"
    results_run_1 = retriever.search(query, top_k=3)
    results_run_2 = retriever.search(query, top_k=3)
    assert [r.technique_id for r in results_run_1] == [r.technique_id for r in results_run_2]

def test_retriever_top_k_limit(retriever):
    """5. ทดสอบว่าต้องส่งผลลัพธ์กลับมาไม่เกิน top_k ที่ระบุ"""
    results = retriever.search("windows network connection", top_k=2)
    assert len(results) <= 2