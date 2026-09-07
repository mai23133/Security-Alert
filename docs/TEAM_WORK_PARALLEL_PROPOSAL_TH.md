# หน้าที่ทีม A/B/C/D หลัง integration

อัปเดต 7 กันยายน 2026 บน feature-c-integration สาย A+B+C+D รวมแล้ว; ยังต้องตรวจรับคุณภาพและ labels ชื่อไฟล์เดิมคงไว้เพื่อให้ลิงก์ของทีมใช้ได้

| สาย | ไฟล์รับผิดชอบ | ส่งมอบแล้ว/งานต่อ |
| --- | --- | --- |
| A: Retrieval | src/rag/, tests/test_retriever.py, tests/test_embedder.py, tests/test_ingest_stix.py | BM25/ingestion พร้อม; ตกลง subset และ metadata |
| B: Agents | src/agents/, src/inference_pipeline.py, tests/test_agents.py, tests/test_inference_guardrails.py | structural baseline พร้อม; semantic/ambiguity/confidence ยังเหลือ |
| C: Evaluation | eval/, data/eval/, metrics/dataset/API tests | fixture/runtime runner และ /evaluate เชื่อมแล้ว; gold-label approval และ quality gates ยังไม่ผ่าน |
| D: Product shell | src/api/, ui/, .github/workflows/, API tests | รวมแล้ว; ต่อ KB lifecycle, concurrency/deadline และ deployment/privacy |

## Contract ร่วม

[specification](../security-alert-attack-technique-inference.md) เป็นข้อกำหนดหลัก คง canonical schema, tactic: str, pinned 19.1, candidate-bound prediction, evidence และ advisory disclaimer ไม่มี automated response

ปัจจุบัน fixture ส่วนมากอยู่ใน test modules ยังไม่มี shared tests/fixtures/ หรือชุด 10 narratives กลางที่ส่งมอบแล้ว ห้ามอ้างข้อเสนอ fixture ในเอกสารเก่าว่าเป็นไฟล์ที่มีจริง

C ต้องใช้ runtime ATTACKInferenceResult หรือ adapter ที่ validate ชัดเจน; fixture predictions ไม่ใช่ runtime quality report และต้องให้ผู้สอนตรวจ gold labelsตามข้อกำหนด

## เจ้าภาพการตัดสินใจ

ทีม/ผู้สอนยืนยันจำนวน dataset, partial-credit formula และ subset ก่อนเปลี่ยน; A/B/D ร่วมตกลง schema revision หากเพิ่ม metadata; ผู้ดูแล deployment ยืนยัน auth/rate limit/retention ก่อนใช้ข้อมูลจริง

Tests ใช้ empty provider keys/mock และต้องทำ ingestion บน clean checkout ข้อมูล processed ไม่ติดตามใน Git ดู [handoff](HANDOFF_TH.md) และ [C checklist](C_EVALUATION_REVIEW_TH.md)
