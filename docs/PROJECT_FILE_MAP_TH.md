# แผนผังและสรุปไฟล์ทั้งโปรเจกต์

ตรวจ 7 กันยายน 2026 บน mai-work หลังรวม A+B+C+D; ดู C_IMPLEMENTATION_SUMMARY_TH.md สำหรับไฟล์ integration ที่เพิ่ม

## ภาพรวมการใช้งาน

~~~text
ผู้ใช้ → ui/index.html → src/api/main.py → src/api/routes/alerts.py
                                            ↓
                                  src/inference_pipeline.py
                                  parser → router → retriever
                                            ↓
                                  inferencer → linker → judge
                                            ↓
                                  src/schemas.py → JSON → UI

data/raw/enterprise-attack-19.1.json
    → src/rag/ingest_stix.py
    → data/processed/{technique_candidates,technique_ids}.json
    → BM25 ตอน import API และ taxonomy ตอนรับ request

eval/ และ routes/evaluate.py → fixture/runtime evaluation พร้อม /evaluate
~~~

ลำดับที่ต้องเตรียมคือ install dependencies → ingestion → tests/API ไม่สามารถ clone แล้วข้าม ingestion ได้

## ไฟล์ระดับ root และ config

| ไฟล์ | หน้าที่ | สถานะ/ข้อควรเข้าใจ |
| --- | --- | --- |
| [README.md](../README.md) | จุดเริ่มอ่านและขั้นตอนติดตั้ง/run/test | อัปเดตให้ ingestion ก่อน pytest และเริ่มจาก mai-work |
| [security-alert-attack-technique-inference.md](../security-alert-attack-technique-inference.md) | ข้อกำหนดหลัก 14 หัวข้อ | คงข้อกำหนดเดิม รายงานความขัดแย้งแยกใน review |
| [AGENTS.md](../AGENTS.md) | คำสั่งทำงานกับ repository | บังคับอ่าน spec และตรวจ pytest/diff/status; ไม่เปลี่ยนกติกาในรอบนี้ |
| [requirements.txt](../requirements.txt) | Dependencies ของ runtime/tests | google-genai, FastAPI, Starlette, Uvicorn, Pydantic, dotenv, pytest, HTTPX, rank-bm25; ไม่ใช่ full lock |
| [.env.example](../.env.example) | ตัวอย่าง environment สำหรับ key | ใช้ตั้งค่าเอง ไม่ใช่ secret จริง ไม่เปิดอ่าน .env ในการตรวจรอบนี้ |
| [.gitignore](../.gitignore) | กัน secrets, venv, caches และ generated KB | data/processed/ ยังคง ignore |
| [.github/workflows/ci.yml](../.github/workflows/ci.yml) | CI job test | Ubuntu/Python 3.11; install, ingestion, offline pytest, diff check; job timeout 10 นาที |

ไม่มี tracked packaging config เช่น pyproject.toml, deployment container config หรือ LICENSE แยกในชุดไฟล์ที่ตรวจ ไม่ได้หมายความว่า dependency/data ไม่มีเงื่อนไข license

## Schema และ orchestration

| ไฟล์ | ส่วนประกอบ/หน้าที่ | เชื่อมกับ |
| --- | --- | --- |
| [src/schemas.py](../src/schemas.py) | ParsedAlert, TechniqueCandidate, InferredTechnique, ATTACKInferenceResult; ID regex และ confidence 0–1 | agents, retriever, API และ tests |
| [src/inference_pipeline.py](../src/inference_pipeline.py) | run_inference เรียกหกขั้นตอนและรวมผล canonical response | single/batch API; runner C ควรเรียกผ่าน contract นี้ |

Schema ไม่ได้ตรวจ pinned membership หรือ evidence เองต้องใช้ guards ร่วม; disclaimer มี default แต่ schema ไม่ได้ล็อกข้อความห้ามเปลี่ยน

## Agents

| ไฟล์ | Input → Output | รายละเอียดปัจจุบัน |
| --- | --- | --- |
| [src/agents/__init__.py](../src/agents/__init__.py) | package marker | ว่างโดยตั้งใจ ไม่ใช่งานขาด |
| [src/agents/alert_parser.py](../src/agents/alert_parser.py) | narrative → ParsedAlert | prompt inline, JSON parsing/optional markdown fence, คง narrative เดิม, fallback lists ว่าง |
| [src/agents/tactic_router.py](../src/agents/tactic_router.py) | ParsedAlert → list tactics | provider เลือกเฉพาะสาม tactic; ผิดรูปแบบ/ล้มกลับมาทั้งสาม |
| [src/agents/gemini_client.py](../src/agents/gemini_client.py) | prompt → response.text | อ่าน key สองชื่อ, สร้าง client เมื่อเรียก; model constant gemini-3.5-flash; ไม่ได้ตรวจ live availability ในรอบนี้ |
| [src/agents/technique_inferencer.py](../src/agents/technique_inferencer.py) | narrative+candidates → 0–3 predictions | rule-based lexical overlap; confidence heuristic capped 0.90, ไม่เรียก LLM |
| [src/agents/evidence_linker.py](../src/agents/evidence_linker.py) | narrative+predictions → predictions ที่ยังมี spans | exact substring, meaningful ASCII token, deduplicate spans |
| [src/agents/grounding_judge.py](../src/agents/grounding_judge.py) | narrative+predictions+candidates → bool | ตั้ง human-review flag ตาม structural conditions และ threshold<0.65 |

Assets/IOCs/actions ที่ parser สร้างใช้เป็นข้อมูลให้ router แต่ retriever/inferencer ยังใช้ narrative ต้นฉบับ ไม่ได้มี IOC-specific scoring หรือ semantic model เพิ่ม

SDK ตั้ง timeout 10,000 ms และ retry attempts 3 สำหรับ 408/429/500/502/503/504 แต่ยังไม่มี total deadline ของสอง provider calls รวม batch และ exceptions ถูก parser/router จับไว้

## RAG และ knowledge base

| ไฟล์ | หน้าที่ | พฤติกรรม/ขอบเขต |
| --- | --- | --- |
| [src/rag/ingest_stix.py](../src/rag/ingest_stix.py) | สร้าง processed candidates และ IDs | อ่าน raw pinned bundle; filter attack-pattern, tactics/platforms, deprecated/revoked |
| [src/rag/embedder.py](../src/rag/embedder.py) | TextEmbedder.tokenize | regex lowercasing สำหรับ BM25; embed() คืน [] เป็น placeholder |
| [src/rag/retriever.py](../src/rag/retriever.py) | BaselineRetriever | โหลด JSON และ BM25 corpus ใน RAM; top-k, allowlist, tactic filter; score tie ใช้ ID |
| [data/raw/enterprise-attack-19.1.json](../data/raw/enterprise-attack-19.1.json) | MITRE Enterprise STIX taxonomy | tracked codebook; 25,843 objects จาก ingestion รอบนี้ |
| data/processed/technique_candidates.json | generated candidate records | 127 records; ไม่อยู่ใน Git |
| data/processed/technique_ids.json | generated sorted unique allowlist | 127 IDs; ไม่อยู่ใน Git |

Tactic ที่เก็บเป็นค่าเดียวจาก sorted intersection แม้ source มีหลาย tactic และ description ตัด 300 ตัวอักษร Metadata platform/source ไม่ถูกส่งผ่าน schema ปัจจุบัน; ยังไม่มี query filter platform

จำนวนแบ่งตาม tactic: credential-access 58, execution 48, initial-access 21 เทียบเป้าหมาย specification 30–50 รวมแล้วยังต้องตัดสินใจ subset

## FastAPI

| ไฟล์ | หน้าที่ | ข้อจำกัดที่เกี่ยวข้อง |
| --- | --- | --- |
| [src/api/__init__.py](../src/api/__init__.py) | package marker | ว่างโดยตั้งใจ |
| [src/api/main.py](../src/api/main.py) | FastAPI app, .env, CORS, middleware, health, /ui, route registration | /ui อ่าน HTML ทุก request; ไม่มี auth/rate limit; register evaluate แล้ว |
| [src/api/routes/__init__.py](../src/api/routes/__init__.py) | package marker | ว่างโดยตั้งใจ |
| [src/api/routes/alerts.py](../src/api/routes/alerts.py) | AlertRequest/BatchAlertRequest/BatchInferenceResult, single และ batch | global RETRIEVER โหลดตอน import; จำกัด narrative/ID/batch, แปลง errors ที่จับได้ |
| [src/api/routes/rag.py](../src/api/routes/rag.py) | RAGSearchRequest/RAGSearchResult, /rag/search | แชร์ retriever จาก alerts, top_k strict 1–25, tactic list validation |
| [src/api/routes/taxonomy.py](../src/api/routes/taxonomy.py) | list/detail taxonomy | อ่าน candidates file ทุก request, tactic unknown→empty, ID unknown→404 |
| [src/api/routes/evaluate.py](../src/api/routes/evaluate.py) | /evaluate ของ bundled dataset | mode/top_k bounded, ห้าม client paths, worker thread, safe errors |

ดู [API overview](API_OVERVIEW_TH.md) สำหรับ payload และ error handling จริง การขาด KB ตั้งแต่ import ไม่ถูกครอบด้วย handler 503

## UI

[ui/index.html](../ui/index.html) รวม HTML/CSS/JavaScript ในไฟล์เดียว พัฒนาต่อจาก layout/workflow ของสาย D เดิม มี textarea จำกัด 20,000 ตัวอักษร, loading state, fetch single endpoint, prediction cards, MITRE links, evidence, candidates, no-match, review และ disclaimer

ค่าข้อความใช้ textContent และลิงก์เปิดด้วย noopener/noreferrer ไม่ใช้ CDN ส่วน URL มาจาก canonical inferencer ใน runtime ไม่ใช่ UI validation เพิ่ม ไม่มี batch upload, search form, taxonomy browser หรือ evaluation dashboard

tests ยืนยันว่า HTML ถูก serve และมี field binding แต่ยังไม่ทดสอบ JavaScript/browser interaction จริง

## Prompts และ evaluation

| ไฟล์ | สถานะ |
| --- | --- |
| [prompts/v1/alert_parser.txt](../prompts/v1/alert_parser.txt) | ว่าง; runtime prompt อยู่ใน alert_parser.py |
| [prompts/v1/tactic_router.txt](../prompts/v1/tactic_router.txt) | ว่าง; runtime prompt อยู่ใน tactic_router.py |
| [prompts/v1/inferencer.txt](../prompts/v1/inferencer.txt) | ว่าง; inferencer ปัจจุบันเป็น lexical rules |
| [prompts/v1/grounding_judge.txt](../prompts/v1/grounding_judge.txt) | ว่าง; judge ปัจจุบันเป็น Python checks |
| [eval/metrics.py](../eval/metrics.py) | Exact micro F1, partial parent recall, substring grounding, hallucination, FPR, review และ Recall@k |
| [eval/evaluator.py](../eval/evaluator.py) | สร้าง fixture/runtime report, metadata/hash และเลือก release subset |
| [eval/run_eval.py](../eval/run_eval.py) | CLI, dataset/prediction validation, gold isolation และ `--subset iteration-2|full` |
| data/eval/ | RC course pack 35 alerts, saved fixture, allowlist snapshot และ subset release 10 alerts |
| [eval_report.md](../eval_report.md) | ผล runtime จริงของ v0.2.0 subset; ไม่อ้างว่าเป็น final quality gate |
| [RELEASE_NOTES_v0.2.0.md](../RELEASE_NOTES_v0.2.0.md) | release assets, agents, RAG sources และสถานะ v0.2.0 |

มี evaluation แล้ว; placeholders ที่เหลือคือ prompts/v1 และ embed() เท่านั้น

## ชุดทดสอบรายไฟล์

| ไฟล์ | ครอบคลุมอะไร |
| --- | --- |
| [tests/__init__.py](../tests/__init__.py) | package marker ว่าง |
| [tests/test_schemas.py](../tests/test_schemas.py) | candidate valid/missing required field |
| [tests/test_ingest_stix.py](../tests/test_ingest_stix.py) | tactic/platform/deprecated/revoked filters และ output paths ด้วย temporary STIX fixture |
| [tests/test_embedder.py](../tests/test_embedder.py) | tokenization/empty input และ placeholder vector เป็น list |
| [tests/test_retriever.py](../tests/test_retriever.py) | initialization, tactic filters, allowlist, ranking determinism, top-k/no-match และ Recall@k สองตัวอย่าง |
| [tests/test_agents.py](../tests/test_agents.py) | candidate inference, injected/generic text, exact/missing evidence, no-match/low confidence |
| [tests/test_inference_guardrails.py](../tests/test_inference_guardrails.py) | duplicate/invalid candidate metadata, over-limit, evidence dedup, provider malformed/timeout และ escaped delimiters |
| [tests/test_gemini_client.py](../tests/test_gemini_client.py) | ไม่มี key ต้อง error และ mock client timeout/retry config |
| [tests/test_alerts_api.py](../tests/test_alerts_api.py) | inference, input limits, request ID, mock timeout, batch limits/order/partial failure และ UI served |
| [tests/test_rag_api.py](../tests/test_rag_api.py) | fake retriever, parameter forwarding, invalid top_k/tactics และ empty tactics |
| [tests/test_taxonomy_api.py](../tests/test_taxonomy_api.py) | health/header, list/filter/detail, lowercase ID, 404 และ file missing หลัง app import |
| [tests/test_api.py](../tests/test_api.py) | D product-shell contract scenarios: root/single/batch |

62 test cases เป็นผลก่อน C; ผล integration ล่าสุดดู C_IMPLEMENTATION_SUMMARY_TH.md การนับรวมมี parametrized cases ไม่ใช่จำนวน functions; ไม่ได้รายงาน coverage percentage เพราะไม่ได้วัด

Retriever tests ใช้ processed files และมี skip เมื่อไม่พบไฟล์; API collection ต้องใช้ KB ตั้งแต่ import จึงยังไม่ใช่ isolated tests ทั้งหมด CI เพิ่ม ingestion เพื่อให้พร้อม มี metrics/integration tests และ network sentinel เฉพาะ evaluation; ยังไม่มี browser E2E/global network sentinel

## เอกสารรายไฟล์

| ไฟล์ | วัตถุประสงค์หลังปรับรอบนี้ |
| --- | --- |
| [PROJECT_READING_GUIDE_TH.md](PROJECT_READING_GUIDE_TH.md) | index/ลำดับอ่านเอกสาร |
| [PROJECT_FILE_MAP_TH.md](PROJECT_FILE_MAP_TH.md) | คู่มือรายไฟล์ฉบับนี้ |
| [PROJECT_REVIEW_TH.md](PROJECT_REVIEW_TH.md) | รายงาน findings และขอบเขตหลักฐานล่าสุด |
| [WORK_PLAN_TH.md](WORK_PLAN_TH.md) | สถานะและลำดับงานที่เหลือ |
| [HANDOFF_TH.md](HANDOFF_TH.md) | checklist สำหรับผู้รับงาน |
| [API_OVERVIEW_TH.md](API_OVERVIEW_TH.md) | API contract จริง |
| [architecture.md](architecture.md) | runtime/data flow/provider boundaries |
| [TEAM_WORK_PARALLEL_PROPOSAL_TH.md](TEAM_WORK_PARALLEL_PROPOSAL_TH.md) | ownership ของ A/B/C/D |
| [A_B_PIPELINE_INTEGRATION_TH.md](A_B_PIPELINE_INTEGRATION_TH.md) | A/B integration contract |
| [MAI_WORK_INFERENCE_GUARDRAILS_TH.md](MAI_WORK_INFERENCE_GUARDRAILS_TH.md) | algorithm constraints/limitations |
| [D_IMPLEMENTATION_SUMMARY_TH.md](D_IMPLEMENTATION_SUMMARY_TH.md) | ผลงานและเครดิต D หลัง merge |
| [D_INTEGRATION_REVIEW_TH.md](D_INTEGRATION_REVIEW_TH.md) | ปิด review เก่า ไม่ใช่คำสั่ง merge ซ้ำ |
| [C_EVALUATION_REVIEW_TH.md](C_EVALUATION_REVIEW_TH.md) | เกณฑ์ตรวจ C; ไม่รับรองสถานะ branch ล่าสุด |

## ไฟล์ที่เพิ่ม/นำเข้าตอนรวม C

| ไฟล์ | หน้าที่ |
| --- | --- |
| [eval/evaluator.py](../eval/evaluator.py) | service สร้าง fixture/runtime report, pinned snapshot checks, metadata hashes และ offline adapter |
| [tests/test_metrics.py](../tests/test_metrics.py) | formulas และ validation tests จาก C เดิม |
| [tests/test_evaluation_integration.py](../tests/test_evaluation_integration.py) | gold overwrite, narrative/snapshot/version, network sentinel, runtime adapter และ /evaluate errors |
| [data/eval/README.md](../data/eval/README.md) | dataset contract, RC review status และวิธีรัน |
| [data/eval/alerts-v1.0.json](../data/eval/alerts-v1.0.json) | 35 synthetic gold alerts ยังรอ review |
| [data/eval/saved_predictions-v1.0.json](../data/eval/saved_predictions-v1.0.json) | fixture predictions สำหรับตรวจ metrics |
| [data/eval/technique_ids-v19.1.json](../data/eval/technique_ids-v19.1.json) | snapshot บังคับเท่ากับ generated allowlist |
| [data/eval/report-v1.0.json](../data/eval/report-v1.0.json) | report fixture ที่นำเข้าจาก C ไม่ใช่ runtime acceptance |
| [C_IMPLEMENTATION_SUMMARY_TH.md](C_IMPLEMENTATION_SUMMARY_TH.md) | รายงานการรวม แก้ ทดสอบ ผลจริง และงานรับรองที่ค้าง |

## ไฟล์ local ที่ไม่ใช่ source ส่งมอบ (ต่อ)

.env เป็น secret config; .venv/ เป็น local packages; .pytest_cache/ และ __pycache__/ เป็น cache; data/processed/ เป็น generated KB ทั้งหมดถูก ignore อย่าส่งทั้ง directory งานในเครื่องเป็น deliverable

ตรวจ tracked filenames ไม่พบ .env หรือ bytecode ใน tree ปัจจุบัน ไม่ใช่การยืนยันว่า Git history ไม่เคยมี secret หรือ token เก่าถูก rotate แล้ว

## สิ่งที่ควรทำต่อ

อ่าน findings และตัวอย่าง inference ใน [PROJECT_REVIEW_TH.md](PROJECT_REVIEW_TH.md) หลังรวม C: ระบบมี API/UI และ evaluation จริงแล้ว แต่ยังขาด semantic grounding, subset decision และ operational controls
