# สรุปการรวมสาย C และผลการตรวจ

อัปเดต 7 กันยายน 2026 บน feature-c-integration ฐาน mai-work e2ee2da รวม origin/yean-work 5d56d31 โดยรักษาประวัติและผลงานผู้พัฒนาสาย C ผ่าน merge

## ขอบเขตที่ทำเสร็จ

รวม evaluation foundation ของ C เข้ากับ A+B+D, แก้บั๊กที่พบใน review, เพิ่ม runtime evaluation และ POST /evaluate พร้อม tests และเอกสาร งานนี้ไม่ได้เปลี่ยน gold labels, ลด subset หรือปรับสูตรเพื่อให้คะแนนผ่าน การรับรองโครงการทั้งหมดต้องรอผล quality gates และผู้สอนตรวจข้อมูล

## งานจาก C ที่คงไว้

- Dataset synthetic/sanitized 35 alerts: 20 positive, 5 multi-technique, 5 ambiguous, 5 negative
- Saved predictions fixture และ report ที่ระบุว่าไม่ใช่ผลโมเดลจริง
- Exact micro precision/recall/F1, parent partial recall, substring grounding, hallucination, FPR, human review และ Recall@1/3/5
- Parent-only match credit 0.5 และ dataset version 1.0.0-rc1
- Tests formulas และ dataset/prediction validation เดิม

## รายการแก้

| ประเด็น | สิ่งที่ทำ |
| --- | --- |
| Prediction เขียนทับ gold | Validator ปฏิเสธ gold_technique_ids/narrative/category ใน predictions; build_records คัดเฉพาะ prediction fields แม้ caller ข้าม validation |
| Narrative ไม่ตรวจ | ตรวจ string ไม่ว่างหลัง trimและยาวไม่เกิน 20,000 |
| Allowlist แยก | ใช้ generated allowlist เป็น default และตรวจ snapshot เท่ากันทุกครั้ง; runtime ตรวจ candidate IDs/version |
| Fixture คนละรูปกับ API | Adapter แปลง ATTACKInferenceResult.candidates_considered เป็น candidates; ไม่แก้ canonical schema |
| ไม่มี runtime runner | --mode runtime เรียก run_inference จริงสำหรับทั้ง dataset โดย use_provider=False |
| Quality error ถูก reject ก่อนวัด | Runtime validate โครงสร้าง แต่ไม่ใช้ fixture validator ที่ตัด unknown IDs/evidence; นับความผิดพลาดใน metrics |
| Offline เมื่อมี key | Pipeline มี explicit offline option ทำ parser/router fallback และปิด provider ไม่ขึ้นกับ environment |
| Report ไม่พอทำซ้ำ | เพิ่มเวลา, commit, code/data/STIX/candidate/allowlist/prediction SHA256, provider mode, top-k, parent credit และ grounding kind |
| Gates กับ acceptance สับสน | แยก numeric_gates_passed และ acceptance_ready=false; fixture ไม่ใช่ runtime gate |
| /evaluate ยังว่าง | เพิ่ม bundled-dataset endpoint, bounded input, safe errors และ worker thread |
| Conflicts เอกสาร | แก้ 2 ไฟล์โดยยึดสถานะ mai-work แล้วอัปเดตผล C ปัจจุบัน |

Commit metadata ระบุ HEAD ขณะรัน; หากมีงานค้าง code_sha256 ระบุ source bytes จริงได้ การรันซ้ำ metrics/prediction hash ต้องตรงกัน แต่ timestamp/commit อาจเปลี่ยน ไม่เปรียบเทียบ report ทั้งไฟล์แบบ byte-for-byte

## วิธีรัน

จาก root ภายใต้ Python 3.11 environment:

~~~bash
python -m pip install -r requirements.txt
python -m src.rag.ingest_stix
GOOGLE_API_KEY='' GEMINI_API_KEY='' python -m pytest -q
python -m eval.run_eval --mode fixture
python -m eval.run_eval --mode runtime
python -m eval.run_eval --mode runtime --output /tmp/security-alert-runtime.json
python -m eval.run_eval --mode runtime --require-quality-gates
~~~

Default CLI เป็น fixture ตาม runner เดิม Default API เป็น runtime การเพิ่ม --require-quality-gates ใช้ได้เฉพาะ runtime; exit 0 เมื่อ numeric gates ผ่าน, exit 1 เมื่อประเมินสำเร็จแต่คะแนนไม่ผ่าน, exit 2 เมื่อ input/configuration ผิด ส่วน run ปกติคืน 0 เมื่อสร้าง report สำเร็จแม้คุณภาพยังไม่ผ่าน

## API

~~~bash
curl -X POST http://127.0.0.1:8000/evaluate \
  -H 'Content-Type: application/json' \
  -d '{"mode":"runtime","top_k":5}'
~~~

mode รับ fixture/runtime, top_k strict integer 1–25; {} ใช้ runtime/5 ไม่รับ paths, custom narratives, output destination หรือ provider config ใช้ dataset ที่มากับ repo เท่านั้น ไม่มี raw alert ใน response และไม่เขียน report ลง disk

HTTP 200 หมายถึงคำนวณสำเร็จ; ดู numeric_gates_passed ต่อ 422 คือ request validation, 503 คือ evaluation inputs/KB ใช้ไม่ได้, 500 คือ unexpected failure ข้อความทั่วไปพร้อม request/version headers ตาม middleware

## ผลประเมินจริง

Dataset RC 35 รายการ, pinned 19.1, BM25 top_k=5, provider disabled:

| Metric | Fixture | Runtime |
| --- | ---: | ---: |
| Exact precision | 100% | 26.03% |
| Exact recall | 100% | 51.35% |
| Exact F1 | 100% | 34.55% |
| Parent recall (credit 0.5) | 100% | 52.70% |
| Substring grounding | 100% | 100% |
| Hallucinated ID | 0% | 0% |
| False-positive rate | 0% | 40% (2/5 negatives) |
| Human-review rate | 28.57% | 22.86% |
| Recall@1 | 81.08% | 37.84% |
| Recall@3 | 100% | 64.86% |
| Recall@5 | 100% | 72.97% |

Runtime ยังไม่ผ่าน Exact F1≥70% และ parent recall≥90% ค่า grounding 100% ตรวจเฉพาะ substring ไม่ใช่ semantic evidence จึงยังไม่เป็นหลักฐานผ่านการรับมอบทั้งหมด

## การตรวจ

ชุดทดสอบรวมครอบคลุม regression A+B+D, tests C เดิม และ integration ใหม่: gold overwrite, bad narrative, snapshot drift, version mismatch, offline เมื่อมี key, deterministic runtime, unknown IDs/evidence ถูกวัดจริง, API path injection/limits/errors และ CLI gate exit code

Workspace: 100 passed; clean copy ที่ไม่มี .env/data/processed แล้วทำ ingestion ใหม่: 100 passed รวม fixture/runtime CLI และ compileall ผ่าน git diff --check และลิงก์เอกสารผ่าน ไม่มี skipped tests ใน run นี้ TestClient ค้างใน sandbox แต่รันทดสอบเดียวกันนอก sandbox ผ่านโดยปิด provider keys

ผล runtime ของ clean copy ตรงกับ workspace; code_sha256 คือ 866dd769305b0484e0d9d563646df704173577bc472812053991f315d96c13bc และ prediction_sha256 คือ 9afa0609f1b89d4e7cf996fac98f136ed5248ec104c6ebf146b2c6dcd944a2a1 สำหรับ source ที่ตรวจครั้งนี้

งานรวมอยู่บน feature-c-integration เพื่อ review ก่อนเข้า mai-work; การตรวจ local ไม่ใช่ผลรับรอง CI บน GitHub

## สิ่งที่ยังต้องให้ทีม/ผู้สอนรับรอง

1. Gold labels ยังเป็น pending_independent_review ไม่สร้างชื่อผู้ตรวจหรืออนุมัติแทนผู้สอน
2. จำนวน dataset 35 รวมกรณีพิเศษเป็นการคงโครงสร้าง C เดิม ไม่ตัดสินข้อกำกวมของ spec แทนผู้สอน
3. Parent weight 0.5 คงค่าจาก C และระบุใน report ต้องตกลงใช้ในการรับมอบ
4. Subset 127 เทียบเป้าหมาย 30–50 ยังไม่เปลี่ยน
5. Semantic grounding/negation/ambiguity/confidence และ quality gates เป็นงาน A/B ถัดไป
6. /evaluate จำกัด dataset แต่ยังอยู่ใน local app ที่ไม่มี auth/rate limit; deployment controls ยังเป็นงานแยก

ขอบเขต integration ทำให้วัดระบบได้แล้ว ไม่ใช่คำรับรองว่าโมเดลหรือโครงการทั้งหมดถูกต้อง 100%
