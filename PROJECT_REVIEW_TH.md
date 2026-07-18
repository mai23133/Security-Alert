# รายงานรีวิวโปรเจกต์ Security-Alert

วันที่ตรวจ: 18 กรกฎาคม 2026  
Branch/Commit: `main` ที่ `331368b` (`week3_api`)

## 1. สรุปสำหรับผู้บริหาร

โปรเจกต์นี้มีเป้าหมายรับข้อความ Security Alert แล้วแนะนำ MITRE ATT&CK Technique ที่เกี่ยวข้องในลักษณะ advisory เพื่อช่วยนักวิเคราะห์ SOC ไม่ใช่สั่งตอบสนองเหตุการณ์โดยอัตโนมัติ

สถานะปัจจุบันอยู่ประมาณ **MVP ช่วงต้น (งาน Week 2–3)** โครงข้อมูล MITRE, Pydantic schema, FastAPI, Alert Parser และ Tactic Router ถูกเริ่มทำแล้ว แต่ผลลัพธ์จาก endpoint หลักยังเป็น mock และ pipeline ส่วน RAG/inference/evidence/grounding/evaluation/UI ยังไม่ถูกพัฒนา ดังนั้นระบบยังไม่พร้อมใช้จริงหรือ deploy production

ภาพรวมความพร้อมโดยประมาณ:

| ส่วน | สถานะ | หมายเหตุ |
|---|---|---|
| MITRE ATT&CK dataset | ทำแล้วระดับต้น | pin Enterprise ATT&CK 19.1 และกรองข้อมูลแล้ว |
| Data schema | ทำแล้วระดับต้น | มี validation ของ technique ID และ confidence |
| Alert parsing | มี implementation | พึ่ง Google Gemini และยังไม่มี test/error handling ที่เพียงพอ |
| Tactic routing | มี implementation | จำกัด 3 tactics และมี fallback |
| Taxonomy API | มี implementation | list/detail จากไฟล์ processed |
| Inference API | เป็น stub | parse/route จริง แต่ technique ที่ตอบกลับ hard-code |
| Retriever/RAG | ยังไม่ทำ | ไฟล์ว่าง |
| Technique inference | ยังไม่ทำ | ไฟล์ว่าง |
| Evidence/grounding | ยังไม่ทำ | ไฟล์ว่าง |
| Evaluation | ยังไม่ทำ | ไฟล์และ dataset directory ว่าง |
| Automated tests | ยังไม่ทำ | pytest พบ 0 tests |
| UI | ยังไม่ทำ | directory ว่าง |
| Production/DevOps docs | ยังไม่ทำ | ไม่มี README, Dockerfile, CI, lock file และ `.gitignore` |

## 2. สิ่งที่ทำไปแล้ว

### 2.1 ข้อมูลและ schema

- เก็บ MITRE Enterprise ATT&CK STIX 2.1 เวอร์ชัน 19.1 ที่ `data/raw/enterprise-attack-19.1.json`
- raw bundle มี 25,843 STIX objects และมีขนาดประมาณ 53 MB
- สคริปต์ `src/rag/ingest_stix.py` กรองเฉพาะ:
  - tactics: `initial-access`, `execution`, `credential-access`
  - platforms: Windows หรือ Linux
  - ไม่รวม deprecated/revoked technique
- มี processed candidate 127 รายการ ไม่มี technique ID ซ้ำ แบ่งเป็น:
  - credential-access 58
  - execution 48
  - initial-access 21
- มี schema หลักใน `src/schemas.py`: `ParsedAlert`, `TechniqueCandidate`, `InferredTechnique`, `ATTACKInferenceResult`
- validation รองรับ technique และ sub-technique รูปแบบ `T####` และ `T####.###` รวมทั้งบังคับ confidence ให้อยู่ในช่วง 0–1

### 2.2 Agent ที่มีโค้ดแล้ว

- `alert_parser.py` เรียก Google Gemini เพื่อแปลง narrative เป็น assets, observed actions และ IOCs
- `tactic_router.py` เรียก Google Gemini เพื่อเลือก tactic ใน scope 3 รายการ
- ทั้งสองส่วนพยายามตัด Markdown code fence และ parse JSON
- router กรองค่าที่อยู่นอก scope และ fallback เป็นทั้ง 3 tactics หากโมเดลไม่คืนค่าที่ใช้ได้

### 2.3 API ที่มีแล้ว

- FastAPI application เวอร์ชัน `0.1.0`
- `GET /` health response
- `GET /taxonomy/techniques` สำหรับ list และ filter ตาม tactic
- `GET /taxonomy/techniques/{technique_id}` สำหรับดูรายละเอียด
- `POST /alerts/infer` รับ alert ID/narrative และเรียก parser/router
- ทุก response ถูกตั้ง header `X-MITRE-ATTaCK-Version: enterprise-attack-19.1`
- เปิด CORS middleware แล้ว

### 2.4 ประวัติ Git

มี 2 commits:

1. `18735bb` — เริ่ม schema, STIX ingestion และวางโครงไฟล์ส่วนต่าง ๆ
2. `331368b` — เพิ่ม Week 3 API, Alert Parser, Tactic Router และ dependencies

## 3. สิ่งที่ยังเหลือ

### ความสำคัญสูงสุด: ทำให้ผล inference เป็นของจริง

1. ทำ `src/rag/embedder.py` เพื่อสร้าง embedding/index ของ technique candidates
2. ทำ `src/rag/retriever.py` เพื่อค้น candidate ตาม parsed alert และ tactic
3. ทำ `src/agents/technique_inferencer.py` เพื่อให้คะแนน/เลือก technique จาก candidate ที่ค้นมา
4. ทำ `src/agents/evidence_linker.py` เพื่อผูกทุก prediction กับข้อความหลักฐานจาก input จริง
5. ทำ `src/agents/grounding_judge.py` เพื่อตรวจว่า ID, tactic, evidence และคำอธิบาย grounded กับ MITRE/input
6. เปลี่ยน mock ใน `POST /alerts/infer` ให้เป็น pipeline จริงตั้งแต่ parse ถึง judge
7. กำหนดเกณฑ์ `needs_human_review` จาก confidence/grounding/evidence ไม่ใช่เพียงตรวจว่ารายการผลลัพธ์ว่างหรือไม่

### คุณภาพและการประเมินผล

- เขียน unit tests สำหรับ schemas, parser, router, ingestion และ API
- mock Gemini ใน test เพื่อให้ test deterministic และไม่เสีย quota
- เพิ่ม integration test ของ inference pipeline
- สร้าง labeled evaluation dataset ใน `data/eval/`
- ทำ `eval/metrics.py` เช่น precision, recall, F1, top-k recall, tactic accuracy, evidence/grounding score และ abstention/review rate
- ทำ `eval/run_eval.py` พร้อมบันทึก model/prompt/dataset/STIX version เพื่อให้ผลทำซ้ำได้
- เติม prompt files ใน `prompts/v1/` และให้โค้ดโหลด prompt จากไฟล์ แทน prompt ที่ hard-code อยู่ใน source

### API และความทนทาน

- validate ว่า narrative ไม่ว่างและกำหนดความยาวสูงสุด
- แยก error ของ invalid model output, timeout, quota/rate limit และ provider failure ไม่ควรคืนรายละเอียด exception ดิบให้ client
- เพิ่ม timeout, retry แบบจำกัด, structured logging และ request/correlation ID
- รองรับ configuration ผ่าน settings object และตรวจ environment ตอน startup
- เพิ่ม authentication/rate limiting หากเปิดใช้นอกเครื่อง
- จำกัด CORS origins สำหรับ production
- ทำ API ของ evaluation (`src/api/routes/evaluate.py`) หรือเอาไฟล์ออกจนกว่าจะใช้
- ใช้ absolute path ที่อิง project/package location เพื่อไม่ให้ API พังเมื่อรันจาก working directory อื่น

### Documentation, UI และการ deploy

- สร้าง README: เป้าหมาย, architecture, setup, env vars, run/test/eval commands และตัวอย่าง request/response
- ทำหน้า UI ใน `ui/` หากยังอยู่ใน scope
- เพิ่ม `.gitignore`, Dockerfile/compose ตามรูปแบบ deploy, CI และ dependency lock/pinning
- เพิ่ม LICENSE และ MITRE ATT&CK attribution ที่เห็นได้ในเอกสาร/หน้า UI ไม่พึ่ง response header อย่างเดียว
- กำหนด policy การเก็บ alert ซึ่งอาจมี IP, hostname, account หรือข้อมูลอ่อนไหว

## 4. ประเด็นและความเสี่ยงที่พบ

### Critical — ความลับถูก track ใน Git

ไฟล์ `.env` อยู่ใน Git repository ขณะที่ `.env.example` ว่างและไม่มี `.gitignore` ต้องถือว่าค่าความลับในไฟล์ดังกล่าวอาจรั่วแล้ว: revoke/rotate key, ลบ `.env` ออกจาก tracking, เติม `.gitignore` และใส่เฉพาะชื่อ environment variables ที่ไม่มีค่า secret ใน `.env.example` หาก repository เคยถูกแชร์หรือ push แล้ว ควรพิจารณาล้าง secret จาก Git history ด้วย

### High — endpoint หลักคืนผล mock ที่อาจทำให้ผู้ใช้เข้าใจผิด

`POST /alerts/infer` คืน T1110 และ candidate T1059.001 แบบ hard-code โดยไม่ใช้ผล tactic routing ในการสร้างผลสุดท้าย จึงสามารถคืน technique ที่ไม่สัมพันธ์กับ alert ได้ ควรระบุ response ว่าเป็น stub อย่างชัดเจนหรือปิด endpoint นี้จากผู้ใช้จริงจนกว่า pipeline จะเสร็จ

### High — ไม่มี automated test/evaluation

ไฟล์ test ทั้งสองไฟล์ว่าง และการรัน pytest รายงาน `no tests ran` จึงยังไม่มี regression safety net และยังไม่มีหลักฐานเชิงตัวเลขว่าการ map ATT&CK ถูกต้องเพียงใด

### High — LLM integration ยังเปราะ

- model name ถูก hard-code และไม่มี startup validation
- parse JSON จากข้อความโดยตรง ไม่มี schema-constrained generation
- ไม่มี timeout/retry/error classification
- ไม่มีการป้องกัน prompt injection จาก narrative อย่างชัดเจน
- exception ถูกส่งกลับ client ผ่าน `detail=str(e)` ซึ่งอาจเปิดเผยข้อมูลภายใน
- ไม่มี deterministic fallback parser สำหรับ IOC พื้นฐาน

### Medium — ingestion output path ไม่ตรงกับไฟล์ที่ API ใช้

สคริปต์ ingestion เขียน `technique_ids.json` และ `technique_candidates.json` ที่ working directory ปัจจุบัน แต่ API อ่าน `data/processed/technique_candidates.json` ทำให้การ regenerate ตามสคริปต์ไม่อัปเดตข้อมูลที่ API ใช้ตามที่คาด

### Medium — technique ที่อยู่ได้หลาย tactic ถูกลดเหลือ tactic เดียว

`to_candidate()` เลือก tactic แรกหลัง sort แม้ STIX object เดียวอาจอยู่หลาย tactic ทำให้สูญเสียความสัมพันธ์ และจำนวนราย tactic อาจไม่สะท้อน ATT&CK จริง ควรเปลี่ยน schema เป็น `tactics: list[str]` หรือสร้าง record ต่อ technique-tactic โดยมีวิธี deduplicate ชัดเจน

### Medium — dependency และ repository hygiene

- dependencies ใช้ lower bounds (`>=`) ไม่มี lock จึง build ซ้ำแล้วอาจได้พฤติกรรมต่างกัน
- ไม่มี `.gitignore` และมี `__pycache__`/`.pyc` ถูก commit แล้ว
- raw STIX ขนาดใหญ่ถูกเก็บตรงใน Git ทำให้ repository หนัก ควรพิจารณาสคริปต์ดาวน์โหลดพร้อม checksum, release asset หรือ Git LFS
- ไม่มี README หรือคำสั่ง setup ที่ทำซ้ำได้

### Medium — runtime verification ยังไม่ครบ

ตรวจ syntax ด้วย `compileall` แล้วผ่าน แต่ environment ที่ใช้รีวิวไม่มี FastAPI ติดตั้ง จึง import/run TestClient ไม่ได้ และยังไม่ได้ทดสอบ Gemini แบบ live เพราะต้องใช้ external API key การมี requirements ไม่ได้ยืนยันว่า runtime ใช้งานได้จนกว่าจะสร้าง clean environment แล้ว install/run smoke test

### Low/Medium — validation และ API semantics

- `AlertRequest.narrative` ยอมรับข้อความว่าง
- filter tactic ที่ไม่รู้จักจะคืนรายการว่างแทน 400
- CORS เปิด `*` ทุก origin/method/header
- taxonomy โหลดและ parse JSON ใหม่ทุก request ซึ่งยังพอรับได้ที่ 127 รายการ แต่ควร cache ตอน startup หากโตขึ้น

## 5. แผนงานแนะนำ

### Phase 0 — Security และ reproducibility

- rotate secret และหยุด track `.env`
- เพิ่ม `.gitignore` และเอา generated bytecode ออกจาก Git
- สร้าง README และ clean environment จาก requirements/lock file
- แก้ ingestion output path พร้อม test

### Phase 1 — Retrieval MVP

- เลือก embedding backend และ index format
- index candidate 127 รายการพร้อม metadata ของทุก tactic/platform/source
- ทำ top-k retrieval โดยมี tactic filter
- เพิ่ม retrieval tests และ top-k recall evaluation

### Phase 2 — Grounded inference

- ทำ inferencer, evidence linker และ grounding judge
- ใช้ structured output/schema validation
- กำหนด confidence calibration และ human-review thresholds
- ห้าม technique ที่ไม่อยู่ใน retrieved/pinned ATT&CK subset หลุดสู่ผลลัพธ์

### Phase 3 — API quality และ evaluation

- ต่อ pipeline จริงเข้ากับ `/alerts/infer`
- เพิ่ม unit/integration/API tests และ CI
- สร้าง evaluation set ที่ครอบคลุม positive, multi-technique, ambiguous และ no-match alerts
- บันทึกและเปรียบเทียบผลตาม prompt/model version

### Phase 4 — UI และ production hardening

- ทำ UI ที่แสดง prediction, confidence, evidence, MITRE link และปุ่ม analyst review
- เพิ่ม auth, rate limit, observability, privacy/retention controls
- package/deploy และทำ acceptance/security testing

## 6. Definition of Done ที่แนะนำสำหรับ MVP

MVP ควรถือว่าเสร็จเมื่อ:

- clean install และ start server ได้จาก README เพียงชุดคำสั่งเดียว
- `/alerts/infer` ไม่มี mock/hard-code และทุก prediction มาจาก pinned ATT&CK subset
- ทุก prediction มี evidence span ที่ตรวจย้อนกลับไปยัง input ได้
- invalid/ambiguous/no-match input ส่งเข้า human review อย่างเหมาะสม
- มี unit/integration tests ใน CI และไม่มี test ที่ต้องเรียก Gemini จริง
- มี evaluation report และเกณฑ์ขั้นต่ำที่ทีมตกลงกัน
- secret ไม่อยู่ใน repository และ production config ไม่เปิด CORS แบบ wildcard
- MITRE attribution, advisory disclaimer และข้อจำกัดของระบบแสดงต่อผู้ใช้ชัดเจน

## 7. ผลการตรวจที่ทำในรอบนี้

- ตรวจไฟล์ source, prompts, tests, eval, data และ Git history ทั้ง repository
- `python -m compileall -q src eval tests`: ผ่าน (ไม่พบ syntax error)
- `python -m pytest -q`: ไม่พบ test ให้รัน
- runtime API smoke test: ยังทำไม่ได้เพราะ environment ปัจจุบันไม่มี package `fastapi`
- ไม่ได้เรียก Gemini live และไม่ได้แก้ไข source code ของระบบ

ข้อสรุป: ฐานของ Week 2–3 มีทิศทางชัดเจน แต่จุดที่สร้างคุณค่าหลัก—retrieval, inference, evidence grounding และ measurable evaluation—ยังเหลือทั้งหมด ควรเริ่มจากแก้ secret/repository hygiene แล้วทำ end-to-end vertical slice ที่มี test ก่อนขยาย UI หรือ production deployment
