# Security-Alert v0.2.0 — AI core

Release date: 7 September 2026
Base branch: `mai-work`
Release commit: `47f9925`

## จุดประสงค์ของ release นี้

v0.2.0 ส่งมอบ pipeline แบบ offline ตั้งแต่รับ Security Alert จนได้คำแนะนำ
MITRE ATT&CK Technique พร้อมหลักฐานและผลประเมินที่ทำซ้ำได้ ระบบเป็น
**advisory tagging only** ไม่ block, quarantine, หรือทำ incident response
อัตโนมัติ ผู้วิเคราะห์ต้องตรวจผลก่อนใช้งานเสมอ

## สิ่งที่เพิ่ม/พร้อมใช้งาน

- Ingest pinned MITRE ATT&CK Enterprise STIX 2.1 `enterprise-attack-19.1`
  เป็น knowledge base ในเครื่อง
- BM25 retrieval ที่ filter Windows/Linux, Initial Access, Execution และ
  Credential Access พร้อม tactic filter และ deterministic top-k
- API/UI สำหรับ infer alert เดี่ยว, batch, inspect retrieval, taxonomy และ
  evaluation
- Pydantic contracts สำหรับ parsed alert, candidate, inferred technique และ
  final response
- Provider boundary สำหรับ Gemini: parser/router รับ structured JSON ที่ไม่
  เชื่อถือ, validate แล้ว fallback อย่างปลอดภัยเมื่อไม่มี key/timeout/JSON ผิด
- Candidate-bounded lexical inferencer: คืนได้ไม่เกิน 3 IDs และเลือกได้เฉพาะ
  candidates จาก pinned knowledge base
- Evidence linker + grounding judge: หลักฐานต้องเป็น exact substring;
  no-match, evidence ไม่ตรง, candidate mismatch, duplicate หรือ low confidence
  จะตั้ง `needs_human_review=true`
- Evaluation runner, metrics, CI smoke test และ fixed 10-alert Iteration 2
  subset

## Agent และการไหลของงาน

```text
Alert Parser
  → Tactic Router
  → BM25 Technique Retriever
  → Technique Inferencer
  → Evidence Linker
  → Grounding Judge
  → ATTACKInferenceResult
```

| Agent | บทบาทใน v0.2.0 |
| --- | --- |
| Alert Parser | สกัด assets/actions/IOCs เป็น `ParsedAlert`; Gemini JSON หรือ safe fallback |
| Tactic Router | จำกัด retrieval เป็น tactics ที่อยู่ใน scope; fallback ค้นทั้งสาม tactic |
| Technique Retriever | ค้น BM25 candidates จาก generated STIX subset |
| Technique Inferencer | lexical baseline เลือก 0–3 techniques จาก candidates เท่านั้น |
| Evidence Linker | เก็บ prediction ที่มี evidence span อยู่ใน narrative จริง |
| Grounding Judge | ตัดสินว่าต้อง human review หรือไม่จาก structural guardrails |

## RAG / knowledge-base sources

| แหล่ง | ตำแหน่ง | สถานะ |
| --- | --- | --- |
| Taxonomy หลัก | `data/raw/enterprise-attack-19.1.json` | tracked, pinned, authoritative |
| Generated allowlist | `data/processed/technique_ids.json` | สร้างด้วย ingestion, ignored, ห้าม commit |
| Generated candidates | `data/processed/technique_candidates.json` | สร้างด้วย ingestion, ignored, ห้าม commit |
| Evaluation snapshot | `data/eval/technique_ids-v19.1.json` | tracked; evaluator ตรวจว่าตรงกับ generated allowlist |

คำสั่งสร้าง KB:

```bash
python -m src.rag.ingest_stix
```

ผลปัจจุบันได้ 127 candidates หลังตัด revoked/deprecated และ filter platform/tactic.
จำนวนนี้ยังมากกว่าเป้าหมาย 30–50 ในข้อกำหนด จึงเป็น known gap ที่ต้องตกลง
subset กับอาจารย์/ทีมก่อน final demo

## API ที่ส่งมอบ

| Method | Endpoint | ใช้งาน |
| --- | --- | --- |
| `POST` | `/alerts/infer` | infer alert เดี่ยวเป็น `ATTACKInferenceResult` |
| `POST` | `/alerts/infer/batch` | infer 1–25 alerts ตามลำดับ input |
| `POST` | `/rag/search` | inspect BM25 candidates/top-k/tactic |
| `GET` | `/taxonomy/techniques` | list pinned techniques |
| `GET` | `/taxonomy/techniques/{id}` | ดู technique ใน subset |
| `POST` | `/evaluate` | metric report จาก bundled course dataset เท่านั้น |
| `GET` | `/ui` | หน้าจอ demo สำหรับ analyst |

API ใส่ request ID และ MITRE ATT&CK version header ทุก response. Alert narrative
จำกัด 20,000 characters; batch จำกัด 25 items. `/evaluate` ไม่รับ filesystem
path, key, provider option หรือ raw alert เพิ่มเติม

## Evaluation assets และผลจริง

- Full course pack: `data/eval/alerts-v1.0.json` มี 35 synthetic/sanitized
  records (20 positive, 5 multi-technique, 5 ambiguous, 5 negative controls)
- Release subset: `data/eval/iteration-2-v0.2.0-subset.json` มี 10 records
  คงที่สำหรับ Iteration 2
- Saved fixture: `data/eval/saved_predictions-v1.0.json` ทดสอบ validator และ
  metric เท่านั้น ไม่ใช่ผลโมเดลจริง
- Runtime result: [eval_report.md](eval_report.md)

Runtime evaluation ปิด provider ด้วย `use_provider=False` แม้ environment มี key;
จึงไม่มี network call และทำซ้ำได้ คำสั่ง release:

```bash
python -m src.rag.ingest_stix
GOOGLE_API_KEY='' GEMINI_API_KEY='' python -m eval.run_eval --mode fixture --subset iteration-2
GOOGLE_API_KEY='' GEMINI_API_KEY='' python -m eval.run_eval --mode runtime --subset iteration-2
```

ผล runtime subset: exact F1 **34.48%**, parent recall **50.00%**,
hallucinated ID rate **0.00%**, substring grounding **100.00%**. รายละเอียด metric
ทั้งหมดอยู่ใน `eval_report.md`.

## Verification ใน release

```bash
GOOGLE_API_KEY='' GEMINI_API_KEY='' python -m pytest -q
python -m compileall -q src eval tests
git diff --check
```

ผลตรวจ ณ release: **101 passed**. GitHub Actions CI รัน install → KB ingestion →
pytest ด้วย keys ว่าง → fixture evaluation subset → whitespace check บน Python 3.11

## Security และการใช้งานอย่างปลอดภัย

- ถือ Alert และ provider response เป็น untrusted input; prompt ห่อ alert ด้วย
  serialized JSON/delimiter และไม่เชื่อ JSON ของ provider โดยตรง
- Technique ID ต้องมาจาก retriever candidates/pinned allowlist; ไม่สร้าง ID เอง
- ทุก response มี advisory disclaimer และ judge สามารถส่งต่อให้ human review
- `.env` และ `data/processed/` ไม่ถูก track
- การเปิด Gemini ทำให้ narrative อาจออกจากเครื่อง; ใช้เฉพาะ sandbox/นโยบายที่
  อนุญาต และอย่า commit secret

## Known gaps / ไม่ใช่การรับรอง final demo

1. F1 และ parent recall ยังต่ำกว่าเกณฑ์สาธิต 70% และ 90%.
2. Grounding ปัจจุบันเป็น exact-substring ไม่ใช่ semantic judge; ยังไม่ครอบคลุม
   negation หรือ ambiguous cases อย่างเพียงพอ.
3. Gold labels เป็น `1.0.0-rc1` และ `pending_independent_review`.
4. `TextEmbedder.embed()` ยัง placeholder; retrieval เป็น BM25 ไม่ใช่ dense/vector RAG.
5. ไม่มี authentication, rate limit, retention/redaction enforcement หรือ full
   production security audit.
6. ยังไม่มี live Gemini acceptance test; test suite mock/ปิด provider เพื่อให้ทำซ้ำได้.

สิ่งเหล่านี้ไม่ขัดกับ Iteration 2 pass bar ซึ่งต้องการ pipeline offline และ
metrics report แต่ต้องปิดก่อนอ้างว่า production-ready หรือผ่าน final demo.
