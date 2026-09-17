# การรันระบบและนโยบายข้อมูลใน course sandbox

อัปเดต 18 กันยายน 2026 หลัง merge-fix ขอบเขตที่รับรองคือ local course sandbox กับข้อมูลจำลอง ไม่ใช่ production deployment

## ติดตั้งและเปิดบริการ

```bash
python3.11 -m venv .venv
.venv/bin/python -m pip install -r requirements.lock
.venv/bin/python -m pip check
.venv/bin/python -m src.rag.ingest_stix
.venv/bin/python -m uvicorn src.api.main:app \
  --host 127.0.0.1 --port 8000 --no-access-log
```

เปิด `/ui`; ตรวจ `/ready` ก่อนเดโม หากใช้ `.env` ต้องเปิดด้วย `--env-file .env` เพราะแอปไม่โหลดไฟล์เอง

## Snapshot และ subset

- Ingestion ตรวจ pinned SHA-256 ของ Enterprise ATT&CK 19.1
- กรองสาม tactics, Windows/Linux และตัด deprecated/revoked
- publish `kb_snapshot.json` แบบ atomic; compatibility exports ใช้กับเครื่องมือเดิม
- runtime ตรวจ snapshot เทียบ raw STIX และถือ generation เดิมจน restart
- default 127 IDs มีสถานะ `provisional_full_in_scope`
- approved manifest ต้องมี 30–50 unique IDs และ approval metadata จริง

## Operational controls

| ค่า | ค่าเริ่มต้น/พฤติกรรม |
| --- | --- |
| `APP_ENV` | `sandbox`; `deployment` บังคับ API key ≥32 ตัวอักษร |
| `SECURITY_ALERT_API_KEY` | ว่างได้ใน local sandbox; เมื่อตั้งต้องส่ง `X-API-Key` |
| `RATE_LIMIT_PER_MINUTE` | 120 ต่อ client IP ต่อ process |
| `REQUEST_TIMEOUT_SECONDS` | 60 วินาที; ต้องอยู่ในช่วง >0 ถึง 120 |
| `CORS_ALLOWED_ORIGINS` | localhost/127.0.0.1; ห้าม wildcard |
| Body/narrative/batch | 600 KB / 20,000 chars / 25 alerts |
| Worker pool | 4; งาน timeout ครอง slot จน thread จบ |

Controls เหล่านี้เป็น in-process สำหรับ sandbox Production หลาย instance ต้องเพิ่ม HTTPS, gateway auth, trusted-proxy policy, distributed rate limit และ centralized retention controls

## Provider และ consent

- Offline mode ไม่เรียก provider แม้ process มี key
- Online mode เลือก Gemini หรือ OpenRouter แยกกันและไม่ส่ง keyไป browser
- ต้องตั้ง `PROVIDER_CONSENT=reviewed-synthetic-only`
- `provider_safety.py` redact IPv4, email และค่าที่มี label password/token/secret/api_key ก่อนส่ง
- Redaction ไม่ครอบคลุมข้อมูลอ่อนไหวทุกชนิด เช่น IPv6, hostname, domain หรือ secret ที่ไม่มี label จึงห้ามส่ง alert จริง
- OpenRouter ตั้ง `provider.data_collection=deny`
- Provider failure ถูกแปลงเป็น safe reason, circuit breaker หยุดเรียก provider เดิมใน request และ fallback เป็น offline พร้อม human review

## Privacy และ retention

- Narrative อยู่ใน memory ระหว่างประมวลผล ไม่มี application database/file persistence
- UI ไม่ใช้ localStorage/sessionStorage และมีปุ่ม Clear
- Evaluation reports เก็บ metric, hashes, IDs และ evidence offsets/hash ไม่เก็บ raw narrative/span
- Structured log เก็บ method, route template, status, latency และ server-generated request ID ไม่เก็บ narrative, alert ID, query, supplied request ID หรือ traceback
- ปิด uvicorn access log; reverse proxy ต้องใช้นโยบายเดียวกัน
- stdout retention 7 วันและลบเมื่อจบรายวิชาเป็น deployment policy ไม่ใช่ฟังก์ชันอัตโนมัติของแอป
- Response inference ตั้งใจคืน evidence และ alert ID จึงต้องถือ response เป็นข้อมูลอ่อนไหวและใช้เฉพาะผู้มีสิทธิ์

## Evaluation และ presentation

Offline full-set metrics เป็นผลที่ทำซ้ำได้และผ่าน PRD gates Gemini/OpenRouter strict runs ปัจจุบัน incomplete เพราะ rate limit จึงไม่มีการนำ offline fallback มาปนเป็นคะแนน LLM

## ก่อน deployment จริง

ต้องมี approved subset/dataset, independent review, target environment, secret rotation, TLS/gateway controls, retention/deletion owner, monitoring และ acceptance ใน environment เป้าหมาย ปัจจุบันยังไม่ควรใช้กับ Alert จริง
