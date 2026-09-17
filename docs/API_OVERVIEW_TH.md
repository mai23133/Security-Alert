# API contract ปัจจุบัน

อัปเดต 17 กันยายน 2026 อ้างอิงข้อกำหนดหลักหัวข้อ Data Schemas, API Contract และ Security & Guardrails

## เตรียมระบบ

```bash
.venv/bin/python -m src.rag.ingest_stix
.venv/bin/python -m uvicorn src.api.main:app \
  --host 127.0.0.1 --port 8000 --no-access-log
```

หากใช้ Gemini/OpenRouter ให้ตั้ง server-side key, `PROVIDER_CONSENT=reviewed-synthetic-only` และเปิดด้วย `--env-file .env` ใช้เฉพาะ reviewed synthetic alerts

FastAPI lifespan โหลดและตรวจ `data/processed/kb_snapshot.json` ครั้งเดียว ทุก route ใช้ snapshot เดียวกัน หลัง ingestion ต้อง restart server ตรวจความพร้อมที่ `/ready`

## Endpoints

| Method/path | Input | Response |
| --- | --- | --- |
| GET `/` | ไม่มี | liveness + STIX version |
| GET `/ready` | ไม่มี | readiness + subset status หรือ 503 |
| GET `/ui` | ไม่มี | Analyst UI |
| POST `/alerts/infer` | `alert_id?`, `narrative`, `inference_mode?` | `ATTACKInferenceResult` |
| POST `/alerts/infer/batch` | alerts 1–25 รายการ | results ตามลำดับ |
| POST `/rag/search` | narrative, tactic list?, top_k 1–25 | candidates |
| GET `/taxonomy/techniques` | tactic? | techniques ใน snapshot |
| GET `/taxonomy/techniques/{id}` | Technique ID | candidate หรือ 404 |
| POST `/evaluate` | runtime/fixture, top_k, diagnostics | offline evaluation report |

## Single inference

```json
{
  "alert_id": "demo-001",
  "narrative": "Encoded PowerShell commands were executed.",
  "inference_mode": "offline"
}
```

- `alert_id`: optional, trim แล้วไม่ว่าง, สูงสุด 128; ไม่ส่งแล้วสร้าง UUID
- `narrative`: 1–20,000 ตัวอักษร
- `inference_mode`: `offline` (default), `gemini`, `openrouter`
- ผล 0–3 Techniques พร้อม evidence; no-match ต้องส่ง human review

Schema canonical อยู่ที่ `src/schemas.py`: `ParsedAlert`, `TechniqueCandidate`, `InferredTechnique`, `ATTACKInferenceResult` ไม่มีการเพิ่ม provider metadata ลง body เพื่อรักษา contract เดิม

## Provider headers

Single response ส่งสถานะผ่าน headers เช่น:

- `X-AI-Parser-Status/Provider/Model`
- `X-AI-Router-Status/Provider/Model`
- `X-AI-Inferencer-Status/Provider/Model/Fallback-Reason`
- `X-AI-Judge-Status/Provider/Model/Fallback-Reason`
- `X-AI-Fallback-Used`, `X-AI-Fallback-Reason`
- `X-AI-Inference-Prompt-Version`
- `X-AI-Confidence-Source`: `rule-score` หรือ `llm-self-assessed`

UI อ่าน headers เหล่านี้ผ่าน CORS exposure Batch คง body schema เดิมและไม่มี per-item provider headers

Fallback reasons ที่ปลอดภัย ได้แก่ `rate-limited`, `timeout`, `network-error`, `temporary-error`, `configuration-error`, `missing-key`, `consent-required`, `invalid-response`, `provider-error` และสถานะ skipped ที่ไม่ใช่ provider failure

## พฤติกรรม inference

- Offline: Parser คง narrative, Router เปิดสาม tactics, BM25 retrieval, rules inference, contextual evidence และ deterministic judge
- Online: provider เดียวทำ Parser → Router → LLM Inferencer → LLM Judge
- LLM Inferencer เลือกได้เฉพาะ retrieved IDs ไม่เกิน 3 และอ้าง `evidence_ids` ที่ระบบ map กลับข้อความต้นฉบับ
- Pipeline ตรวจ ID/name/tactic/MITRE URL/duplicate/จำนวนผลและ evidence อีกครั้ง
- หาก provider หรือ semantic judge ล้มเหลว ระบบใช้ conservative rule result และ `needs_human_review=true`; ไม่สลับไป provider อื่น

## Batch, RAG และ taxonomy

Batch ประมวลผลตามลำดับ รักษาลำดับ input และแปลง item failure เป็น no-match/review ตาม contract; ถ้า total deadline หมดทั้ง request ตอบ 504

RAG `top_k` เป็น strict integer 1–25; tactics รับเฉพาะ `initial-access`, `execution`, `credential-access`; `[]`/null หมายถึงไม่กรอง Taxonomy และ inference ใช้ in-memory retriever ชุดเดียวกัน

## Evaluation

`POST /evaluate` เป็น offline-only เสมอ ใช้ bundled synthetic dataset 35 alerts ไม่รับ path/provider จาก request และไม่เขียน narrative ลง disk `diagnostics` เก็บเฉพาะ IDs, stage status และ evidence offsets/hash

CLI รองรับ `--mode llm --provider gemini|openrouter` แยกต่างหาก โดย strict run ปฏิเสธ provider fallback ผลปัจจุบันดู [MODEL_EVALUATION_RESULTS_TH.md](MODEL_EVALUATION_RESULTS_TH.md)

## Middleware, errors และ limits

- body สูงสุด 600,000 bytes
- workers สูงสุด 4 ต่อ process
- deadline default 60 วินาที ปรับได้มากกว่า 0 ถึง 120 วินาที
- rate limit default 120 requests/min/client IP/process
- เมื่อตั้ง `SECURITY_ALERT_API_KEY` routes ที่ป้องกันต้องส่ง `X-API-Key`
- CORS เป็น explicit HTTP(S) origins; wildcard ถูกปฏิเสธ
- ทุก response เพิ่ม request/server trace ID, MITRE version, `no-store`, `nosniff`, `no-referrer`

| HTTP | ความหมาย |
| --- | --- |
| 401 | API key ไม่ถูกต้อง |
| 413 | body เกินขนาด |
| 422 | request ไม่ตรง contract และไม่สะท้อน input |
| 429 | rate limit พร้อม `Retry-After` |
| 503 | KB/evaluation ไม่พร้อม |
| 504 | total deadline หมด |
| 500 | safe internal error ไม่มี raw exception |

รายละเอียด privacy/deployment อยู่ที่ [DEPLOYMENT_PRIVACY_TH.md](DEPLOYMENT_PRIVACY_TH.md)
