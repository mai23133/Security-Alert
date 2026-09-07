# API contract ปัจจุบัน

ตรวจ 7 กันยายน 2026 บน mai-work (ฐาน e2ee2da + C 5d56d31 ผ่าน 6b3a38c); [specification](../security-alert-attack-technique-inference.md) หัวข้อ 6/8/10 เป็นข้อกำหนดหลัก

## เตรียมระบบ

รัน python -m src.rag.ingest_stix ก่อน import app หรือเปิด uvicorn เพราะ alerts.py สร้าง retriever ทันที ทั้ง single และ search ใช้ retriever ชุดเดียวกันในหน่วยความจำ หลัง rebuild ต้อง restart server เพื่อให้ inference กับ taxonomy ใช้ข้อมูลชุดเดียวกัน

## Endpoints

| Method/path | Input | Response |
| --- | --- | --- |
| GET / | ไม่มี | {"status":"ok","stix_version":"19.1"} |
| GET /ui | ไม่มี | HTML UI วิเคราะห์ alert เดี่ยว |
| POST /alerts/infer | alert_id optional, narrative | ATTACKInferenceResult |
| POST /alerts/infer/batch | alerts 1–25 รายการ | {"results":[ATTACKInferenceResult,...]} |
| POST /rag/search | narrative, tactic list optional, top_k | {"candidates":[TechniqueCandidate,...]} |
| GET /taxonomy/techniques | tactic query optional | {"count":จำนวน,"techniques":[...]} |
| GET /taxonomy/techniques/{technique_id} | ID ไม่สนตัวพิมพ์ | TechniqueCandidate หรือ 404 |
| POST /evaluate | mode=runtime/fixture, top_k=1–25 | report metrics/metadata/quality_gates/disclaimer จาก bundled dataset |

FastAPI มี /docs, /redoc และ /openapi.json เพิ่มโดย framework UI /ui ไม่อยู่ใน OpenAPI schema

## Single inference

~~~json
{
  "alert_id": "demo-001",
  "narrative": "Encoded PowerShell commands were executed."
}
~~~

alert_id ยาวไม่เกิน 128 และหากส่งต้องไม่ว่างหลัง trim; narrative ยาว 1–20,000 ตัวอักษรหลัง trim หากไม่ส่ง ID หรือส่ง null จะสร้าง UUID

ATTACKInferenceResult มี alert_id, inferred_techniques, candidates_considered, needs_human_review และ disclaimer

Prediction แต่ละรายการมี technique_id, technique_name, tactic, confidence, evidence_spans, mitre_url ส่วน candidate มี technique_id, technique_name, tactic, description_excerpt, stix_version

ตัวอย่างรูปแบบ no-match (ไม่ใช่ผลที่รับประกันสำหรับ narrative ด้านบน):

~~~json
{
  "alert_id": "demo-001",
  "inferred_techniques": [],
  "candidates_considered": [],
  "needs_human_review": true,
  "disclaimer": "Advisory tagging only. Not autonomous SOC action. Verify with senior analyst."
}
~~~

candidates_considered อาจไม่ว่างแม้ predictions ว่าง ผล 0–3 รายการเป็น baseline แบบจับคำ; confidence เป็น heuristic ไม่ใช่ probability ที่ผ่าน calibration

## Batch

~~~json
{
  "alerts": [
    {"alert_id": "a-001", "narrative": "Encoded PowerShell commands."},
    {"narrative": "Routine patch management completed."}
  ]
}
~~~

ประมวลผลตามลำดับ ไม่ใช่ parallel batch หาก validation ผิดจะ 422 ทั้ง request หาก error รายการหนึ่งถูกแปลงเป็น HTTPException ใน _run_alert จะคืน no-match/review ใน results ของรายการนั้นและ HTTP 200 ของ batch ไม่มี per-item error code ใน schema ปัจจุบัน จึงแยก benign no-match กับ processing failure จาก body เพียงอย่างเดียวไม่ได้

## RAG search

~~~json
{
  "narrative": "encoded PowerShell execution",
  "tactic": ["execution"],
  "top_k": 5
}
~~~

top_k เป็น strict integer 1–25 ค่า default 5 ไม่รับ bool/string; tactic รับเฉพาะ initial-access/execution/credential-access ซ้ำถูกตัดออก, []/null/ไม่ส่งหมายถึงไม่กรอง narrative ใช้ขีดจำกัดเดียวกับ single

Taxonomy list กรอง tactic แบบ exact match ไม่มี validation แบบ RAG: ค่าไม่รู้จักคืน count=0; หากไฟล์ candidates หายหลัง app import แล้วจะคืน list ว่าง ไม่ใช่ 503

## Evaluation

POST /evaluate รับ {"mode":"runtime","top_k":5} หรือ {} (default runtime/5) mode fixture ใช้ saved predictions ส่วน runtime เรียก pipeline จริงโดย use_provider=False ปิด Gemini แม้มี key ใน .env

ใช้เฉพาะ dataset จำลองที่ bundle มา 35 alerts ห้าม field dataset/output/path/provider หรือ input เพิ่มเติม; top_k strict integer 1–25 route sync ทำงานใน worker thread ไม่ block event loop และไม่บันทึก report/alert ลง disk

Response มี metadata (versions/hashes/provider mode), metrics, quality_gates, numeric_gates_passed, acceptance_ready=false และ disclaimer HTTP 200 หมายถึงประเมินเสร็จ ไม่ใช่ผ่าน F1 gates; 422 สำหรับ request ผิด, 503 EVALUATION_UNAVAILABLE สำหรับข้อมูล/KB ผิดหรือหาย, 500 EVALUATION_FAILED สำหรับ unexpected failure ไม่มี exception ดิบ

## Headers และ errors (ทุก API)

Middleware เพิ่ม X-Request-ID และ X-MITRE-ATTaCK-Version: enterprise-attack-19.1 ให้ response ที่ผ่าน call_next สำเร็จ ค่า stix_version ใน JSON candidates/health เป็น 19.1

Request ID ยอมรับ ASCII letters/numbers และ . _ : - ความยาว 1–128; ค่าไม่ผ่านถูกแทน UUID ต่างจาก alert_id ไม่ควรรับประกัน headers บน unhandled exception ทุกกรณี

| HTTP | Body/เงื่อนไข |
| --- | --- |
| 422 | FastAPI validation detail list; ไม่ใช่ typed error wrapper เดียวกับ 500 |
| 404 | taxonomy detail ไม่พบ ID; detail เป็น string |
| 503 | detail.code=KNOWLEDGE_BASE_UNAVAILABLE เมื่อ OSError/FileNotFoundError หลุดถึง try ของ single/search |
| 504 | detail.code=INFERENCE_TIMEOUT เมื่อ TimeoutError หลุดถึง single route |
| 500 | detail.code=INTERNAL_ERROR สำหรับ Exception ที่ single จับได้ |

~~~json
{"detail":{"code":"INFERENCE_TIMEOUT","message":"Inference timed out. Human review is required."}}
~~~

ถ้า processed files ไม่มีตั้งแต่เริ่ม server จะล้มตอน import ก่อนถึง handler 503 ส่วน Gemini exception ใน parser/router ถูกจับแล้ว fallback จึงไม่จำเป็นต้องได้ 504 และไม่มี total request deadline

CORS default คือ http://127.0.0.1:8000 และ http://localhost:8000 ปรับผ่าน CORS_ALLOWED_ORIGINS (comma-separated); allow GET/POST และ Content-Type/X-Request-ID ยังไม่ได้ตั้ง expose_headers ให้ frontend ข้าม origin อ่าน custom response headers

## ขอบเขตความปลอดภัย

Response inference มี advisory disclaimer แต่ taxonomy/search/health ไม่ได้ใช้ ATTACKInferenceResult จึงไม่มี disclaimer field แบบเดียวกัน logs ของ middleware ไม่เก็บ narrative โดยตรง แต่ exception logging ยังต้องตรวจ privacy เพิ่ม ไม่มี auth/rate limiting และยังไม่ถือว่าพร้อม production ดู [รายงาน](PROJECT_REVIEW_TH.md)
