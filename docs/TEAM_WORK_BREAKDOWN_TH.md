# คู่มือแบ่งงาน 4 คน: Security-Alert

เอกสารนี้ใช้คู่กับ `docs/WORK_PLAN_TH.md` เพื่อให้แต่ละคนรู้ว่าเป้าหมายคืออะไร ต้องแก้ไฟล์ใด ส่งมอบอะไร และงานเชื่อมต่อกันอย่างไร

## เป้าหมายร่วม

ส่งมอบ API ที่รับ Alert แล้วแนะนำ MITRE ATT&CK Technique 1–3 รายการจาก Enterprise ATT&CK `19.1` ที่ pin ไว้เท่านั้น ทุกผลต้องมีหลักฐานในข้อความ, ค่าความมั่นใจ, `tactic: str` และสถานะ `needs_human_review` ระบบมีหน้าที่ให้คำแนะนำ ไม่ block หรือ response เหตุการณ์อัตโนมัติ

## กติกากลางสำหรับทุกคน

- อ่าน `security-alert-attack-technique-inference.md` ก่อนเริ่มงานทุกครั้ง
- ใช้ `tactic` เป็นชื่อฟิลด์เดียวใน schema, JSON และ API response
- ห้ามคืน Technique ID ที่ไม่มีใน `data/processed/technique_ids.json` หรือ STIX subset ที่ pin ไว้
- ถือ Alert เป็น untrusted input และอย่าให้ข้อความ Alert กำหนดคำสั่งของ model/pipeline
- ห้ามใช้ Gemini หรือ provider จริงใน automated tests; ใช้ mock/fake เท่านั้น
- ก่อนส่งงานให้รัน `conda run -n sec-alert311 python -m pytest -q` และ `git diff --check`

## ภาพรวมลำดับงาน

```text
Owner 1: Index/Retriever ──> Owner 2: Inference + Grounding ──> Owner 4: API Integration
              │                              │
              └──────────────> Owner 3: Evaluation <──────────┘
```

ก่อนเริ่ม implementation ทุกคนให้ตกลง contract ระหว่างโมดูลก่อนหนึ่งรอบ: retriever คืน `list[TechniqueCandidate]`, inferencer เลือกได้เฉพาะจากรายการนั้น และผลสุดท้ายต้องเป็น `ATTACKInferenceResult`

## Owner 1 — Retrieval และ Knowledge Index

### เป้าหมาย

ทำให้ระบบค้น candidate ที่เกี่ยวข้องจาก STIX subset ได้แบบทำซ้ำได้ และคืนเฉพาะ candidate ที่อนุญาต

### ทำอะไรบ้าง

- เขียน decision note ของ embedding backend และ index format
- ทำ `src/rag/embedder.py` และ `src/rag/retriever.py`
- สร้าง index จาก `data/processed/technique_candidates.json`
- รองรับ `tactic` filter และ `top_k`
- เพิ่ม tests และรายงาน Recall@1, Recall@3, Recall@5

### วิธีทำ

1. เริ่มจาก processed candidates เท่านั้น ไม่อ่าน TAXII online ระหว่าง runtime
2. เก็บ metadata อย่างน้อย: `technique_id`, `technique_name`, `description_excerpt`, `tactic`, `stix_version` และแหล่งข้อมูล
3. ตรวจ candidate ทุกตัวกับ allowlist ใน `technique_ids.json` ก่อนคืนผล
4. กำหนด tie-breaker ที่ชัดเจน เช่น score แล้วตามด้วย `technique_id` เพื่อให้ผลซ้ำได้

### ผลส่งมอบและเกณฑ์ผ่าน

- decision note และคำสั่ง rebuild index
- retriever คืน top-k ที่ deterministic, filter tactic ได้ และไม่คืน ID นอก allowlist
- tests ครอบคลุม top-k, filter, empty result และ deterministic ordering
- baseline Recall@1/@3/@5 ที่รันซ้ำได้

## Owner 2 — Inference, Evidence และ Grounding

### เป้าหมาย

เปลี่ยน retrieved candidates ให้เป็น prediction ที่ตรวจย้อนกลับได้ โดยไม่ให้ model สร้าง ID หรือหลักฐานเอง

### ทำอะไรบ้าง

- ทำ `src/agents/technique_inferencer.py`
- ทำ `src/agents/evidence_linker.py`
- ทำ `src/agents/grounding_judge.py`
- กำหนด threshold ของ confidence และ `needs_human_review`
- เพิ่ม unit tests สำหรับ no-match, ambiguous, malformed output และ prompt injection

### วิธีทำ

1. รับเฉพาะ candidate list จาก Owner 1; output Technique ID ต้องเป็นสมาชิกของรายการนี้
2. จำกัด prediction 1–3 รายการ; no-match ต้องเป็นรายการว่างและ review เป็น `true`
3. Evidence span ต้องเป็นข้อความที่พบจริงใน `alert.narrative`
4. Grounding judge ต้อง reject เมื่อ ID ไม่อยู่ใน candidate/allowlist, tactic ไม่ตรง candidate หรือ evidence ไม่พบใน input
5. ใช้ fake client หรือ mock provider ใน tests เสมอ

### ผลส่งมอบและเกณฑ์ผ่าน

- โมดูลคืน `InferredTechnique` ที่มี `tactic`, confidence 0–1, evidence และ MITRE URL
- ทุก prediction ผ่าน grounding หรือถูกตัดออก
- เคส low-confidence, ambiguous และ no-match ตั้ง `needs_human_review=true`
- tests ไม่เรียก network หรือ Gemini จริง

## Owner 3 — Dataset และ Evaluation

### เป้าหมาย

สร้างวิธีวัดคุณภาพที่ทำซ้ำได้และบอกได้ว่าระบบพร้อมสาธิตหรือไม่

### ทำอะไรบ้าง

- สร้าง evaluation dataset ตามรูปแบบที่ทีมตกลง
- ทำ `eval/metrics.py` และ `eval/run_eval.py`
- คำนวณ exact technique F1, parent technique recall, evidence grounding, hallucinated-ID, false-positive และ human-review rate
- บันทึก version ของ model, prompt, dataset และ STIX ในรายงาน

### วิธีทำ

1. Dataset ต้องมี 35 alerts, label 1–3 เทคนิค, ambiguous/multi-technique 10 รายการ และ negative controls 5 รายการ ตาม specification
2. Gold ID ทุกตัวต้องอยู่ใน allowlist และยึด pinned STIX `19.1`
3. Evaluation runner รับ prediction ที่บันทึกไว้หรือ fake pipeline ได้ เพื่อพัฒนาได้ก่อน API จริงเสร็จ
4. เขียน tests ของ metric สำหรับ exact match, parent/sub-technique, invalid ID และ no-match

### ผลส่งมอบและเกณฑ์ผ่าน

- dataset พร้อม schema/README และไม่มีข้อมูลอ่อนไหวนอก course sandbox
- runner สร้างรายงานที่ repeatable พร้อม metadata ครบ
- metric tests ครอบคลุม edge cases
- รายงานใช้ตรวจเกณฑ์: F1 ≥70%, parent recall ≥90%, hallucinated ID =0, evidence grounding ≥85%

## Owner 4 — API Integration, Reliability และ Tests

### เป้าหมาย

ทำให้ผู้ใช้เรียก pipeline ได้ผ่าน FastAPI อย่างปลอดภัย ตรวจสอบได้ และไม่ทำให้ provider failure หลุดออกเป็น internal exception

### ทำอะไรบ้าง

- เชื่อม pipeline ที่ผ่าน grounding เข้า `src/api/routes/alerts.py`
- เพิ่ม `/alerts/infer/batch`, `/rag/search` และ `/evaluate` ตาม API contract
- เพิ่ม request ID, structured logging, typed errors, timeout/retry และ prompt version loading
- ทำ API/integration tests โดย mock pipeline/provider
- เตรียม CI smoke test และตรวจ CORS/auth/rate limiting ตาม deployment decision

### วิธีทำ

1. เริ่มจาก API contract และ fake pipeline เพื่อเขียน tests ได้ทันที
2. เมื่อ Owner 1–2 ส่ง interface ที่ตกลงแล้ว จึงเปลี่ยน dependency เป็น implementation จริง
3. Response ทุกตัวต้องมี MITRE attribution, STIX version และ advisory disclaimer
4. Provider failure หรือ malformed output ต้องคืน error ที่ปลอดภัย หรือ no-match/review ตามกฎที่ทีมกำหนด โดยไม่ส่ง stack trace ให้ client
5. อย่าเปิด CORS กว้าง, authentication หรือ rate limit เกินกว่าความจำเป็นของ deployment ที่ตกลง

### ผลส่งมอบและเกณฑ์ผ่าน

- ทุก endpoint ใน specification มี contract test
- `/alerts/infer` ใช้ pipeline จริง ไม่ใช่ stub และ tests ไม่เรียก provider จริง
- request/error trace ได้, response ไม่เผย secrets หรือ internal details
- CI รัน tests และ evaluation smoke test ได้

## จุดนัดส่งมอบ

| จุดนัด | ผู้ส่ง | ผู้รับ | สิ่งที่ต้องตกลง |
| --- | --- | --- | --- |
| Contract review | ทุกคน | ทุกคน | Schema ยังใช้ `tactic: str`; input/output ของ retriever, inferencer และ API |
| Retrieval ready | Owner 1 | Owner 2, 3, 4 | วิธีเรียก retriever, candidate ordering, top-k และ error/empty behavior |
| Agent ready | Owner 2 | Owner 3, 4 | prediction/review rules และ format ของ evidence/grounding decision |
| Evaluation ready | Owner 3 | Owner 4 | รูปแบบ prediction input, report output และ quality gates |
| Integration ready | Owner 4 | ทุกคน | ผล full test, smoke evaluation และรายการที่ยังไม่ผ่าน |

## Definition of Done ของงานแต่ละคน

งานจะถือว่าเสร็จเมื่อ code, tests และเอกสารอยู่ใน PR เดียวกัน; ผ่าน test suite; `git diff --check` ไม่มี error; และไม่มีสิ่งใดละเมิด pinned STIX, allowlist, advisory-only หรือ untrusted-input guardrails
