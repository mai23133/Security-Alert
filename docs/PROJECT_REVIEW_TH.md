# รายงานรีวิวโปรเจกต์ Security-Alert

วันที่ตรวจ: 21 กรกฎาคม 2026  
Branch ที่ตรวจ: `mai-work`

## สรุป

โปรเจกต์อยู่ในสถานะ early MVP และผ่านเกณฑ์ Week 1 ด้าน setup, STIX ingestion และ API tests ขั้นต้นแล้ว ระบบสามารถติดตั้ง, รัน FastAPI และตอบ `POST /alerts/infer` ได้อย่างรวดเร็วโดยไม่เรียกบริการภายนอก

ผลทดสอบล่าสุดใน environment `sec-alert311`:

```text
17 passed in 0.39s
```

`/alerts/infer` ยังไม่ใช่ ATT&CK inference จริง: endpoint คืน no-match แบบ deterministic และตั้ง `needs_human_review=true` เสมอ เพื่อหลีกเลี่ยง Technique ที่ไม่ grounded ระหว่างรอ pipeline จริง

## สิ่งที่พร้อมใช้งาน

| ส่วน | สถานะ | หมายเหตุ |
| --- | --- | --- |
| Setup และ dependency | พร้อมสำหรับ MVP | README มี conda/venv, dependency สำคัญถูกตรึงบางส่วน |
| MITRE STIX ingestion | พร้อม | ใช้ `enterprise-attack-19.1.json`, กรอง 3 tactics, Windows/Linux และตัด deprecated/revoked |
| Taxonomy API | พร้อมระดับต้น | list, tactic filter และ detail จาก processed subset |
| Inference API | safe stub | no-match เร็ว, advisory disclaimer และ human-review flag |
| API tests | พร้อมระดับต้น | schema, ingestion, taxonomy และ inference no-match รวม 17 tests |
| Gemini agents | มีโค้ดแต่ยังไม่เชื่อม | parser/router ยังไม่ควรใช้ใน production เพราะไม่มี timeout, retry หรือ guardrail ครบ |

## Findings

### High: API contract ที่ระบุไว้ยังทำไม่ครบ

เอกสารข้อกำหนดระบุ `/alerts/infer/batch`, `/rag/search` และ `/evaluate` แต่ route ปัจจุบันยังไม่มี endpoints เหล่านี้ และ `/alerts/infer` ยังไม่ใช้ retrieval, inference, evidence linking หรือ grounding judge

### Resolved: ชื่อฟิลด์ schema ไม่ตรงกับข้อกำหนด

ข้อกำหนดปัจจุบันกำหนด `tactic: str` สำหรับ `TechniqueCandidate` และ `InferredTechnique` จึงต้องปรับ schema, ingestion, taxonomy API และ tests ให้ใช้ชื่อฟิลด์เดียวกัน

### High: Gemini path ยังไม่มี operational guardrails

`alert_parser.py`, `tactic_router.py` และ `gemini_client.py` ยังไม่มี timeout, retry, error classification, structured output enforcement หรือ prompt-injection hardening แม้ endpoint ปัจจุบันไม่เรียก path นี้ แต่ต้องแก้ก่อนนำกลับมาใช้

### Medium: deployment guardrails ยังไม่พร้อม

CORS ยังเปิด `*`, ไม่มี authentication/rate limit, ไม่มี request ID/structured logging และยังไม่มี privacy/retention policy สำหรับ alert text

### Medium: dependency ยังไม่มี lock file

การตรึง FastAPI/httpx ลดความเสี่ยงด้าน test client แล้ว แต่ dependency อื่นยังใช้ range; ควรสร้าง lock file ก่อนเริ่ม CI/deploy

## ลำดับงานที่แนะนำ

1. ปรับ schema และ ingestion ให้ใช้ชื่อฟิลด์ `tactic` ตาม specification
2. เลือก retrieval backend แบบทำซ้ำได้ และสร้าง index จาก pinned subset
3. เพิ่ม retriever tests และ Recall@k baseline
4. สร้าง inferencer, evidence linker และ grounding judge ที่เลือกได้เฉพาะ retrieved candidates
5. ต่อ pipeline เข้ากับ `/alerts/infer` พร้อม timeout, typed errors, prompt versioning และ mocked API tests
6. ทำ evaluation dataset, metrics, CI และ deployment guardrails

## ข้อสรุป

โค้ดพร้อมสำหรับ review ในฐานะ walking skeleton ที่ติดตั้งและทดสอบซ้ำได้ แต่ยังไม่พร้อมเป็นระบบอนุมาน MITRE ATT&CK จริง จนกว่าจะปิด High findings ข้างต้น โดยเฉพาะ retrieval, grounding และ Gemini guardrails
