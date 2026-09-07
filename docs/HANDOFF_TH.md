# ส่งต่องานหลังรวม A+B+D

ตรวจ 7 กันยายน 2026: mai-work f567aa3 รวม PR #4 และ ec73b10 แล้ว งานถัดไปคือ C ไม่ใช่ merge D ซ้ำ

## ผู้รับงานอ่านอะไร

1. [ข้อกำหนดหลัก](../security-alert-attack-technique-inference.md)
2. [รายงานปัจจุบันและข้อจำกัด](PROJECT_REVIEW_TH.md)
3. [แผนงาน](WORK_PLAN_TH.md) และ [รายการตรวจ C](C_EVALUATION_REVIEW_TH.md)
4. [API contract](API_OVERVIEW_TH.md) และ [แผนผังไฟล์](PROJECT_FILE_MAP_TH.md)

## เตรียมฐานงาน

~~~bash
git switch mai-work
git pull --ff-only origin mai-work
python -m pip install -r requirements.txt
python -m src.rag.ingest_stix
GOOGLE_API_KEY='' GEMINI_API_KEY='' python -m pytest -q
~~~

ใช้ Python 3.11 environment ที่ activate แล้ว เก็บงานค้างในเครื่องให้เรียบร้อยก่อนเปลี่ยน branch ผลอ้างอิงรอบนี้ 62 passed ห้าม commit .env หรือ data/processed/

## ข้อตกลงส่งต่อ C

- ใช้ ATTACKInferenceResult จาก src/schemas.py; tactic เป็น str, confidence 0–1, no-match เป็น list ว่างพร้อม review/disclaimer
- Prediction มาจาก retrieved candidates และ pinned allowlist; dataset/report ต้องเก็บ STIX version
- /evaluate ยังไม่มี implementation ต้องกำหนด evaluation request/response ก่อนเชื่อม
- ตรวจ branch C ใหม่ รวมเฉพาะงานที่ review แล้ว และรักษา single/batch/search/UI กับ CI ingestion
- Fixture report ที่ได้ 100% ไม่ใช่หลักฐานคุณภาพ pipeline จริง
- ตกลงจำนวน dataset และน้ำหนัก parent partial credit; gold labels ต้องมีผู้สอนตรวจตาม spec

## ตรวจส่งงาน

~~~bash
GOOGLE_API_KEY='' GEMINI_API_KEY='' python -m pytest -q
python -m compileall -q src eval tests
git diff --check
git status --short
~~~

เมื่อ C มี implementation จริงจึงเพิ่มคำสั่ง evaluation และตรวจ report; ปัจจุบัน python -m eval.run_eval จบเงียบเพราะไฟล์ว่าง ไม่ใช่ผลประเมินสำเร็จ
