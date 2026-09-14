# การรันระบบและนโยบายข้อมูลใน course sandbox

ขอบเขตใช้งานของ implementation รอบนี้คือ local course sandbox สำหรับข้อมูลจำลอง ไม่ใช่หลักฐานการอนุมัติ deployment ของผู้สอน

## ติดตั้งและเปิดบริการ

ใช้ Python 3.11 และ dependency ที่ตรึงทั้ง direct/transitive ใน `requirements.lock`:

```bash
python3.11 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m pip check
.venv/bin/python -m src.rag.ingest_stix
.venv/bin/python -m uvicorn src.api.main:app --host 127.0.0.1 --port 8000 --no-access-log
```

เปิด `http://127.0.0.1:8000/ui` และตรวจ `/ready` ก่อนเริ่มสาธิต
`/` เป็น liveness และยังตอบ 200 เมื่อ KB ไม่พร้อม; `/ready` และ routes ที่ต้องใช้ KB ตอบ 503
API ไม่โหลด `.env` โดยอัตโนมัติ และไม่ใช้ provider แม้ process จะมี API key ของ Gemini

## Snapshot และการ rebuild

- Ingestion ตรวจ SHA-256 ของ `enterprise-attack-19.1.json` ที่ตรึงไว้
- `kb_snapshot.json` รวม candidates, allowlist, full description และ metadata ในไฟล์เดียว โดย publish ด้วย atomic replace
- ไฟล์ candidates/IDs/metadata แยกเป็น compatibility exports; runtime อ่าน snapshot เดียวที่ startup
- Startup ตรวจ names, IDs, tactics, source object และ metadata เทียบ pinned STIX จริง
- Rebuild แล้วต้อง restart server ทุกครั้ง; process ที่กำลังทำงานจะใช้ generation เดิมจนหยุด จึงไม่มี taxonomy ใหม่ปนกับ inference เก่า
- การ publish snapshot ล้มเหลวจะคง snapshot เดิม; compatibility exports อาจเปลี่ยนไปแล้ว ต้องรัน ingestion ให้สำเร็จอีกครั้งก่อนใช้ CLI ที่อ่าน exports

เมื่อได้รับ manifest 30–50 IDs ที่อนุมัติจริง ให้ใช้:

```bash
.venv/bin/python -m src.rag.ingest_stix --manifest data/subset/approved.json
```

เริ่มจาก `data/subset/approval-template.json` โดยกรอกหลักฐานจริง ห้ามเปลี่ยน pending เป็น approved เพื่อข้ามการตรวจ
ค่าเริ่มต้นยังคง 127 IDs สำหรับเปรียบเทียบ baseline และระบุ `provisional_full_in_scope` ไม่ใช่ approved subset

## Operational controls

| ค่า | ค่าเริ่มต้น / พฤติกรรม |
| --- | --- |
| `APP_ENV` | sandbox; deployment ต้องมี API key อย่างน้อย 32 ตัวอักษร |
| `SECURITY_ALERT_API_KEY` | ว่างสำหรับ sandbox บน loopback; เมื่อตั้งค่า routes ข้อมูลต้องส่ง `X-API-Key` |
| `RATE_LIMIT_PER_MINUTE` | 120 requests ต่อ client IP ต่อ process; ไม่เชื่อ X-Forwarded-For |
| `REQUEST_TIMEOUT_SECONDS` | 15 วินาที ครอบคลุม request body และงานใน request |
| `CORS_ALLOWED_ORIGINS` | `http://127.0.0.1:8000,http://localhost:8000`; ห้าม wildcard |
| Request body | สูงสุด 600,000 bytes; narrative 20,000 ตัวอักษร; batch 25 รายการ |
| Worker | สูงสุด 4 งานต่อ process; งานที่ timeout ยังคงครอง slot จน thread จบ |

อัตราจำกัดเป็น in-memory ต่อ process ไม่ใช่ distributed quota: deployment หลาย worker/หลายเครื่องต้องใช้ gateway ที่ควบคุม auth, HTTPS, trusted proxy และ quota รวมก่อนรับ traffic จริง
Thread ที่ timeout ไม่ถูกฆ่ากลางงาน; ขอบเขตจำนวน worker ช่วยจำกัดงานค้าง แต่การหยุด process อาจต้องรอ SDK timeout/retry หากมีการเรียก provider จากโค้ดภายนอก API
Batch item ที่ล้มเหลวเป็น no-match/review ตาม contract เดิม; ถ้า deadline รวมหมด ทั้ง request ตอบ 504 โดยไม่ส่ง partial JSON

## Privacy, consent และ retention

- API/UI ใช้ offline inference เท่านั้น ไม่มีตัวเลือกส่ง alert ไป provider ผ่าน request
- Narrative อยู่ใน memory ระหว่างประมวลผล; ไม่มีการเขียนลงฐานข้อมูล/ไฟล์หรือ browser storage
- ผลลัพธ์มี evidence และ alert ID ตาม contract จึงอาจมีข้อความจาก input โดยตั้งใจ; error responses ไม่สะท้อน input
- Browser มีปุ่มล้าง input, key และผลลัพธ์; การปิดหน้าเป็นการสิ้นสุดการใช้งาน ไม่มี secure memory erasure guarantee
- ถ้า worker timeout ข้อมูลอาจอยู่ใน memory จนงานนั้นจบ โดยไม่มี persistent retention
- Application logs มีเฉพาะ method, route template, status, latency และ server-generated request ID; ไม่บันทึก narrative, alert ID, raw path/query, supplied request ID หรือ exception traceback
- ใช้ `X-Server-Trace-ID` เทียบกับ request ID ใน structured log; `X-Request-ID` ยังส่งกลับค่าของ client ที่ถูก format แต่ไม่นำข้อมูลที่ client กำหนดลง log
- ปิด uvicorn access logs ด้วย `--no-access-log` เพื่อหลีกเลี่ยง raw paths/query; หากมี reverse proxy ต้องตั้ง logging policy ให้สอดคล้องกัน
- ค่าเริ่มต้นไม่มี persistent application log sink; หากเก็บ stdout เป็นไฟล์ ให้เจ้าของ sandbox จำกัดสิทธิ์เฉพาะผู้ดูแล เก็บไม่เกิน 7 วัน และลบเมื่อสิ้นสุดรายวิชา นี่คือ policy ที่ต้องจัดการใน deployment ไม่ใช่ log rotation ที่แอปทำให้อัตโนมัติ
- Evaluation artifacts เก็บ metrics, hashes, IDs และ evidence offsets/hash ไม่มี narrative หรือ span ดิบเพิ่ม; ใช้เฉพาะ synthetic datasets

สำหรับการทดลองเรียก provider โดยตรงนอก API ต้องได้รับอนุญาตตามนโยบายรายวิชาและตรวจข้อมูลจำลองก่อนตั้ง `PROVIDER_CONSENT=reviewed-synthetic-only`
Wrapper จึงจะยอมเรียก provider และแทน IPv4/email/ค่าที่มีชื่อ password, token, secret, api_key ก่อนส่ง
Redaction นี้ไม่ตรวจข้อมูลอ่อนไหวทุกชนิดและไม่ใช่สิทธิ์ส่ง alert จริง; domain, IPv6, hostnames หรือความลับที่ไม่ได้ติด label อาจยังอยู่ จึงต้องตรวจข้อมูลก่อนเสมอ

## ก่อน deployment จริง

ต้องมี subset/dataset approval, full runtime quality gates ผ่าน, นโยบาย consent/retention ที่เจ้าของระบบยืนยัน และ acceptance ใน environment เป้าหมาย
โค้ดครั้งนี้ไม่ได้ deploy, rotate secret ของบัญชีภายนอก หรืออ้างว่าการตรวจด้านองค์กรเหล่านี้ผ่านแล้ว
