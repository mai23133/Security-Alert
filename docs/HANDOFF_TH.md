# เอกสารส่งต่องาน Security-Alert

อัปเดต: 3 สิงหาคม 2026
สถานะ: พร้อมเริ่มพัฒนาต่อ โดยมีงาน Week 2 ค้างอยู่

## โปรเจกต์นี้ทำอะไร

Security-Alert รับข้อความ Security Alert แล้วช่วยเสนอ MITRE ATT&CK Technique ที่อาจเกี่ยวข้องให้ analyst ตรวจสอบต่อ ผลลัพธ์เป็นเพียงคำแนะนำ ไม่ใช่การ block, response หรือสั่งงาน SOC อัตโนมัติ

เป้าหมายสุดท้ายคือให้ระบบคืน Technique 1–3 รายการ พร้อม confidence, หลักฐานที่ตัดมาจากข้อความ alert และธง `needs_human_review`.

## สถานะปัจจุบันแบบสั้น

| ส่วน | สถานะ | ความหมาย |
| --- | --- | --- |
| Repository / setup | พร้อม | Git สะอาด, มี README และ conda environment `sec-alert311` |
| MITRE knowledge base | พร้อม | มี STIX Enterprise ATT&CK เวอร์ชันที่ตรึงไว้ `19.1` และไฟล์ processed |
| Taxonomy API | ใช้งานได้ | ดูรายการ Technique ในขอบเขตและค้นหาราย ID ได้ |
| `/alerts/infer` | ยังเป็น stub ที่ปลอดภัย | รับ request ได้ แต่คืน no-match และให้คนตรวจเสมอ |
| Retrieval / RAG | ยังไม่เริ่ม | `embedder.py` และ `retriever.py` ยังว่าง |
| LLM inference และ evidence | ยังไม่เริ่มจริง | ไฟล์ inferencer, evidence linker และ grounding judge ยังว่าง |
| Evaluation / CI / deploy | ยังไม่เริ่ม | ยังไม่มี dataset, metrics, CI และ production guardrails |

ผลตรวจล่าสุดที่รันได้ในเครื่องนี้:

```text
conda run -n sec-alert311 python -m pytest -q
17 passed
```

## สิ่งที่ทำเสร็จแล้ว

- ใช้ MITRE ATT&CK Enterprise STIX `enterprise-attack-19.1` เป็นแหล่งข้อมูลหลัก
- จำกัดขอบเขตไว้ที่ tactics: `initial-access`, `execution`, `credential-access` และ platforms Windows/Linux
- ตัด Technique ที่ deprecated หรือ revoked ก่อนนำมาเป็น candidate
- สร้าง API ที่มีแล้ว:
  - `GET /`
  - `GET /taxonomy/techniques`
  - `GET /taxonomy/techniques/{technique_id}`
  - `POST /alerts/infer`
- ทุก API response มี header ระบุ STIX version
- มี disclaimer ว่าเป็น advisory และต้องให้ senior analyst ตรวจ
- มี automated tests สำหรับ schema, STIX ingestion, taxonomy และ no-match API

## ข้อควรเข้าใจก่อนเริ่มต่อ

`POST /alerts/infer` ยัง **ไม่วิเคราะห์จริง** แม้จะรับ alert ได้สำเร็จ: ผลลัพธ์จะเป็นรายการว่าง และ `needs_human_review=true` เสมอ นี่เป็นการออกแบบชั่วคราวเพื่อป้องกันการเดา Technique โดยไม่มีหลักฐาน

มีโค้ด Gemini สำหรับ alert parser และ tactic router อยู่แล้ว แต่ยังไม่ถูกเชื่อมกับ API และยังไม่มี timeout, retry, การจัดการ error, การบังคับ structured output หรือ test แบบ mock จึงยังไม่ควรนำไปใช้จริง

## งานที่ต้องทำก่อน: ปิด Week 2

แม้วันที่ปัจจุบันเข้าสู่ Week 3 แล้ว แต่ Week 2 ยังไม่มี implementation จึงควรทำตามลำดับนี้ก่อน

### 1. แก้ชื่อฟิลด์ schema ให้ตรงข้อกำหนด

ข้อกำหนดหลักต้องการ `tactic: str` ทั้งใน `TechniqueCandidate` และ `InferredTechnique`

ผลกระทบ: schema, JSON output และ API response ต้องใช้ชื่อฟิลด์เดียวกัน เพื่อให้ผู้ใช้ API ที่อ้างอิงข้อกำหนดอ่านค่า tactic ได้อย่างถูกต้อง

ไฟล์ที่เกี่ยวข้อง:

- `src/schemas.py`
- `src/rag/ingest_stix.py`
- `src/api/routes/taxonomy.py`
- tests ที่ใช้ field `tactic`
- `data/processed/technique_candidates.json` (ต้อง regenerate หลังแก้)

### 2. ตัดสินใจ embedding backend และรูปแบบ index

ให้บันทึกเหตุผลและวิธีทำซ้ำใน decision note ก่อนลงมือ เพื่อให้ผล retrieval reproducible โดยไม่เปลี่ยนไปตามบริการภายนอกโดยไม่ตั้งใจ

สิ่งที่ index ต้องเก็บอย่างน้อย: Technique ID, name, description excerpt, tactics, platform, source และ STIX version

### 3. ทำ RAG retrieval

เริ่มที่:

- `src/rag/embedder.py`
- `src/rag/retriever.py`

Retriever ต้องรับข้อความ alert, filter ตาม tactic ได้ และคืน top-k เฉพาะจาก pinned ATT&CK subset เท่านั้น ห้ามสร้างหรือคืน ID ที่ไม่มีใน `data/processed/technique_ids.json`.

### 4. เขียน test และ Recall@k baseline

เพิ่ม test ให้ครอบคลุมการ filter, top-k, ID ที่อนุญาต และผลลัพธ์ซ้ำได้ จากนั้นบันทึก Recall@1, Recall@3 และ Recall@5 baseline

## งานหลัง Retrieval พร้อม

ลำดับ pipeline ที่ต้องทำคือ:

```text
Alert Parser → Tactic Router → Technique Retriever → Technique Inferencer
→ Evidence Linker → Grounding Judge → API response
```

- Inferencer เลือกได้ 1–3 Technique จาก candidates ที่ retriever คืนมาเท่านั้น
- Evidence linker ต้องชี้กลับไปยังข้อความจริงใน alert
- Grounding judge ต้องปฏิเสธ ID ที่ไม่อยู่ใน subset หรือไม่มี evidence
- เคสกำกวม, low confidence และ no-match ต้องตั้ง `needs_human_review=true`

หลังจากนั้นจึงเชื่อม pipeline เข้า `/alerts/infer` พร้อม mock tests โดยไม่เรียก Gemini จริง

## เงื่อนไขที่ห้ามละเมิด

- ใช้เฉพาะ MITRE Enterprise ATT&CK `19.1` ที่ pin ไว้ใน repository
- ห้ามสร้าง Technique ID เอง หรือคืน ID นอก subset
- Alert text เป็น untrusted input และอาจมี prompt injection
- ผลลัพธ์เป็น advisory เท่านั้น ห้ามทำ automated response
- อย่า commit `.env`, API key, raw alert หรือข้อมูลระบุตัวตนที่ยังไม่ sanitize

## คำสั่งเริ่มงาน

```bash
cd /home/mai/Security-Alert
conda run -n sec-alert311 python -m pytest -q
conda run -n sec-alert311 python -m uvicorn src.api.main:app --reload
```

เปิด API docs ได้ที่ `http://127.0.0.1:8000/docs`

ก่อนแก้โค้ด ให้เริ่มจากอ่าน `security-alert-attack-technique-inference.md` เพราะเป็น Source of Truth ของโปรเจกต์

## ไฟล์สำคัญ

| ความต้องการ | ไฟล์ |
| --- | --- |
| ข้อกำหนดหลัก | `security-alert-attack-technique-inference.md` |
| ตารางงานรายสัปดาห์ | `docs/WORK_PLAN_TH.md` |
| รายงานสถานะเดิม | `docs/PROJECT_REVIEW_TH.md` |
| schema | `src/schemas.py` |
| STIX ingestion | `src/rag/ingest_stix.py` |
| Retrieval ที่ต้องเริ่มทำ | `src/rag/embedder.py`, `src/rag/retriever.py` |
| API infer ปัจจุบัน | `src/api/routes/alerts.py` |
| ATT&CK data | `data/raw/enterprise-attack-19.1.json` |

## เป้าหมายของ PR ถัดไป

"ใช้ schema `tactic` ตามข้อกำหนด และมี deterministic retriever พร้อม tests + Recall@k baseline"

เมื่อ PR นี้เสร็จ จึงถือว่าปิดงาน Week 2 และพร้อมเริ่มส่วน inference/evidence/grounding ของ Week 3 อย่างถูกลำดับ
