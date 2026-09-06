# รายการแก้ไขสาย D ก่อนรวมเข้ากับ A+B

อัปเดต: 7 กันยายน 2026  
สาขาที่ตรวจ: `feature-branch` ที่ commit `c35c1562133776c8f35acc5c773d485a9e0509ac`  
สาขาปลายทาง: `mai-work`  
Source of Truth: `security-alert-attack-technique-inference.md`

## สรุปสถานะ

สาย A+B บน `mai-work` เชื่อม pipeline จริงระดับ baseline เข้ากับ `POST /alerts/infer` แล้ว โดยใช้ลำดับ:

```text
Alert Parser
→ Tactic Router
→ BM25 Retriever
→ Technique Inferencer
→ Evidence Linker
→ Grounding Judge
→ ATTACKInferenceResult
```

สาย D ควรพัฒนาต่อจาก contract นี้ โดยรับผิดชอบ product shell ได้แก่ API ที่เหลือ, typed safe errors, request ID, CI และ UI

`feature-branch` ปัจจุบันยังไม่ควร merge ทั้งสาขา เพราะ:

1. เปลี่ยน response schema ของ `/alerts/infer` จนไม่ตรงกับ schema กลาง
2. แทน pipeline A+B ด้วยผลจำลองแบบ hard-coded
3. แก้ไฟล์ agents และ STIX ingestion ซึ่งอยู่นอกขอบเขตสาย D และทับ implementation ที่เชื่อมแล้ว
4. เพิ่ม ChromaDB และ Gemini embedding เป็น dependency หลัก ทั้งที่ baseline ปัจจุบันใช้ BM25 แบบ offline
5. test ของ branch D ยังไม่ผ่าน และมีการ skip regression tests
6. `/rag/search` ซึ่งเป็นงานส่งมอบของ D ยังไม่มี
7. UI อ่าน response คนละรูปแบบกับ `ATTACKInferenceResult`

ผลตรวจ ณ วันที่เขียนเอกสาร:

```text
mai-work:       42 passed
feature-branch: 17 passed, 1 failed, 2 skipped
```

test ที่ล้มคือ batch test เรียก `POST /alerts/batch-infer` แต่ route ที่โค้ดประกาศคือ `POST /alerts/infer/batch`

การจำลอง merge พบ conflict 8 ไฟล์:

```text
requirements.txt
src/agents/alert_parser.py
src/agents/evidence_linker.py
src/agents/grounding_judge.py
src/agents/tactic_router.py
src/agents/technique_inferencer.py
src/api/routes/alerts.py
tests/test_alerts_api.py
```

## Contract ที่ห้ามเปลี่ยนระหว่างรวม D

### 1. Schema กลาง

ให้ import model จาก `src/schemas.py` ห้ามประกาศ `ATTACKInferenceResult` ชุดใหม่ภายใน route

response ของ alert หนึ่งรายการต้องมีรูปแบบนี้:

```python
class ATTACKInferenceResult(BaseModel):
    alert_id: str
    inferred_techniques: list[InferredTechnique]
    candidates_considered: list[TechniqueCandidate]
    needs_human_review: bool
    disclaimer: str
```

`InferredTechnique.confidence` ต้องเป็น `float` ช่วง `0.0–1.0` ไม่ใช่ข้อความ `"High"`, `"Low"` หรือ `"None"`

ห้ามเปลี่ยนชื่อ field เป็น:

```text
request_id
prediction
candidates
```

ถ้าต้องมี request ID สำหรับ tracing ให้เก็บแยกจาก `alert_id` เช่น response header `X-Request-ID` หรือ logging context โดยไม่แก้ schema หลักโดยพลการ

### 2. Pipeline กลาง

`POST /alerts/infer` ต้องเรียก `run_inference()` จาก `src/inference_pipeline.py` และใช้ `BaselineRetriever` จาก `src/rag/retriever.py`

ห้ามใช้ `fake_inference_pipeline()` ใน runtime จริง และห้ามคืน `T1110` ให้ทุก alert แบบ hard-coded

fake pipeline หรือ test double ใช้ได้เฉพาะใน automated tests โดย inject หรือ monkeypatch dependency ที่ route เรียก

### 3. Knowledge Base และ Retriever

ให้ใช้ไฟล์ต่อไปนี้เป็นฐาน:

```text
data/raw/enterprise-attack-19.1.json
data/processed/technique_candidates.json
data/processed/technique_ids.json
```

รอบ integration D นี้ให้คง BM25 baseline ที่ทำงานแบบ offline และทำซ้ำได้ ห้ามเปลี่ยน runtime ให้ต้องใช้ ChromaDB, Gemini embedding หรือ online TAXII

การเปลี่ยน retrieval backend เป็นงานสถาปัตยกรรมอีกชุดหนึ่ง ต้องมี decision, dependency ที่ตรึง, index ที่สร้างซ้ำได้, Recall@k baseline และการยืนยันจากทีมก่อน

### 4. Guardrails

- prediction ต้องมาจาก retrieved candidates เท่านั้น
- Technique ID ต้องอยู่ใน pinned allowlist
- จำกัด prediction 1–3 รายการ
- evidence span ต้องพบจริงใน narrative
- no-match หรือผลไม่แน่ใจต้องมี `needs_human_review=true`
- response ต้องมี advisory disclaimer
- ทุก response ต้องระบุ MITRE ATT&CK version ที่ตรึงไว้
- alert เป็น untrusted input และต้องไม่เปลี่ยนคำสั่งหรือกติกาของ pipeline ได้
- tests ต้องไม่เรียก Gemini หรือ network จริง
- ห้ามส่ง exception, stack trace, secret หรือ provider output ดิบกลับ client

## สิ่งที่ต้องแก้ใน `feature-branch`

| ลำดับ | พื้นที่ | ปัญหาปัจจุบัน | ผลลัพธ์ที่ต้องการ |
| ---: | --- | --- | --- |
| 1 | ฐาน branch | D พัฒนาจากฐานก่อน A+B integration | นำ `mai-work` ล่าสุดมาเป็นฐานก่อนแก้ D |
| 2 | Agents | D เขียนทับ parser/router/inferencer/linker/judge | ใช้ไฟล์จาก `mai-work`; D ไม่แก้ algorithm ของ agents |
| 3 | Retrieval | เพิ่ม Chroma/Gemini retriever และ ingestion ใหม่ | ใช้ `src/rag/retriever.py` BM25 และ processed allowlist เดิม |
| 4 | Schema | route ประกาศ schema ใหม่ | import schema กลางและรักษา API contract |
| 5 | Single infer | route เรียก fake pipeline | route เรียก `run_inference()` จริง |
| 6 | Batch | ใช้ fake pipeline และ error เป็น prediction/evidence | เรียก pipeline จริงต่อ alert และคืนผล/typed error ที่ปลอดภัย |
| 7 | RAG search | ยังไม่มี | เพิ่ม `POST /rag/search` บน `BaselineRetriever.search()` |
| 8 | Errors | ส่งพฤติกรรม error ไม่สม่ำเสมอ | กำหนด safe typed error และ request ID ที่ทดสอบได้ |
| 9 | Tests | endpoint ไม่ตรง, skip regression tests | แก้ path, คืน regression tests และ mock dependency อย่างถูกต้อง |
| 10 | CI | ตั้ง dummy key และ `MOCK_AI` ที่โค้ดไม่ได้ใช้ | รัน tests โดยไม่มี provider key และ fail หากมี network call |
| 11 | UI | อ่าน `prediction/confidence/candidates` แบบเก่า | อ่าน nested `inferred_techniques` และ `candidates_considered` |
| 12 | Docs | ยังไม่บอก error/batch/search contract | เพิ่มตัวอย่าง request/response และข้อจำกัดของ local demo |

## ลำดับขั้นตอนการแก้ไข

### ขั้นที่ 1: ทำ branch D ให้มีฐานเดียวกับ A+B

ก่อนเริ่มให้ commit หรือเก็บงานที่ยังไม่เสร็จของ D ให้ปลอดภัย จากนั้นนำ `mai-work` ล่าสุดเข้ามาเป็นฐาน

แนวทางที่แนะนำคือสร้าง branch ใหม่จาก `mai-work` แล้วค่อยย้ายเฉพาะงาน D ที่ต้องการ:

```bash
git fetch origin
git switch mai-work
git pull --rebase origin mai-work
git switch -c feature-d-integration
```

จาก `feature-branch` ให้นำแนวคิดหรือส่วนที่เกี่ยวกับไฟล์เหล่านี้มาปรับใหม่บน branch นี้:

```text
.github/workflows/ci.yml
src/api/routes/alerts.py
src/api/routes/rag.py              # สร้างเมื่อเพิ่ม /rag/search
tests/test_alerts_api.py
tests/test_rag_api.py              # สร้างเมื่อเพิ่ม /rag/search
ui/index.html
```

ไม่ควร cherry-pick commit `c35c156` ทั้งก้อน เพราะ commit เดียวเปลี่ยนทั้ง API, agents, retrieval, ingestion, tests, dependency และ UI ทำให้ดึงงานนอกขอบเขตเข้ามาด้วย

ถ้าทีมเลือก merge `mai-work` เข้า `feature-branch` เดิม ให้ resolve conflict โดยใช้ implementation จาก `mai-work` สำหรับไฟล์ agents ทั้งห้า และใช้ `src/api/routes/alerts.py` ของ `mai-work` เป็นจุดตั้งต้น แล้วค่อยเพิ่ม batch/error behavior เข้าไป

เกณฑ์ผ่านขั้นนี้:

- `POST /alerts/infer` เดิมยังคืน `ATTACKInferenceResult`
- regression tests 42 รายการเดิมยังผ่าน
- ไม่มี ChromaDB หรือ Gemini embedding เข้ามาเป็น dependency ของ runtime baseline

### ขั้นที่ 2: คืน agents และ retrieval ให้ตรง A+B

ไฟล์ต่อไปนี้ต้องยึด implementation จาก `mai-work`:

```text
src/agents/alert_parser.py
src/agents/tactic_router.py
src/agents/technique_inferencer.py
src/agents/evidence_linker.py
src/agents/grounding_judge.py
src/inference_pipeline.py
src/rag/embedder.py
src/rag/retriever.py
src/rag/ingest_stix.py
```

ไม่ให้นำไฟล์ `src/agents/technique_retriever.py` และ `src/rag/process_stix.py` มาแทนเส้นทางข้อมูลปัจจุบัน เพราะจะเกิด source of truth ชุดที่สองและมีพฤติกรรมต่างจาก allowlist เดิม

เหตุผลสำคัญ:

- `process_stix.py` ใน D มี helper ที่ยอมรับ `defense-evasion` ซึ่งอยู่นอกสาม tactic ที่กำหนด
- การเลือก tactic ด้วย `list(set)[0]` ไม่ deterministic
- Chroma ingestion ต้องเรียก Gemini และพัก 3 วินาทีต่อ technique จึงสร้างซ้ำแบบ offline ไม่ได้
- D ใช้ชื่อ embedding model สองชื่อใน ingestion และ retriever ทำให้ index/query อาจไม่เข้ากัน
- Gemini client ของ D สร้าง client ตอน import; เมื่อไม่มี key อาจทำให้ API/test import ไม่สำเร็จ

เกณฑ์ผ่านขั้นนี้:

- service เริ่มทำงานได้โดยไม่มี `GOOGLE_API_KEY` และ `GEMINI_API_KEY`
- retrieval ใช้ pinned candidates และ allowlist เท่านั้น
- parser/router failure fallback ได้โดย API ไม่ล้ม
- agent functions ยังตรงกับ signature ที่ `run_inference()` เรียก

### ขั้นที่ 3: แก้ `POST /alerts/infer` ให้ใช้ pipeline จริง

ให้คงโครงสร้าง route ปัจจุบันบน `mai-work`:

```python
@router.post("/infer", response_model=ATTACKInferenceResult)
async def infer_techniques(req: AlertRequest):
    alert_id = req.alert_id or create_alert_id()
    return run_inference(
        alert_id=alert_id,
        narrative=req.narrative,
        retriever=RETRIEVER,
    )
```

รายละเอียดที่ต้องเพิ่ม:

1. validate ว่า narrative ไม่เป็นค่าว่างหลัง trim
2. กำหนดขนาดข้อความสูงสุดที่สมเหตุสมผลและคืน `422` เมื่อเกิน
3. สร้าง request ID สำหรับ tracing และแนบใน response header
4. log request ID, endpoint, status และระยะเวลา โดยไม่ log raw narrative
5. normalize timeout/provider error เป็น typed response ที่ไม่เผยรายละเอียดภายใน
6. คง safe fallback ที่ A+B รองรับเมื่อไม่มี provider key

ตัวอย่าง response ที่ถูกต้อง:

```json
{
  "alert_id": "alert-001",
  "inferred_techniques": [],
  "candidates_considered": [],
  "needs_human_review": true,
  "disclaimer": "Advisory tagging only. Not autonomous SOC action. Verify with senior analyst."
}
```

ห้ามใช้ `prediction=["System Error"]` เพราะ `System Error` ไม่ใช่ MITRE Technique ID และจะทำให้ hallucinated-ID rate ผิดทันที

### ขั้นที่ 4: เพิ่ม `POST /alerts/infer/batch`

path ต้องตรง specification:

```text
POST /alerts/infer/batch
```

request ขั้นต่ำ:

```json
{
  "alerts": [
    {"alert_id": "a-001", "narrative": "..."},
    {"alert_id": "a-002", "narrative": "..."}
  ]
}
```

response ควรประกอบด้วยผลของแต่ละ alert โดยแต่ละรายการยังเป็น `ATTACKInferenceResult` ตาม schema กลาง ไม่ยุบเป็น list ของ ID

ขั้นตอนทำงาน:

1. validate ว่า `alerts` มีอย่างน้อยหนึ่งรายการ
2. กำหนดจำนวนสูงสุดต่อ batch เพื่อป้องกัน resource abuse
3. เรียก `run_inference()` ด้วย retriever ตัวเดียวกันสำหรับแต่ละ alert
4. รักษาลำดับผลลัพธ์ให้ตรงกับลำดับ input
5. สร้าง `alert_id` ให้เฉพาะรายการที่ไม่ได้ส่งมา
6. กำหนดนโยบาย partial failure ให้ชัดเจน

นโยบาย partial failure ที่แนะนำสำหรับ MVP:

- validation ของ request ทั้งก้อนผิด ให้ FastAPI คืน `422`
- alert รายการหนึ่งประมวลผลไม่ได้ ให้คง alert ID และคืน safe no-match/review สำหรับรายการนั้น
- ห้ามใส่ exception string ใน evidence หรือ prediction
- log รายละเอียดภายในด้วย request ID เท่านั้น

test ขั้นต่ำ:

- batch สองรายการสำเร็จและผลเรียงตาม input
- alert ที่ไม่มี ID ได้ ID ใหม่ไม่ซ้ำ
- batch ว่างถูก reject
- batch เกินขนาดถูก reject
- รายการหนึ่ง timeout แต่รายการอื่นยังได้ผล
- error response ไม่มี secret, stack trace หรือ exception ดิบ

### ขั้นที่ 5: เพิ่ม `POST /rag/search`

endpoint นี้ใช้สำหรับแสดง top-k candidates ก่อน inference และต้องเรียก `BaselineRetriever.search()` โดยตรง

request ที่แนะนำ:

```json
{
  "narrative": "encoded PowerShell execution",
  "tactic": ["execution"],
  "top_k": 5
}
```

response ใช้ `list[TechniqueCandidate]` หรือ wrapper ที่ระบุ candidates โดยไม่เปลี่ยน field ภายใน candidate

validation ที่ต้องมี:

- narrative ต้องไม่ว่าง
- `top_k` ต้องเป็นจำนวนเต็มบวกและมีเพดาน
- tactic ต้องเป็น `initial-access`, `execution` หรือ `credential-access`
- ไม่ส่ง tactic หรือส่ง list ว่าง ให้ค้นทั้งสาม tacticตาม behavior ที่ทีมล็อกไว้
- ทุก ID ที่คืนต้องอยู่ใน `data/processed/technique_ids.json`

test ขั้นต่ำ:

- คืนจำนวน candidate ไม่เกิน `top_k`
- filter tactic ถูกต้อง
- ผลซ้ำได้เมื่อ input เดิม
- reject `top_k=0`, ค่าติดลบ, string และค่าเกินเพดาน
- reject tactic นอก scope
- ไม่คืน ID นอก allowlist
- test ไม่เรียก network

### ขั้นที่ 6: ทำ typed errors และ request ID

สร้าง error model กลางสำหรับ API เช่น:

```json
{
  "error": {
    "code": "INFERENCE_TIMEOUT",
    "message": "Inference timed out. Human review is required.",
    "request_id": "req-..."
  }
}
```

ทีมต้องเลือกให้ชัดว่ากรณี provider failure จะคืน HTTP error หรือ safe no-match ใน `200` สำหรับ single inference ข้อกำหนดปัจจุบันยอมให้ตกลงได้ทั้งสองแบบ แต่ต้องใช้แบบเดียวกันใน single, batch, docs และ tests

mapping ที่แนะนำ:

| กรณี | HTTP status | พฤติกรรม |
| --- | ---: | --- |
| request/schema ผิด | 422 | FastAPI validation error หรือ typed validation error |
| narrative เกินขนาด | 413 หรือ 422 | ไม่เริ่ม pipeline |
| provider timeout ที่ไม่มี safe fallback | 504 | `INFERENCE_TIMEOUT` |
| processed taxonomy หาย/อ่านไม่ได้ | 503 | `KNOWLEDGE_BASE_UNAVAILABLE` |
| unexpected internal failure | 500 | `INTERNAL_ERROR` และข้อความทั่วไป |

ข้อกำหนด logging:

- log request ID, status code, latency และ error code
- ห้าม log API key, raw alert, full provider output หรือ stack trace ไปยัง client
- stack trace ภายในใช้ได้เฉพาะ environment ที่ควบคุมและต้องไม่ปน response

### ขั้นที่ 7: แก้ automated tests

ห้าม skip regression test เพื่อให้ CI ผ่าน ให้แก้ implementation หรือ fixture แทน

รายการที่ต้องแก้จาก D ปัจจุบัน:

1. เปลี่ยน batch test จาก `/alerts/batch-infer` เป็น `/alerts/infer/batch`
2. ลบ `@pytest.mark.skip` ที่ปิด test ของ `/alerts/infer`
3. คืน test ingestion ที่ตรวจ `technique_ids.json` และ `technique_candidates.json`
4. assert schema จริง ได้แก่ `alert_id`, `inferred_techniques`, `candidates_considered`, `needs_human_review`, `disclaimer`
5. mock `run_inference()` หรือ provider adapter เฉพาะ test ที่ต้องจำลอง timeout/error
6. เพิ่ม sentinel ที่ fail test หากเกิด network call
7. ตรวจ `X-MITRE-ATTaCK-Version: enterprise-attack-19.1`
8. ตรวจ request ID ตาม contract ที่ D เลือก

อย่าตั้ง `GEMINI_API_KEY=dummy_key_for_ci_testing` เป็นวิธีป้องกัน network เพราะโค้ดอาจพยายามเรียก provider ด้วย key ปลอมจริง ควรถอด provider keys ออกจาก environment และใช้ dependency injection/monkeypatch

### ขั้นที่ 8: แก้ CI

CI ต้องติดตั้ง dependency จากไฟล์ที่ตรึงไว้และรันคำสั่งเดียวกับที่ทีมใช้ตรวจในเครื่อง

ขั้นต่ำ:

```yaml
- name: Run tests
  env:
    GOOGLE_API_KEY: ""
    GEMINI_API_KEY: ""
  run: python -m pytest -q

- name: Check diff whitespace
  run: git diff --check
```

สิ่งที่ต้องปรับ:

- ให้ workflow ทำงานกับ PR ที่จะรวมเข้า branch จริงของทีม เช่น `mai-work` และ `main`
- ใช้ `python -m pip` และ `python -m pytest` เพื่อให้แน่ใจว่าใช้ interpreter เดียวกัน
- ไม่ติดตั้ง dependency ซ้ำด้วยคำสั่งแยก หากอยู่ใน `requirements.txt` แล้ว
- ไม่กำหนด `MOCK_AI=True` จนกว่าจะมีโค้ดรองรับ flag นี้จริงและมี test ยืนยัน
- fail เมื่อ test ถูกเก็บผิด path หรือ collection error
- พิจารณาเพิ่ม test ว่าจำนวน skipped tests ไม่เพิ่มโดยไม่มีเหตุผลที่บันทึกไว้

### ขั้นที่ 9: แก้ UI ให้ตรง schema กลาง

UI ปัจจุบันอ่าน field เหล่านี้:

```text
data.prediction
data.confidence
data.evidence_spans
data.candidates
```

ต้องเปลี่ยนเป็น:

```text
data.inferred_techniques
data.candidates_considered
data.needs_human_review
data.disclaimer
```

สำหรับแต่ละ inferred technique ให้แสดง:

- `technique_id`
- `technique_name`
- `tactic`
- `confidence`
- `evidence_spans`
- `mitre_url`

สำหรับ candidate list ให้แสดงอย่างน้อย:

- `technique_id`
- `technique_name`
- `tactic`

UI behavior ที่ต้องมี:

1. ปิดปุ่มหรือแสดง loading ระหว่าง request
2. แสดง no-match อย่างชัดเจนเมื่อ `inferred_techniques=[]`
3. แสดง human-review status ทุกครั้ง
4. แสดง disclaimer จาก response ทุกครั้ง
5. escape/render alert และ API data เป็น text ไม่ใช้ `innerHTML` กับข้อมูล untrusted
6. แสดง safe error message และ request ID เมื่อ API ล้ม
7. ไม่ log raw alert ลง console ใน build ที่นำไปสาธิต
8. ระบุว่า UI เป็น local demo จนกว่าจะกำหนด auth, rate limit และ privacy/retention

Tailwind CDN เป็น external dependency หากต้องสาธิตแบบ offline ควรใช้ CSS ในไฟล์หรือ bundle asset ไว้ใน repository

### ขั้นที่ 10: ตรวจ CORS และขอบเขต deployment

ถ้าเป้าหมายรอบนี้เป็น local demo ให้จำกัด CORS อย่างน้อยเป็น origin ของ UI ที่ใช้จริง และเขียนข้อจำกัดไว้ใน README

ถ้าจะ deploy หรือรับ alert จริง ต้องเพิ่มก่อน release:

- authentication
- rate limiting
- CORS allowlist
- privacy/retention policy
- การไม่เก็บ raw alert นอก course sandbox
- acceptance/security tests

รายการนี้ไม่ควรบล็อก local UI skeleton แต่ต้องบล็อกการประกาศว่า production-ready

### ขั้นที่ 11: อัปเดตเอกสาร API

แก้ `docs/API_OVERVIEW_TH.md` และเอกสารส่งต่อให้มี:

- request/response ของ single infer
- request/response ของ batch
- request/response ของ RAG search
- error codes และ request ID
- batch limit และ top-k limit
- provider failure policy
- ข้อความ advisory และ MITRE version
- ระบุว่า tests ใช้ mock/fake dependency และไม่เรียก provider จริง

ห้ามแก้เอกสารให้กล่าวว่า A+B ยังไม่เชื่อม เพราะ `mai-work` มี pipeline baseline แล้ว

## ไฟล์จาก D ที่นำมาใช้ได้หลังปรับ

| ไฟล์/แนวคิด | วิธีนำมาใช้ |
| --- | --- |
| `.github/workflows/ci.yml` | ใช้เป็น skeleton แล้วแก้ branch target, commands และ environment |
| batch route | ใช้แนวคิดการประมวลผลหลายรายการ แต่เปลี่ยนให้เรียก `run_inference()` และใช้ schema กลาง |
| typed HTTP 504/500 | ใช้เป็นฐานออกแบบ error model แต่ห้ามเผย exception และต้องใช้ contract เดียวกัน |
| `ui/index.html` | ใช้ layout ได้ แต่เปลี่ยน data binding ให้ตรง `ATTACKInferenceResult` |
| request ID | เก็บแนวคิด tracing แต่แยกจาก `alert_id` ให้ชัด |

ไฟล์/แนวคิดที่ไม่ควรนำมารวมในรอบนี้:

```text
src/agents/technique_retriever.py
src/rag/process_stix.py
ChromaDB runtime dependency
Gemini embedding ingestion
fake_inference_pipeline() ใน production route
schema ATTACKInferenceResult ที่ประกาศซ้ำใน route
```

## ลำดับ commit ที่แนะนำ

แยก commit ให้ review และย้อนกลับได้ง่าย:

1. `chore: rebase stream D on integrated A+B baseline`
2. `feat(api): add contract-compatible batch inference endpoint`
3. `feat(api): add deterministic RAG search endpoint`
4. `feat(api): add request IDs and safe typed errors`
5. `test(api): cover batch search and failure behavior`
6. `ci: run offline test suite for mai-work and main`
7. `feat(ui): render ATTACKInferenceResult from live API`
8. `docs: document stream D API and integration contracts`

แต่ละ commit ควรทำให้ tests ผ่าน หรืออย่างน้อยไม่ทำลาย tests ที่ผ่านก่อนหน้า

## Checklist ก่อนเปิด Pull Request

### Source และ architecture

- [ ] branch D มี `mai-work` ล่าสุดเป็นฐาน
- [ ] `/alerts/infer` ยังเรียก `run_inference()` จริง
- [ ] ไม่มี fake hard-coded prediction ใน production route
- [ ] ไม่เขียนทับ agent/retriever/ingestion ของ A+B
- [ ] ใช้ pinned STIX `enterprise-attack-19.1`
- [ ] ใช้ processed allowlist เดิม

### Schema และ API

- [ ] response alert เดี่ยวใช้ `ATTACKInferenceResult` จาก `src/schemas.py`
- [ ] confidence เป็น float
- [ ] batch path คือ `/alerts/infer/batch`
- [ ] มี `/rag/search`
- [ ] request ID แยกจาก alert ID
- [ ] error contract ปลอดภัยและบันทึกใน docs
- [ ] MITRE version header ยังอยู่ครบ

### Security

- [ ] ไม่มี Technique ID นอก retrieved candidates/allowlist
- [ ] ไม่มี exception หรือ secret ใน response
- [ ] ไม่ log raw narrative
- [ ] tests ไม่เรียก Gemini/network จริง
- [ ] no-match และ failure ที่กำหนดไว้ส่ง human review
- [ ] disclaimer แสดงใน API และ UI

### Tests และ CI

- [ ] ไม่มีการ skip regression tests เพื่อหลบ failure
- [ ] single infer tests ผ่าน
- [ ] batch tests ผ่าน
- [ ] RAG search tests ผ่าน
- [ ] timeout/error tests ผ่าน
- [ ] prompt injection/allowlist/evidence tests ของ A+B ยังผ่าน
- [ ] CI ทำงานบน PR เข้า `mai-work`
- [ ] CI รันโดยไม่มี provider API key

### UI

- [ ] UI อ่าน `inferred_techniques` และ `candidates_considered`
- [ ] แสดง confidence/evidence/tactic แยกราย technique
- [ ] แสดง no-match, human review และ disclaimer
- [ ] ไม่ใช้ `innerHTML` กับข้อมูลจาก alert/API
- [ ] แสดง safe error และ request ID

## คำสั่งตรวจรับก่อนส่ง merge

รันจาก root ของ repository ด้วย environment Python 3.11 ที่ติดตั้ง dependencies แล้ว:

```bash
python -m pytest -q
git diff --check
git status --short
```

ตรวจ endpoint แบบ manual เพิ่มเติมผ่าน FastAPI TestClient หรือ local server:

```text
POST /alerts/infer
POST /alerts/infer/batch
POST /rag/search
GET  /taxonomy/techniques
GET  /taxonomy/techniques/{id}
```

กรณีตรวจรับขั้นต่ำ:

1. alert brute-force/PowerShell คืน candidate หรือ inference ใน schema ที่ถูกต้อง
2. benign alert คืน no-match หรือ low-confidence พร้อม human review
3. prompt-injection alert ไม่สามารถบังคับ ID นอก allowlist
4. evidence ที่ไม่มีใน narrative ถูกตัดหรือทำให้ต้อง review
5. batch partial failure ไม่ทำให้ข้อมูล error กลายเป็น prediction
6. `/rag/search` คืนผล deterministic ตาม top-k/tactic
7. ระบบและ tests รันได้โดยไม่มี Gemini API key

## Definition of Done ของสาย D

สาย D พร้อม merge เมื่อครบทุกข้อดังนี้:

1. API single infer ของ A+B ไม่เกิด regression
2. batch และ RAG search ใช้ component จริงและตรง API contract
3. schema response ยังตรง `src/schemas.py`
4. typed error/request ID ไม่เปิดเผยข้อมูลภายใน
5. tests ทั้งหมดผ่านแบบ offline โดยไม่ skip regression tests
6. CI รันชุดทดสอบเดียวกับ local และทำงานกับ PR เข้า branch ที่ทีมใช้รวม
7. UI แสดง `ATTACKInferenceResult`, candidates, review flag และ disclaimer ได้
8. ไม่มีงานนอกขอบเขต D เขียนทับ retrieval หรือ agent algorithms
9. `git diff --check` ผ่านและ PR ไม่มี secrets, `.env`, bytecode หรือ Chroma database

หลัง D ผ่านเกณฑ์นี้จึง merge เข้า `mai-work` แล้วรัน system tests ร่วมกับสาย C เพื่อสร้างรายงาน evaluation ของ pipeline จริงต่อไป
