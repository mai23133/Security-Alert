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


def test_retriever_rejects_non_positive_top_k(retriever):
    with pytest.raises(ValueError, match="positive integer"):
        retriever.search("PowerShell execution", top_k=0)
    with pytest.raises(ValueError, match="positive integer"):
        retriever.search("PowerShell execution", top_k=-1)

def test_retriever_recall_baseline(retriever):
    """6. วัดผลความแม่นยำ (Recall@1, Recall@3, Recall@5) เบื้องต้น"""
    # เตรียมชุดข้อมูลทดสอบ: (ข้อความจำลองที่คล้าย Alert จริง, รหัสเทคนิคที่คาดหวัง)
    test_cases = [
        ("adversaries may use brute force techniques to guess passwords", "T1110"),
        ("execution of malicious powershell script commands", "T1059.001")
    ]

    hits_at_1 = hits_at_3 = hits_at_5 = 0

    for narrative, gold_id in test_cases:
        results = retriever.search(narrative, top_k=5)
        retrieved_ids = [r.technique_id for r in results]

        # เช็กว่าคำตอบที่ถูกต้อง ติดอันดับ Top 1, 3, 5 หรือไม่
        if gold_id in retrieved_ids[:1]:
            hits_at_1 += 1
        if gold_id in retrieved_ids[:3]:
            hits_at_3 += 1
        if gold_id in retrieved_ids[:5]:
            hits_at_5 += 1

    total = len(test_cases)
    print(f"\n\n--- Baseline Recall Report ---")
    print(f"Recall@1: {(hits_at_1 / total) * 100}%")
    print(f"Recall@3: {(hits_at_3 / total) * 100}%")
    print(f"Recall@5: {(hits_at_5 / total) * 100}%")
    print(f"------------------------------\n")

    # บังคับว่าอย่างน้อยต้องค้นหาเจอใน Top 5
    assert hits_at_5 > 0, "ระบบค้นหาได้ไม่แม่นยำเท่าที่ควร"

def test_retriever_empty_result(retriever):
    """7. ทดสอบว่าถ้าค้นหาด้วยคำที่ไม่มีความหมาย (Empty Result) ต้องคืนค่ากลับมาเป็นลิสต์ว่าง"""
    results = retriever.search("asdfghjkl qwertyuiop", top_k=5)
    assert len(results) == 0, "ระบบต้องคืนค่าว่างเมื่อค้นหาคำที่ไม่มีในระบบ"
