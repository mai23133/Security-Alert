# Security-Alert

ระบบรับ Security Alert แบบข้อความและแนะนำ MITRE ATT&CK Technique พร้อม confidence, evidence และสถานะให้มนุษย์ตรวจ ผลลัพธ์เป็น advisory เท่านั้น ไม่มีการตอบสนองเหตุการณ์อัตโนมัติ

สถานะ 7 กันยายน 2026: feature-c-integration รวม mai-work e2ee2da กับ yean-work 5d56d31 แล้ว มี dataset/metrics/runner และ /evaluate พร้อมผล runtime จริง ยังไม่ผ่าน quality gates หรือการรับรอง gold labels ดู [สรุปการรวม C](docs/C_IMPLEMENTATION_SUMMARY_TH.md)

## เริ่มอ่าน

- [ข้อกำหนดหลัก](security-alert-attack-technique-inference.md) — Source of Truth
- [รายงานตรวจล่าสุด](docs/PROJECT_REVIEW_TH.md) — สิ่งที่ทำได้ ข้อจำกัด และผลทดสอบ
- [สรุปไฟล์ทั้งโปรเจกต์](docs/PROJECT_FILE_MAP_TH.md) — หน้าที่และความสัมพันธ์รายไฟล์
- [แผนงาน](docs/WORK_PLAN_TH.md) — งานคงเหลือและลำดับก่อนรวม C
- [คู่มือเอกสาร](docs/PROJECT_READING_GUIDE_TH.md) — เอกสารใดใช้อ่านเรื่องอะไร

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

ก่อน C integration เข้า mai-work ต้องใช้ checkout ของ feature-c-integration เพื่อรัน /evaluate และ runner ใหม่ ต้องทำ ingestion ก่อน pytest และก่อนเปิด API เพราะ alerts route โหลด retriever ตอน import; fresh clone ไม่มี data/processed/ ซึ่งเป็น generated files ที่ถูก ignore ไม่ต้อง commit ข้อมูลนี้

ใช้ Python 3.11.15 ใน .venv; ผลตรวจ integration ล่าสุดดู docs/C_IMPLEMENTATION_SUMMARY_TH.md ไม่ใช่การรับรอง GitHub Actions หรือคุณภาพโมเดลผ่านทุก gate

requirements.txt ตรึงบาง package เช่น FastAPI, HTTPX และ rank-bm25 แต่หลายรายการใช้ช่วงเวอร์ชัน จึงยังไม่ใช่ dependency lock ที่ทำซ้ำได้ทุกเวอร์ชัน

## เปิด local demo แบบไม่เรียก provider

~~~bash
GOOGLE_API_KEY='' GEMINI_API_KEY='' python -m uvicorn src.api.main:app --reload
~~~

เปิด http://127.0.0.1:8000/ui สำหรับกรอก alert เดี่ยว หรือ http://127.0.0.1:8000/docs สำหรับ API docs

main.py โหลด .env ด้วย python-dotenv; การกำหนด key ทั้งสองเป็นค่าว่างใน environment ช่วยกันค่าจาก .env เปิด provider โดยไม่ตั้งใจ หากต้องการเปิด Gemini ให้ตั้ง GOOGLE_API_KEY หรือ GEMINI_API_KEY ใน environment/.env ภายใน sandbox ที่อนุญาตก่อนรัน ตรวจ .env.example เป็นตัวอย่างและห้าม commit secret

เมื่อไม่มี key: parser คง narrative แต่คืน assets/actions/IOCs ว่าง, router ค้นทั้งสาม tactics ส่วน BM25 และ inferencer ทำงานต่อได้ เมื่อมี key: parser/router อาจส่ง narrative ไป Google; ยังไม่ได้ตรวจบริการจริงหรือการรองรับ model ที่ตั้งในโค้ดในรอบนี้

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

Retriever ใช้ BM25 ในหน่วยความจำ; TextEmbedder.embed() ยังเป็น placeholder คืน [] ไม่มี dense embeddings ส่วน inferencer ใช้ lexical rules ไม่เรียก LLM; evidence เป็น exact substring และ judge คืน review flag ยังไม่ตรวจ semantic grounding หรือความกำกวมครบถ้วน

## CI และขอบเขตการตรวจ

.github/workflows/ci.yml ใช้ Ubuntu, Python 3.11, timeout job 10 นาที: install → ingestion → pytest (key ทั้งสองว่าง) → fixture evaluation smoke → git diff --check รันเมื่อ push เข้า main/mai-work/feature-d-integration/feature-c-integration และ PR เข้า main/mai-work รายการ branch D ที่ลบแล้วใน trigger ไม่ทำให้ mai-work หยุดทำงาน

~~~bash
python -m compileall -q src eval tests
GOOGLE_API_KEY='' GEMINI_API_KEY='' python -m pytest -q
git diff --check
git status --short
~~~

Tests ที่ผ่านไม่ยืนยัน F1, semantic safety, browser workflow หรือ production readiness และยังไม่มี global network-blocking test fixture

## ประเมินผล (offline แม้มี key)

~~~bash
python -m eval.run_eval --mode fixture
python -m eval.run_eval --mode runtime
python -m eval.run_eval --mode runtime --require-quality-gates
curl -X POST http://127.0.0.1:8000/evaluate -H 'Content-Type: application/json' -d '{"mode":"runtime","top_k":5}'
~~~

CLI default เป็น fixture เพื่อเข้ากับงาน C เดิม แต่ API default runtime; --require-quality-gates คืน exit 1 หาก numeric gates ไม่ผ่าน (ผลปัจจุบันยังไม่ผ่าน) การประเมินสำเร็จไม่เท่ากับผ่านเกณฑ์ ใช้ --output /tmp/runtime-report.json หากต้องการบันทึก report โดยไม่มี raw narratives

## งานต่อไปและ privacy (หลัง integration)

C integration มี fixture/runtime report แล้ว งานต่อคือปิด semantic grounding, ตรวจ gold labels, subset และ metadata gaps ตาม [handoff](docs/HANDOFF_TH.md)

CORS default จำกัด localhost แต่ยังไม่มี authentication/rate limiting/retention enforcement การเปิด provider ส่งข้อความออกนอกเครื่อง และ error logging ยังมี traceback จึงต้องกำหนด privacy controls ก่อนใช้ alert จริง

MITRE ATT&CK เป็นเครื่องหมายการค้าของ The MITRE Corporation โครงการใช้ Enterprise STIX รุ่น 19.1; attribution ใน README ไม่ทดแทนการตรวจ license/terms สำหรับการแจกจ่ายหรือ deploy
