# แผนงานปัจจุบัน Security-Alert

อัปเดต: 1 กันยายน 2026
Source of Truth: `security-alert-attack-technique-inference.md`
การแบ่งงานที่ใช้งานอยู่: `docs/TEAM_WORK_PARALLEL_PROPOSAL_TH.md`

## เป้าหมาย MVP

สร้างระบบสาธิตที่รับ Security Alert แบบข้อความ แล้วแนะนำ MITRE ATT&CK Enterprise Technique 1–3 รายการจาก pinned STIX `enterprise-attack-19.1` พร้อม `confidence`, `evidence_spans`, `tactic` และ `needs_human_review` ผลลัพธ์เป็นคำแนะนำเท่านั้น ห้ามตอบสนองเหตุการณ์โดยอัตโนมัติ

## สถานะปัจจุบัน

| ส่วนงาน | สถานะ | หลักฐาน/งานส่งต่อ |
| --- | --- | --- |
| Setup, schema, STIX ingestion และ taxonomy API | เสร็จแล้ว | ใช้ `tactic: str`, pinned STIX `19.1`, ตัด deprecated/revoked และมี taxonomy list/detail API |
| สาย A — Retrieval | เสร็จแล้วระดับ baseline, ยังมี gap | BM25 deterministic top-k, allowlist/tactic filter และ tests พร้อม API; ยังไม่มี platform/source metadata และ subset มี 127 candidates |
| สาย B — Inference, evidence และ guardrails | เชื่อมแล้วระดับ baseline, ยังมี gap | candidate-bounded inference, exact-substring evidence และ review rules ทำงานใน API; semantic evidence-to-technique validation ยังไม่มี |
| สาย C — Dataset และ evaluation | กำลังทำ | ต้องส่ง gold dataset, metrics และ reproducible report |
| สาย D — API, CI และ UI | กำลังทำ | `/alerts/infer` เชื่อม A+B แล้วแบบ deterministic; ยังต้องเพิ่ม batch/search, typed errors, CI และ UI |

ผลตรวจล่าสุด: `python -m pytest -q` ผ่าน 42 tests และ `git diff --check` ผ่าน

## ลำดับการรวมงาน

```text
API request
→ B: parse_alert(narrative)
→ B: route_tactics(parsed_alert)
→ A: retriever.search(narrative, tactic=tactics, top_k=5)
→ B: infer_techniques(narrative, candidates)
→ B: link_evidence(narrative, inferred)
→ B: judge_result(narrative, inferred, candidates)
→ ATTACKInferenceResult
```

D เป็นเจ้าภาพ integration เมื่อ A ส่ง retriever แล้ว โดยคง schema และ disclaimer เดิมไว้ทั้งหมด. `/alerts/infer` เชื่อม A+B แล้ว; tests ต้องไม่เรียก Gemini หรือ network จริง

## งานคงเหลือก่อน MVP พร้อมประเมิน

1. A เติม metadata platform/source หรือบันทึกเหตุผลที่ schema ปัจจุบันยังไม่มี; ตัดสินใจกับทีม/ผู้สอนเรื่อง 127 candidates เทียบเป้าหมาย 30–50
2. B เพิ่ม semantic grounding ที่ตรวจว่า evidence สนับสนุน Technique นั้นจริง ไม่ใช่เพียง substring ทั่วไป
3. D เพิ่ม batch/search, typed errors, request ID, timeout/retry, CI และ UI ตามขอบเขตที่ทีมตกลง
4. C ส่ง dataset 35 alerts (รวม ambiguous/multi-technique 10 และ negative controls 5), metrics และ report ที่ทำซ้ำได้
5. รัน evaluation ระบบรวมให้ผ่าน Exact F1 ≥70%, parent recall ≥90%, hallucinated ID = 0 และ evidence grounding ≥85%
6. ก่อน deploy: จำกัด CORS, เพิ่ม authentication/rate limiting ตาม deployment target, privacy/retention และ acceptance/security tests

## ข้อตกลงและความเสี่ยงที่ต้องติดตาม

- Technique ID ต้องมาจาก pinned STIX subset เท่านั้น; prediction ต้องมาจาก candidates ของ retriever และ evidence ต้องเป็น exact substring ของ narrative
- Alert เป็น untrusted input; no-match, low confidence หรือ ambiguous result ต้องตั้ง `needs_human_review: true`
- หากจะใช้ Gemini ใน runtime ต้องมี timeout, retry, typed errors และ structured-output validation; automated tests ห้ามเรียก provider จริง
- specification ระบุ subset โดยประมาณ 30–50 techniques แต่ processed data ปัจจุบันมี 127 candidates จึงต้องให้ทีม/ผู้สอนยืนยันว่าจะลด subset หรือปรับข้อกำหนดก่อน release
