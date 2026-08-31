# แผนงานปัจจุบัน Security-Alert

อัปเดต: 31 สิงหาคม 2026
Source of Truth: `security-alert-attack-technique-inference.md`
การแบ่งงานที่ใช้งานอยู่: `docs/TEAM_WORK_PARALLEL_PROPOSAL_TH.md`

## เป้าหมาย MVP

สร้างระบบสาธิตที่รับ Security Alert แบบข้อความ แล้วแนะนำ MITRE ATT&CK Enterprise Technique 1–3 รายการจาก pinned STIX `enterprise-attack-19.1` พร้อม `confidence`, `evidence_spans`, `tactic` และ `needs_human_review` ผลลัพธ์เป็นคำแนะนำเท่านั้น ห้ามตอบสนองเหตุการณ์โดยอัตโนมัติ

## สถานะปัจจุบัน

| ส่วนงาน | สถานะ | หลักฐาน/งานส่งต่อ |
| --- | --- | --- |
| Setup, schema, STIX ingestion และ taxonomy API | เสร็จแล้ว | ใช้ `tactic: str`, pinned STIX `19.1`, ตัด deprecated/revoked และมี taxonomy list/detail API |
| สาย A — Retrieval | กำลังทำ | ต้องส่ง deterministic top-k, allowlist/tactic filter, tests และ Recall@k baseline |
| สาย B — Inference, evidence และ guardrails | เสร็จแล้ว | inferencer, evidence linker, grounding judge และ fake-provider tests พร้อมให้ D เชื่อม; ดู `MAI_WORK_INFERENCE_GUARDRAILS_TH.md` |
| สาย C — Dataset และ evaluation | กำลังทำ | ต้องส่ง gold dataset, metrics และ reproducible report |
| สาย D — API, CI และ UI | กำลังทำ | API ยังเป็น safe no-match stub; ต้องเชื่อม A+B และทำ contract/integration tests |

ผลตรวจล่าสุด: `python -m pytest -q` ผ่าน 27 tests และ `git diff --check` ผ่าน

## ลำดับการรวมงาน

```text
API request
→ A: retrieve_candidates(narrative, tactic=None, top_k=5)
→ B: infer_techniques(narrative, candidates)
→ B: link_evidence(narrative, inferred)
→ B: judge_result(narrative, inferred, candidates)
→ ATTACKInferenceResult
```

D เป็นเจ้าภาพ integration เมื่อ A ส่ง retriever แล้ว โดยคง schema และ disclaimer เดิมไว้ทั้งหมด. Tests ต้องไม่เรียก Gemini หรือ network จริง

## งานคงเหลือก่อน MVP พร้อมประเมิน

1. A ส่ง retriever ที่คืนเฉพาะ candidate ใน pinned allowlist พร้อม Recall@1/@3/@5
2. D เชื่อม A+B เข้ากับ `/alerts/infer` และเพิ่ม batch/search, typed errors, request ID, CI และ UI ตามขอบเขตที่ทีมตกลง
3. C ส่ง dataset 35 alerts (รวม ambiguous/multi-technique 10 และ negative controls 5), metrics และ report ที่ทำซ้ำได้
4. รัน evaluation ระบบรวมให้ผ่าน Exact F1 ≥70%, parent recall ≥90%, hallucinated ID = 0 และ evidence grounding ≥85%
5. ก่อน deploy: จำกัด CORS, เพิ่ม authentication/rate limiting ตาม deployment target, privacy/retention และ acceptance/security tests

## ข้อตกลงและความเสี่ยงที่ต้องติดตาม

- Technique ID ต้องมาจาก pinned STIX subset เท่านั้น; prediction ต้องมาจาก candidates ของ retriever และ evidence ต้องเป็น exact substring ของ narrative
- Alert เป็น untrusted input; no-match, low confidence หรือ ambiguous result ต้องตั้ง `needs_human_review: true`
- หากจะใช้ Gemini ใน runtime ต้องมี timeout, retry, typed errors และ structured-output validation; automated tests ห้ามเรียก provider จริง
- specification ระบุ subset โดยประมาณ 30–50 techniques แต่ processed data ปัจจุบันมี 127 candidates จึงต้องให้ทีม/ผู้สอนยืนยันว่าจะลด subset หรือปรับข้อกำหนดก่อน release
