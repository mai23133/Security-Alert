# Demo Day — Full runtime evaluation report

ผลล่าสุดสำหรับ Iteration 3: full pack 35 alerts ได้ Exact F1 และ parent recall
**97.30%** ผ่าน numeric demo thresholds ทุกข้อ ผลจาก local run บน commit
`0a9071e5132b5e01c96a01daa3eabbe1d848b6b8` ด้วย `behavior-rules-v3`
ดู metadata, dependency versions และ hashes ใน [runtime-final.json](docs/reports/runtime-final.json)

## เปรียบเทียบก่อน–หลังบน full pack เดียวกัน

เทียบ [lexical baseline](docs/reports/runtime-before.json) จาก commit
`0be7a1092ed46d0d34d4b5df1de28ea33d39370f` กับผลล่าสุด โดยใช้ 35 alerts เดียวกัน
dataset SHA-256 และ pinned STIX SHA-256 ตรงกันทั้งสองรายงาน ไม่มีการแก้ gold labels
ใช้ provisional subset 127 IDs, top-k 5 และ parent partial credit 0.5
Serialized candidate/allowlist hashes ต่างกันตามการปรับ KB/retrieval;
ผลนี้แสดงการปรับ pipeline โดยรวม ไม่ใช่การแยกวัด inference เพียงส่วนเดียว

| Metric | ก่อน: lexical baseline | หลัง: behavior-rules-v3 | เกณฑ์ PRD / ผลล่าสุด |
| --- | ---: | ---: | --- |
| Alerts evaluated | 35 | 35 | Full course pack |
| Exact precision | 26.03% | 97.30% | รายงาน |
| Exact recall | 51.35% | 97.30% | รายงาน |
| Exact F1 | 34.55% | 97.30% | ≥70% — ผ่าน |
| Parent technique recall | 52.70% | 97.30% | ≥90% — ผ่าน |
| Evidence grounding (substring) | 100.00% | 100.00% | ≥85% — ผ่านตามนิยามนี้ |
| Hallucinated ID rate | 0.00% | 0.00% | =0% — ผ่าน |
| False-positive rate | 40.00% | 0.00% | PRD ไม่ระบุ threshold |
| Human-review rate | 22.86% | 31.43% | รายงาน |
| Recall@1 | 37.84% | 81.08% | รายงาน |
| Recall@3 | 64.86% | 97.30% | รายงาน |
| Recall@5 | 72.97% | 100.00% | รายงาน |

F1 เพิ่มประมาณ 62.75 จุดเปอร์เซ็นต์ และ parent recall เพิ่ม 44.59 จุดเปอร์เซ็นต์
ผลเพิ่มเติมล่าสุด: behavior-evidence rate 100%, tactic accuracy 97.14%
Diagnostics เหลือ extra prediction 1 รายการ และ inference miss 1 รายการ

## Demo ที่รันใหม่และวิธีตรวจซ้ำ

[demo.json](docs/reports/demo.json) รันผ่านครบ 5 ขั้นตามหัวข้อ 12 ของข้อกำหนด:

1. Brute force + PowerShell คืน `T1110`, `T1059.001` พร้อมหลักฐาน
2. คืน top-5 candidates
3. Benign patch-management คืน no-match พร้อม human-review flag
4. ลบ evidence แล้ว Evidence Linker ตัด predictions และ Judge ส่งให้คนตรวจ
5. เรียก `/evaluate` แสดง metrics ของ full 35 alerts

ผลใหม่มี `functional_demo_passed: true`, `quality_gates_passed: true`,
F1/parent recall 97.30%, grounding 100% และ hallucinated IDs 0%
นี่เป็นผล automated functional demo ไม่ใช่หลักฐานวิดีโอหรือการนำเสนอสด

Test evidence ล่าสุดมี 199 tests, failures/errors/skipped เท่ากับ 0 ดู
[tests.xml](docs/reports/tests.xml) และ release hashes ใน
[release-manifest.json](docs/reports/release-manifest.json)

## ผลประเมิน provider จริง

วันที่ 17 กันยายน 2026 ได้ทดลอง strict full-set evaluation แยก provider โดยกำหนดว่า
ทุก stage ต้องใช้ provider สำเร็จ และห้ามนับ offline fallback เป็นผล LLM:

| Provider / model | Intended alerts | ผล | Metrics |
| --- | ---: | --- | --- |
| Gemini `gemini-3.5-flash-lite` | 35 | หยุดที่ `eval-005` หลัง retry 3 ครั้ง เพราะ rate limit; 4 alerts ก่อนหน้าผ่าน strict stages | ไม่คำนวณ เพื่อไม่สรุปจากชุดข้อมูลไม่ครบ |
| OpenRouter `openrouter/free` | 35 | หยุดที่ `eval-001` หลัง retry 3 ครั้ง เพราะ rate limit | ไม่คำนวณ |

ทั้งสอง provider ยืนยัน connectivity/key/consent ด้วย synthetic alert เท่านั้น แต่ยังไม่มี
full-set LLM score ที่รับรอง จึงห้ามนำค่า offline 97.30% ไปอ้างเป็นคุณภาพ Gemini หรือ
OpenRouter ดูหลักฐานแบบไม่เก็บ narrative/secret ที่
[llm-gemini-full.json](docs/reports/llm-gemini-full.json) และ
[llm-openrouter-full.json](docs/reports/llm-openrouter-full.json)

รันจาก repository root หลังติดตั้ง dependencies ที่ตรึงไว้:

```bash
.venv/bin/python -m src.rag.ingest_stix
GOOGLE_API_KEY='' GEMINI_API_KEY='' .venv/bin/python -m eval.run_eval --mode runtime --subset full --diagnostics --require-quality-gates --output docs/reports/runtime-final.json
GOOGLE_API_KEY='' GEMINI_API_KEY='' .venv/bin/python scripts/demo_acceptance.py
GOOGLE_API_KEY='' GEMINI_API_KEY='' .venv/bin/python -m pytest -q
.venv/bin/python scripts/release_manifest.py
git diff --check
git status --short
```

Full evaluation ล่าสุดคืน exit 0 และปิด provider เสมอ
ใช้ STIX `enterprise-attack-19.1`, dataset `1.0.0-rc1` รวม 20 positive,
5 multi-technique, 5 ambiguous และ 5 negative alerts
รายงาน diagnostics เก็บ evidence offsets/hash แทน raw narratives/spans

## ข้อจำกัดก่อนรับมอบ

Numeric gates ผ่าน แต่ `acceptance_ready: false`: gold labels/composition ยังต้องรับรอง
และ subset 127 IDs ยังต้องได้รับการยืนยันให้สอดคล้องกับข้อกำหนดประมาณ 30–50 IDs
Verbatim grounding/behavior checks ไม่ใช่ independent semantic validation;
confidence เป็น rule score ไม่ใช่ calibrated probability
ชุดประเมินเคยใช้วิเคราะห์ข้อผิดพลาดระหว่างพัฒนา จึงไม่ใช่ blind holdout ใหม่
FPR 0% บน negative controls 5 รายการไม่รับรองผลกับข้อมูลจริงทั่วไป
ผลนี้เป็น local run ไม่ใช่การยืนยัน GitHub Actions หรือการเผยแพร่ v1.0.0
ระบบเป็น advisory และต้องให้ผู้เชี่ยวชาญตรวจสอบ

## ภาคผนวก: รายงาน Iteration 2 เดิม (v0.2.0)

ผลด้านล่างเก็บไว้เป็นประวัติ ใช้เพียง 10 alerts จึงไม่ใช้เทียบ improvement โดยตรง
กับ full pack 35 alerts ด้านบน คำสั่ง historical ต้องรันบนโค้ดรุ่นเดิม;
รันคำสั่งเดียวกันบนโค้ดล่าสุดจะได้ผลของโมเดลใหม่

## Reproduction contract

This historical release asset records the offline runtime evaluation for the
fixed 10-alert `iteration_2_v0.2.0` subset. It is produced from the pinned
MITRE ATT&CK Enterprise STIX 2.1 `enterprise-attack-19.1` knowledge base after:

```bash
python -m src.rag.ingest_stix
GOOGLE_API_KEY='' GEMINI_API_KEY='' python -m eval.run_eval --mode runtime --subset iteration-2
```

The runner calls the real local pipeline with `use_provider=False`; it makes no
network/provider call even if keys are present. The report uses BM25 top-k 5,
the lexical baseline inferencer, parent-match credit 0.5, and exact-substring
evidence grounding. Dataset labels are `1.0.0-rc1` and
`pending_independent_review`.

## Result

| Metric | Runtime result |
| --- | ---: |
| Alerts evaluated | 10 |
| Exact precision | 27.78% |
| Exact recall | 45.45% |
| Exact F1 | 34.48% |
| Parent technique recall | 50.00% |
| Evidence grounding rate (substring) | 100.00% |
| Hallucinated ID rate | 0.00% |
| False-positive rate | 50.00% |
| Human-review rate | 30.00% |
| Recall@1 / Recall@3 / Recall@5 | 27.27% / 63.64% / 63.64% |

The run passed the Iteration 2 execution requirement (the pipeline and metrics
completed), but did not pass the final-demo quality gates: F1 is below 70% and
parent recall below 90%. A successful evaluation run does not assert those
final thresholds.
