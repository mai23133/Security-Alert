# รายงานรีวิวโปรเจกต์ Security-Alert

วันที่ตรวจ: 21 กรกฎาคม 2026  
Branch/Commit ที่ตรวจ: `mai-work` ที่ `e43cbec` (`Update setup docs and Gemini SDK`)  
หมายเหตุ: มี local changes ที่ยังไม่ commit/push ใน `WORK_PLAN_TH.md`, `src/api/routes/taxonomy.py`, `src/rag/ingest_stix.py` และ tests บางไฟล์

## 1. สรุปสถานะล่าสุด

Security-Alert ยังอยู่ในสถานะ **early MVP / Week 1 เสร็จตามการตรวจรับของเจ้าของโปรเจกต์** และกำลังพร้อมเข้าสู่ Week 2 ซึ่งเป็นช่วงเริ่มทำ RAG/retrieval จริง

ระบบตอนนี้ทำได้แล้วในระดับโครงหลัก:

- มี FastAPI backend
- มี MITRE ATT&CK Enterprise 19.1 raw dataset
- มี processed ATT&CK candidate subset สำหรับ 3 tactics
- มี schema validation
- มี Alert Parser และ Tactic Router ที่เรียก Google Gemini ผ่าน SDK ใหม่ `google-genai`
- มี taxonomy API สำหรับ list/detail technique
- มี README/setup docs ล่าสุดสำหรับ conda env `sec-alert311`
- มี `.gitignore` และ `.env.example`
- มี unit tests ขั้นต้นบางส่วนใน local

ข้อจำกัดสำคัญยังเหมือนเดิม: **RAG/retrieval, technique inference, evidence linking และ grounding ยังไม่ได้ implement** ดังนั้น `/alerts/infer` ยังไม่ใช่ inference pipeline จริง และยังคืน technique แบบ stub/hard-code

## 2. ภาพรวมความพร้อม

| ส่วน | สถานะล่าสุด | หมายเหตุ |
|---|---|---|
| Repository hygiene | ดีขึ้นมาก | มี `.gitignore`, `.env` ไม่ถูก track, `.env.example` มี `GOOGLE_API_KEY=` |
| README/setup | ทำแล้ว | มีวิธีติดตั้งจากศูนย์ด้วย conda `sec-alert311` และ `venv` |
| Dependencies | ทำแล้วระดับต้น | เปลี่ยนเป็น `google-genai`; ยังไม่มี lock file แบบ strict |
| MITRE ATT&CK dataset | ทำแล้วระดับต้น | pin Enterprise ATT&CK 19.1 |
| STIX ingestion | ทำแล้วบางส่วน | local แก้ output path ไป `data/processed/` แล้ว แต่ยังไม่ push |
| Data schema | ทำแล้วระดับต้น | validate technique ID และ confidence |
| Alert parsing | มี implementation | เรียก Gemini ผ่าน `google-genai`; ยังไม่มี structured output/retry/timeout |
| Tactic routing | มี implementation | จำกัด 3 tactics และ fallback เป็นทั้ง 3 tactics |
| Taxonomy API | มี implementation | local แก้ path ให้ project-root based แล้ว แต่ยังไม่ push |
| Inference API | ยังเป็น stub | parse/route จริง แต่ final technique ยัง hard-code T1110 |
| RAG / Retriever | ยังไม่เริ่มจริง | `embedder.py` และ `retriever.py` ยังว่าง |
| Technique inference | ยังไม่เริ่มจริง | `technique_inferencer.py` ยังว่าง |
| Evidence linking | ยังไม่เริ่มจริง | `evidence_linker.py` ยังว่าง |
| Grounding judge | ยังไม่เริ่มจริง | `grounding_judge.py` ยังว่าง |
| Evaluation | ยังไม่เริ่มจริง | `eval/metrics.py` และ `eval/run_eval.py` ยังไม่มี implementation ที่ใช้ได้ |
| Automated tests | ทำแล้วบางส่วนใน local | schema/ingestion tests ผ่าน; taxonomy API tests ยังรันค้าง |
| UI | ยังไม่เริ่ม | `ui/` ยังไม่มี workflow |
| CI/Deploy | ยังไม่เริ่ม | ยังไม่มี CI, Dockerfile, release process |

## 3. สิ่งที่ทำเพิ่มจากรีวิวรอบก่อน

### 3.1 Repository hygiene และ setup

- เพิ่ม `.gitignore` เพื่อ ignore:
  - `.env`, `.env.*`
  - virtual environments
  - `__pycache__`, `.pyc`
  - pytest/cache/coverage files
  - editor files
  - `data/processed/`
- เพิ่ม `.env.example` พร้อม key placeholder:
  - `GOOGLE_API_KEY=`
- เพิ่ม README ภาษาไทยพร้อม:
  - ภาพรวมโปรเจกต์
  - วิธีติดตั้งด้วย conda `sec-alert311`
  - วิธีติดตั้งด้วย `venv`
  - วิธีตั้งค่า Gemini API key
  - วิธี regenerate ATT&CK processed data
  - วิธีรัน API
  - ตัวอย่าง `curl`
  - สถานะล่าสุดของ tests และข้อจำกัด

### 3.2 เปลี่ยน Gemini SDK

โค้ดเดิมใช้:

- `google-generativeai`
- `google.generativeai.GenerativeModel`

โค้ดล่าสุดเปลี่ยนมาใช้:

- `google-genai`
- `from google import genai`
- wrapper ใหม่ที่ `src/agents/gemini_client.py`

`alert_parser.py` และ `tactic_router.py` เรียกผ่าน helper `generate_text()` แล้ว ทำให้การเรียก Gemini รวมศูนย์ขึ้นกว่าเดิม

### 3.3 Dependencies ล่าสุด

`requirements.txt` ตอนนี้ระบุ dependency หลัก:

- `google-genai>=2.12.1`
- `fastapi>=0.139.2`
- `uvicorn>=0.51.0`
- `pydantic>=2.13.4`
- `python-dotenv>=1.2.2`
- `pytest>=9.1.1`
- `httpx>=0.28.1`

ตรวจใน conda env `sec-alert311` ได้:

- Python `3.11.15`
- `google-genai 2.12.1`
- `fastapi 0.139.2`
- `uvicorn 0.51.0`
- `pydantic 2.13.4`
- `python-dotenv 1.2.2`
- `pytest 9.1.1`
- `httpx 0.28.1`

### 3.4 Work plan

เจ้าของโปรเจกต์ตรวจรับ Week 1 แล้ว และ `WORK_PLAN_TH.md` ใน local ถูกอัปเดตให้ Week 1 เป็น `เสร็จแล้ว` ทั้ง 5 รายการ:

- secret / `.env`
- `.gitignore` และ generated files
- STIX ingestion output path
- README และ dependencies
- test ขั้นต้น

หมายเหตุ: การแก้ `WORK_PLAN_TH.md` ยังเป็น local change ยังไม่ได้ push

## 4. สถานะ RAG / Retrieval ตอนนี้

### 4.1 สิ่งที่มีแล้ว

มีฐานข้อมูล candidate สำหรับ retrieval ในรูปแบบ JSON จาก MITRE ATT&CK subset:

- `data/raw/enterprise-attack-19.1.json`
- `data/processed/technique_ids.json`
- `data/processed/technique_candidates.json`

candidate ถูก filter จาก:

- tactics: `initial-access`, `execution`, `credential-access`
- platforms: Windows, Linux
- ตัด deprecated/revoked technique

จากรีวิวรอบก่อน candidate มี 127 รายการ:

- `credential-access`: 58
- `execution`: 48
- `initial-access`: 21

### 4.2 สิ่งที่ยังไม่มี

ยังไม่มี RAG จริงในความหมายของ retrieval augmented generation:

- ยังไม่มี embedding model/backend
- ยังไม่มี vector index หรือ lexical index
- ยังไม่มี chunking/normalization strategy สำหรับ technique candidate text
- ยังไม่มี `top-k` retrieval
- ยังไม่มี tactic-aware retrieval
- ยังไม่มี ranking/scoring
- ยังไม่มี evaluation เช่น top-k recall

ไฟล์ที่เกี่ยวข้องยังว่าง:

- `src/rag/embedder.py`
- `src/rag/retriever.py`

### 4.3 ข้อเสนอสำหรับ Week 2

Week 2 ควรเริ่มจาก retrieval MVP ที่ deterministic ก่อนต่อ LLM inference:

1. ตัดสินใจ embedding backend
   - ทางเลือกเบา: lexical/BM25 ก่อน เพื่อไม่ต้องพึ่ง external embedding API
   - ทางเลือก semantic: local sentence-transformers หรือ Gemini embeddings
2. นิยาม candidate text ที่จะ embed/index เช่น:
   - technique ID
   - technique name
   - tactic
   - description excerpt
   - platforms
3. สร้าง index artifact ที่ reproduce ได้
4. ทำ `retrieve_candidates(parsed_alert, tactics, top_k)`
5. เขียน tests ให้รับประกันว่า:
   - ไม่คืน technique นอก pinned subset
   - filter tactic ได้
   - top-k คงที่กับ fixture
6. ทำ baseline evaluation เล็ก ๆ สำหรับ alerts ตัวอย่าง

## 5. สถานะ API ตอนนี้

### 5.1 Endpoints ที่มี

- `GET /`
  - health check
  - คืน `{"status": "ok", "stix_version": "19.1"}`
- `GET /taxonomy/techniques`
  - list candidate techniques
  - filter ด้วย query param `tactic`
- `GET /taxonomy/techniques/{technique_id}`
  - ดึง technique รายตัว
- `POST /alerts/infer`
  - รับ `alert_id` และ `narrative`
  - เรียก parser/router จริง
  - คืน inference result แบบ stub

ทุก response มี header:

```text
X-MITRE-ATTaCK-Version: enterprise-attack-19.1
```

### 5.2 ข้อจำกัด API

- `/alerts/infer` ยังคืน `T1110` แบบ hard-code
- ยังไม่ใช้ผล `tactics` เพื่อเลือก technique จริง
- ยังไม่มี validation ว่า narrative ห้ามว่าง
- ยังไม่มี max length
- ยังคืน `detail=str(e)` เมื่อ provider/model error
- CORS ยังเปิด `*`
- ยังไม่มี auth/rate limit
- ยังไม่มี request ID / structured logging

## 6. สถานะ Tests

### 6.1 Tests ที่มีใน local

มี test files เพิ่มใน local:

- `tests/test_schemas.py`
- `tests/test_ingest_stix.py`
- `tests/test_taxonomy_api.py`
- `tests/__init__.py`

### 6.2 ผลที่รันล่าสุด

รันใน conda env `sec-alert311`:

```bash
conda run -n sec-alert311 python -m compileall -q src eval tests
```

ผล: ผ่าน

รันเฉพาะ schema และ ingestion:

```bash
conda run -n sec-alert311 python -m pytest tests/test_schemas.py tests/test_ingest_stix.py -q
```

ผล:

```text
8 passed in 0.10s
```

รัน taxonomy API tests:

```bash
conda run -n sec-alert311 python -m pytest tests/test_taxonomy_api.py -q
```

ผล: ค้างเกิน 60 วินาทีและถูกหยุดด้วย `Ctrl+C`

### 6.3 ความหมายของสถานะ test

- schema และ ingestion มี regression safety net ขั้นต้นแล้ว
- taxonomy API test ยังต้อง debug ต่อ
- ยังไม่มี tests สำหรับ parser/router ที่ mock Gemini
- ยังไม่มี integration test สำหรับ `/alerts/infer`
- ยังไม่มี RAG/retrieval tests เพราะ RAG ยังไม่ถูก implement

## 7. ความเสี่ยงหลักล่าสุด

### High — `/alerts/infer` ยังเป็น stub

Endpoint หลักยังคืน technique hard-code ทำให้ยังไม่ควรใช้เป็นผลวิเคราะห์จริง ควรขึ้น label ชัดเจนว่าเป็น demo/stub จนกว่า retrieval/inference/evidence/grounding จะเสร็จ

### High — RAG ยังไม่มี implementation

แม้มีไฟล์ `embedder.py` และ `retriever.py` แต่ยังว่างทั้งหมด จึงยังไม่มีระบบ retrieve candidate จาก ATT&CK subset ตาม alert จริง

### High — Gemini output ยัง parse แบบเปราะ

parser/router ยัง parse JSON จากข้อความ LLM โดยตรง แม้มีการตัด code fence แล้ว แต่ยังไม่มี:

- schema-constrained generation
- retry
- timeout
- error classification
- fallback parser สำหรับ IOC พื้นฐาน
- prompt-injection hardening

### Medium — local changes ยังไม่ถูก push

งานบางส่วนที่เกี่ยวกับ Week 1 ยังอยู่ใน working tree:

- `WORK_PLAN_TH.md`
- `src/api/routes/taxonomy.py`
- `src/rag/ingest_stix.py`
- `tests/test_schemas.py`
- `tests/__init__.py`
- `tests/test_ingest_stix.py`
- `tests/test_taxonomy_api.py`

ควร commit/push หรือแยก branch ให้ชัดก่อนเริ่ม Week 2 เพื่อลดความสับสน

### Medium — taxonomy API tests ค้าง

การค้างของ `tests/test_taxonomy_api.py` ต้อง debug ก่อนถือว่า test suite พร้อมใช้งานจริง

### Medium — technique หลาย tactic ยังถูกลดเหลือ tactic เดียว

`to_candidate()` ยังเลือก tactic แรกหลัง sort หาก STIX object อยู่ได้หลาย tactic ทำให้ข้อมูลสูญหาย ควรแก้ schema เป็น `tactics: list[str]` หรือสร้าง record ต่อ technique-tactic

### Medium — ยังไม่มี lock file

`requirements.txt` ใช้ lower bounds (`>=`) ทำให้ clean install ในอนาคตอาจได้ version ใหม่กว่าที่ตรวจวันนี้ ควรเพิ่ม lock file เมื่อเริ่มต้องการ reproducibility จริง

## 8. สิ่งที่ควรทำถัดไป

ลำดับที่แนะนำ:

1. Commit/push local Week 1 changes ที่ยอมรับแล้ว
2. Debug `tests/test_taxonomy_api.py` ที่ค้าง
3. ตัดสินใจ retrieval backend สำหรับ Week 2
4. Implement `src/rag/embedder.py`
5. Implement `src/rag/retriever.py`
6. เพิ่ม retrieval tests และ baseline recall
7. ปรับ schema เพื่อรองรับหลาย tactics ก่อน index จริง หากต้องการไม่เสียข้อมูลจาก STIX

## 9. สรุป

โปรเจกต์ขยับจาก “โครง Week 2–3 ที่ยังไม่มี hygiene/docs” มาเป็น “early MVP ที่ setup ได้ชัดขึ้นและพร้อมเริ่ม Week 2” แล้ว

สิ่งที่ดีขึ้นมากคือ repository hygiene, README, dependency, Gemini SDK และ tests ขั้นต้น ส่วนที่ยังเป็นหัวใจที่ต้องทำต่อคือ RAG/retrieval และ inference pipeline จริง ตอนนี้ยังไม่มี embedding/index/retriever และ `/alerts/infer` ยังเป็น stub จึงยังไม่ควรสื่อว่าเป็นระบบ ATT&CK inference ที่ใช้วิเคราะห์จริงได้
