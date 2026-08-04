# แผนงานปัจจุบัน Security-Alert

อัปเดต: 4 สิงหาคม 2026
Source of Truth: `security-alert-attack-technique-inference.md`

## เป้าหมาย MVP

สร้างระบบสาธิตที่รับ Security Alert แบบข้อความ แล้วแนะนำ MITRE ATT&CK Enterprise Technique 1–3 รายการจาก pinned STIX `enterprise-attack-19.1` พร้อม `confidence`, `evidence_spans`, `tactic` และ `needs_human_review` ผลลัพธ์เป็นคำแนะนำเท่านั้น ห้ามตอบสนองเหตุการณ์โดยอัตโนมัติ

## สถานะจริงจาก repository

| ส่วนงาน | สถานะ | หลักฐาน/ขอบเขตปัจจุบัน |
| --- | --- | --- |
| Setup, dependency และ test พื้นฐาน | เสร็จแล้ว | รัน `conda run -n sec-alert311 python -m pytest -q` ได้ 17 tests |
| Pinned STIX ingestion | เสร็จแล้ว | `src/rag/ingest_stix.py` กรอง 3 tactics, Windows/Linux และตัด deprecated/revoked |
| Schema และ Taxonomy API | เสร็จแล้ว | ใช้ `tactic: str` ใน `TechniqueCandidate` และ `InferredTechnique`; มี taxonomy list/detail API |
| `/alerts/infer` | ปลอดภัยแต่ยังเป็น stub | คืน no-match พร้อม `needs_human_review=true`; ยังไม่เรียก pipeline |
| Embedding, index และ retrieval | ยังไม่เริ่ม | `src/rag/embedder.py`, `src/rag/retriever.py` ยังว่าง |
| Inference, evidence และ grounding | ยังไม่เริ่ม | agent สามไฟล์ยังว่าง |
| Evaluation, CI, UI และ deployment | ยังไม่เริ่ม | ไม่มี dataset/runner/CI/UI ที่ทำงานจริง |

## ข้อตกลงก่อนเริ่มงาน

- Schema ปัจจุบันคือ `tactic: str` ไม่ใช่ `tactics` หรือ `list[str]`.
- หาก STIX technique อยู่ได้มากกว่าหนึ่ง tactic, ingestion เลือก tactic ในขอบเขตเพียงค่าเดียวแบบ deterministic โดยเรียงชื่อก่อนเลือกค่าแรก.
- Candidate, prediction และ API response ต้องใช้ชื่อฟิลด์ `tactic` เหมือนกัน.
- ใช้เฉพาะ Enterprise ATT&CK STIX `19.1` ที่อยู่ใน repository และเฉพาะ ID ใน `data/processed/technique_ids.json`.
- Alert เป็น untrusted input; pipeline ต้องไม่ทำตามข้อความที่พยายามสั่ง model และห้ามสร้าง Technique ID เอง.

## งานที่เหลือและลำดับจริง

| ระยะ | ลำดับ | งาน | Definition of Done | สถานะ |
| --- | --- | --- | --- | --- |
| Foundation | 1 | เลือก embedding backend และบันทึก decision | มี decision note ระบุ model, dependencies, index format, วิธี rebuild และเหตุผลด้าน reproducibility | ยังไม่เริ่ม |
| Foundation | 2 | สร้าง embedding/index จาก processed candidates | Index เก็บ ID, name, description excerpt, tactic, STIX version และ source metadata; rebuild ได้จาก pinned data | ยังไม่เริ่ม |
| Retrieval | 3 | ทำ retriever ที่ filter tactic และ top-k | คืนเฉพาะ `TechniqueCandidate` จาก pinned subset, ลำดับผลซ้ำได้ และรองรับ top-k | ยังไม่เริ่ม |
| Retrieval | 4 | เพิ่ม retrieval tests และ Recall@1/@3/@5 | มี test filter/allowlist/determinism และ baseline report | ยังไม่เริ่ม |
| Inference | 5 | ทำ inferencer, evidence linker และ grounding judge | เลือก 1–3 IDs จาก retrieved candidates เท่านั้น ทุก prediction มี evidence จริง และ judge ปฏิเสธผลไม่ grounded | ยังไม่เริ่ม |
| Inference | 6 | กำหนด confidence/review และทดสอบ input อันตราย | low-confidence, ambiguous, no-match, prompt injection และ malformed output ต้องส่ง human review อย่างปลอดภัย | ยังไม่เริ่ม |
| API | 7 | เชื่อม pipeline เข้า `/alerts/infer` และเพิ่ม endpoints ตาม contract | `/alerts/infer`, `/alerts/infer/batch`, `/rag/search`, `/evaluate` ใช้ contract ที่ตรวจสอบได้; tests mock provider ทั้งหมด | ยังไม่เริ่ม |
| Evaluation | 8 | สร้าง gold dataset, metrics และ runner | มี positive, multi-label, ambiguous, no-match/negative controls; รายงาน F1, parent recall, grounding, hallucination และ false positive | ยังไม่เริ่ม |
| Release | 9 | CI, logging, security, UI และ acceptance | CI/smoke tests, request ID, CORS/auth/rate limit ตาม deployment, privacy/retention, attribution/disclaimer และ acceptance tests | ยังไม่เริ่ม |

## Milestone และเกณฑ์ตรวจรับ

1. Retrieval พร้อม: top-k deterministic จาก pinned subset พร้อม Recall@k baseline.
2. Agent pipeline พร้อม: ผล 1–3 เทคนิคมี evidence และ grounding; ไม่แน่ใจต้องตั้ง review flag.
3. API พร้อม: endpoint ไม่ใช่ stub, ไม่เรียก Gemini จริงใน test, มี typed error handling.
4. Evaluation พร้อม: วัด exact F1, parent recall, evidence grounding, hallucinated-ID และ false-positive rate ได้ซ้ำ.
5. Release candidate: ผ่านเกณฑ์ specification คือ Exact F1 ≥70%, parent recall ≥90%, hallucinated ID =0 และ evidence grounding ≥85%.

## วิธีอัปเดตสถานะ

เมื่อเริ่มงาน ให้เปลี่ยนสถานะเป็น `กำลังทำ` พร้อมชื่อผู้รับผิดชอบและลิงก์ PR; เมื่อเสร็จให้บันทึกคำสั่งทดสอบและผลลัพธ์จริง ห้ามเปลี่ยน Source of Truth หรือ schema โดยไม่ปรับ consumer และ tests ที่เกี่ยวข้องพร้อมกัน

รายละเอียดการแบ่งงานสี่คนอยู่ที่ `docs/TEAM_WORK_BREAKDOWN_TH.md`.
