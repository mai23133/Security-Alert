# Security-Alert

ระบบรับ Security Alert แบบข้อความและแนะนำ MITRE ATT&CK Technique พร้อม confidence, evidence และสถานะให้มนุษย์ตรวจ ผลลัพธ์เป็น advisory เท่านั้น ไม่มีการตอบสนองเหตุการณ์อัตโนมัติ

สถานะ 15 กันยายน 2026: พัฒนาต่อจากแผนปิดโครงการแล้ว มี snapshot lifecycle, behavior grounding, operational controls และ browser acceptance; full-pack F1 และ parent recall เท่ากับ 97.30%, FPR 0% จึงผ่าน numeric quality gates ในเครื่องแล้ว แต่ยังรอการรับรอง subset/gold labels และ independent semantic review ดู [สรุปงานและหลักฐานล่าสุด](docs/PROJECT_COMPLETION_IMPLEMENTATION_TH.md)

## เริ่มอ่าน

- [ข้อกำหนดหลัก](security-alert-attack-technique-inference.md) — Source of Truth
- [แผนปิดโครงการ](docs/PROJECT_COMPLETION_PLAN_TH.md) — เกณฑ์และสถานะแต่ละขั้น
- [สรุปฉบับอ่านง่าย: สิ่งที่ทำไปแล้ว](docs/สิ่งที่ทำไปแล้ว_TH.md)
- [สรุปสิ่งที่ทำและงานคงเหลือ](docs/PROJECT_COMPLETION_IMPLEMENTATION_TH.md)
- [คู่มือ deployment/privacy](docs/DEPLOYMENT_PRIVACY_TH.md)
- [แผนงาน](docs/WORK_PLAN_TH.md) — งานคงเหลือและลำดับก่อนรวม C
- [สรุปแบบอ่านง่าย](docs/สิ่งที่ทำไปแล้ว_TH.md) — สิ่งที่ทำแล้วและเงื่อนไขที่ยังไม่ผ่าน
- [สถาปัตยกรรม](docs/architecture.md) — data flow และขอบเขต provider
- [ภาพรวม API](docs/API_OVERVIEW_TH.md) — endpoint และ contract ปัจจุบัน
- [UI จากกิ่ง ui-test](docs/UI_REFERENCE_TH.md) — ธีมสว่าง/มืด ตาราง evaluation และ injection probe

## ติดตั้งและทดสอบจาก clean checkout

ใช้ Python 3.11 ให้ตรง CI หากใช้ Conda ให้สร้างและ activate environment Python 3.11 แทนสองคำสั่ง venv ด้านล่าง

~~~bash
git clone --branch mai-work https://github.com/mai23133/Security-Alert.git
cd Security-Alert
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m src.rag.ingest_stix
GOOGLE_API_KEY='' GEMINI_API_KEY='' python -m pytest -q
git diff --check
~~~

ต้องทำ ingestion ก่อน pytest และก่อนใช้งาน inference; API เปิดได้แม้ KB ไม่มี แต่ /ready และ routes ที่ต้องใช้ KB จะตอบ 503 จนสร้าง KB แล้ว restart server ข้อมูลใน data/processed/ เป็น generated files ไม่ต้อง commit

ใช้ Python 3.11.15 ใน .venv; ผลตรวจล่าสุดดู docs/PROJECT_COMPLETION_IMPLEMENTATION_TH.md ซึ่งไม่ใช่การรับรอง GitHub Actions หรือคุณภาพโมเดลผ่านทุก gate

requirements.txt อ้างอิง requirements.lock ซึ่งตรึง direct/transitive dependencies ที่ตรวจบน Python 3.11

## เปิด local demo แบบไม่เรียก provider

~~~bash
GOOGLE_API_KEY='' GEMINI_API_KEY='' python -m uvicorn src.api.main:app --host 127.0.0.1 --no-access-log
~~~

เปิด http://127.0.0.1:8000/ui สำหรับกรอก alert เดี่ยว หรือ http://127.0.0.1:8000/docs สำหรับ API docs

API ไม่โหลด .env โดยอัตโนมัติและใช้ offline pipeline เสมอ แม้ process จะมี Gemini key; parser คง narrative และ router ค้นสาม tactics ส่วน BM25 กับ behavior inferencer ทำงานในเครื่อง การทดลอง provider โดยตรงนอก API ต้องมี consent สำหรับข้อมูลจำลองที่ตรวจแล้วตามคู่มือ privacy

## ระบบทำอะไรได้

| Endpoint | การทำงาน |
| --- | --- |
| GET / | health และ STIX version |
| GET /ui | UI วิเคราะห์ alert เดี่ยว พร้อม prediction/evidence/candidates/review |
| POST /alerts/infer | pipeline A+B คืน ATTACKInferenceResult |
| POST /alerts/infer/batch | 1–25 alerts คืน wrapper results ตามลำดับ |
| POST /rag/search | BM25 candidates ใน wrapper candidates; top_k 1–25 |
| GET /taxonomy/techniques | list/filter tactic จาก processed candidates |
| GET /taxonomy/techniques/{id} | รายละเอียด candidate; ไม่พบคืน 404 |
| POST /evaluate | ประเมิน bundled dataset 35 alerts แบบ fixture/runtime โดยปิด provider เสมอ |

รายละเอียด request/response และข้อจำกัด errors อยู่ใน [API overview](docs/API_OVERVIEW_TH.md)

~~~bash
curl -X POST http://127.0.0.1:8000/alerts/infer \
  -H 'Content-Type: application/json' \
  -d '{"alert_id":"demo-001","narrative":"Encoded PowerShell commands were executed."}'
~~~

ตัวอย่างนี้ใช้สาธิต contract ไม่ได้รับประกันว่า prediction ใดจะตรง gold label

## Knowledge base และ inference

ใช้ data/raw/enterprise-attack-19.1.json ที่ตรึงใน repository กรอง Windows/Linux และ initial-access, execution, credential-access ตัด deprecated/revoked ออก ได้ 127 candidates (58/48/21 ตามลำดับ credential/execution/initial)

จำนวน 127 ยังเกินเป้าหมายประมาณ 30–50 ใน specification ต้องตัดสินใจ subset กับทีม/ผู้สอนก่อนรับมอบ ไม่เปลี่ยนข้อกำหนดให้ตรง implementation โดยอัตโนมัติ

Retriever ใช้ BM25 จาก full description ร่วมกับ behavior reranking และ weighted verbatim query; index อยู่ใน memory ส่วน TextEmbedder.embed() ยังไม่มี dense embeddings Inference/evidence ตรวจพฤติกรรมใน clause และบริบท negation/benign/ambiguity โดย score เป็นคะแนนตามกฎ ไม่ใช่ความน่าจะเป็นที่สอบเทียบแล้ว กฎเหล่านี้ยังไม่ใช่การตรวจ semantic โดยผู้เชี่ยวชาญอิสระ

## CI และขอบเขตการตรวจ

.github/workflows/ci.yml ใช้ Ubuntu/Python 3.11: install → ingestion → pytest → fixture → development runtime gates → Chromium acceptance → whitespace check อีก job บังคับ full runtime quality gates และเก็บ report แม้ไม่ผ่าน สถานะ local ล่าสุดยังไม่ใช่หลักฐานว่า GitHub Actions ผ่าน

~~~bash
python -m compileall -q src eval tests
GOOGLE_API_KEY='' GEMINI_API_KEY='' python -m pytest -q
git diff --check
git status --short
~~~

ผล tests และ browser acceptance มีหลักฐานใน docs/reports/ ส่วน full quality gate และการอนุมัติรับมอบต้องตรวจแยกกัน

## ประเมินผล (offline แม้มี key)

~~~bash
python -m eval.run_eval --mode fixture --subset iteration-2
python -m eval.run_eval --mode runtime --subset iteration-2
python -m eval.run_eval --mode runtime --require-quality-gates
curl -X POST http://127.0.0.1:8000/evaluate -H 'Content-Type: application/json' -d '{"mode":"runtime","top_k":5}'
~~~

CLI default เป็น fixture และ subset `iteration-2` 10 รายการ; ใช้ `--subset full` เมื่อต้องการวัด course pack 35 รายการ. API default runtime/full pack; --require-quality-gates คืน exit 1 หาก numeric gates ไม่ผ่าน (ผล local ปัจจุบันผ่านและคืน exit 0) การผ่าน numeric gates ยังไม่เท่ากับได้รับอนุมัติรับมอบ ใช้ --output /tmp/runtime-report.json หากต้องการบันทึก report โดยไม่มี raw narratives

## งานต่อไปและ privacy (หลัง integration)

งานคงเหลือมี independent semantic/calibration review และการยืนยัน subset/dataset ตาม [สรุปงานล่าสุด](docs/PROJECT_COMPLETION_IMPLEMENTATION_TH.md)

มี CORS allowlist, optional API key, rate limit ต่อ IP/process, request deadline และ logs ที่ไม่เก็บ input/traceback ค่าเริ่มต้นใช้ loopback sandbox และไม่ส่ง alert ไป provider ดูข้อจำกัด deployment และ retention ใน [คู่มือ privacy](docs/DEPLOYMENT_PRIVACY_TH.md)

MITRE ATT&CK เป็นเครื่องหมายการค้าของ The MITRE Corporation โครงการใช้ Enterprise STIX รุ่น 19.1; attribution ใน README ไม่ทดแทนการตรวจ license/terms สำหรับการแจกจ่ายหรือ deploy
