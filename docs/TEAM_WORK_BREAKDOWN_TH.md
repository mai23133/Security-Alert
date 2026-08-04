# คู่มือแบ่งงาน 4 คน: Security-Alert

เอกสารนี้ใช้คู่กับ `docs/WORK_PLAN_TH.md` และ `security-alert-attack-technique-inference.md` เพื่อให้ทุกคนทำงานตาม Schema และ Workflow เดียวกัน

## เป้าหมายร่วม

ระบบรับ Alert narrative แล้วแนะนำ MITRE ATT&CK Enterprise Technique 1–3 รายการจาก pinned STIX `enterprise-attack-19.1` ให้ analyst ตรวจสอบต่อ ผลลัพธ์เป็นคำแนะนำเท่านั้น ไม่ block หรือ response เหตุการณ์อัตโนมัติ

ผลลัพธ์ต้องอยู่ใน `ATTACKInferenceResult` ตาม Schema ของอาจารย์ และทุก prediction ต้องมี confidence, evidence ที่พบจริงใน Alert narrative, `tactic: str`, MITRE URL และการตัดสิน `needs_human_review`

## กติกากลางและ API Contract

- อ่าน `security-alert-attack-technique-inference.md` ก่อนเริ่มงานทุกครั้ง เพราะเป็น Source of Truth
- ใช้ `TechniqueCandidate.tactic: str` และ `InferredTechnique.tactic: str` เท่านั้น ห้ามเปลี่ยนเป็น `list[str]`
- Gemini เลือก Technique ได้เฉพาะจาก `TechniqueCandidate` ที่ Retriever ส่งให้ และห้ามสร้าง Technique ID เอง
- `evidence_spans` ทุกค่าเป็นข้อความที่มีอยู่จริงใน Alert narrative
- ทุก `ATTACKInferenceResult` ต้องมี `disclaimer`
- ห้ามเพิ่ม field ระดับบนใน `ATTACKInferenceResult` หากไม่มีใน Schema
- ตำแหน่ง metadata ใน response คือ `TechniqueCandidate.stix_version` สำหรับ STIX version, `InferredTechnique.mitre_url` สำหรับ MITRE reference และ `ATTACKInferenceResult.disclaimer` สำหรับคำเตือน
- ใช้เฉพาะ Enterprise ATT&CK `19.1` ที่ pin ไว้ และตรวจ ID กับ `data/processed/technique_ids.json`
- Alert เป็น untrusted input และอาจมี prompt injection; tests ที่เกี่ยวกับ Gemini ต้องใช้ mock/fake และห้ามเรียก API จริง

## Workflow ระบบ

```text
Owner 4: รับ API Request
          ↓
Owner 2: Alert Parser + Tactic Router
          ↓
Owner 1: Index + Retriever
          ↓
Owner 2: Inferencer + Evidence + Grounding Judge
          ↓
Owner 4: Validate Schema + API Response

Owner 3: ประเมิน Retriever, Inference และระบบรวม
```

Workflow ภายใน Owner 2 คือ:

```text
Alert narrative
→ ParsedAlert
→ Tactic
→ รับ Candidates จาก Retriever
→ InferredTechnique
→ Evidence validation
→ Human review decision
```

## Interfaces กลางที่ต้องล็อกก่อนเริ่ม

```python
# Owner 2: แปลงข้อความ Alert เป็นข้อมูลแบบมีโครงสร้าง
def parse_alert(narrative: str) -> ParsedAlert:
    ...


# Owner 2: เลือก Tactic เดียวตาม Schema ปัจจุบัน
def route_tactic(parsed_alert: ParsedAlert) -> str:
    ...


# Owner 1: ค้นหา Technique Candidates ที่เกี่ยวข้อง
def retrieve_candidates(
    parsed_alert: ParsedAlert,
    tactic: str,
    top_k: int = 5,
) -> list[TechniqueCandidate]:
    ...


# Owner 2: เลือก Technique จาก Candidate ที่ได้รับเท่านั้น
def infer_techniques(
    narrative: str,
    candidates: list[TechniqueCandidate],
) -> list[InferredTechnique]:
    ...


# Owner 2: ตัดสินว่าต้องส่งให้เจ้าหน้าที่ตรวจเพิ่มเติมหรือไม่
def judge_result(
    narrative: str,
    inferred: list[InferredTechnique],
    candidates: list[TechniqueCandidate],
) -> bool:
    ...
```

Owner 1 และ Owner 2 ต้องตกลงรูปแบบ empty result, error และ deterministic ordering ของ candidates ก่อนเขียน implementation จริง

## Owner 1 — Index และ Retriever

### เป้าหมาย

สร้าง Retriever ที่คืน Top-k `TechniqueCandidate` จาก MITRE ATT&CK subset ที่ pin ไว้เท่านั้น เพื่อให้ Owner 2 ใช้เป็นขอบเขตของการ inference

### งานที่รับผิดชอบ

- เตรียมข้อมูลจาก MITRE ATT&CK STIX `19.1`
- ตัด revoked และ deprecated techniques
- กรอง `tactic` และ platform ตามขอบเขตโปรเจกต์
- สร้าง index จาก processed candidates
- ทำ BM25/keyword baseline ก่อน
- เพิ่ม embedding retriever เมื่อมีเวลาและไม่ทำให้ผลทดสอบไม่ reproducible
- คืน Top-k `TechniqueCandidate`
- ตรวจ Candidate ID กับ ATT&CK allowlist
- เขียน retrieval tests

### วิธีทำ

1. ใช้ `data/processed/technique_candidates.json` และ `technique_ids.json` เป็นข้อมูล runtime หลัก
2. เก็บ metadata ที่มีใน Schema โดยเฉพาะ `technique_id`, `technique_name`, `description_excerpt`, `tactic` และ `stix_version`
3. รองรับ filter ด้วย tactic เดียวและ `top_k` โดยผลต้องเรียงแบบ deterministic
4. ทดสอบว่า candidate ทุกตัวอยู่ใน allowlist, filter ได้, top-k ถูกต้อง และ no-match คืนรายการว่าง

### สิ่งส่งมอบ

- decision note ของ index/retrieval backend และวิธี rebuild
- `embedder.py`, `retriever.py` และ retrieval tests
- Top-k results ที่ deterministic และไม่คืน ID นอก allowlist

Owner 1 **ไม่เป็นเจ้าของ Metric**: ส่ง Top-k results ให้ Owner 3 คำนวณ Recall@k แล้วใช้รายงานนั้นปรับ Retriever

## Owner 2 — Parser, Router, Inferencer, Evidence และ Judge

### เป้าหมาย

แปลง narrative เป็นข้อมูลที่มีโครงสร้าง เลือก tactic เดียว และสร้าง prediction ที่ grounded โดยเลือกได้เฉพาะ candidates ที่ Owner 1 คืนมา

### งานที่รับผิดชอบ

- Alert Parser: แปลง narrative เป็น `ParsedAlert`
- Tactic Router: เลือก tactic เดียวให้ตรงกับ `tactic: str`
- Inferencer: ตรวจ JSON ที่ Gemini ส่งกลับ, จัดการ timeout และ malformed output, และเลือก Technique จาก candidates เท่านั้น
- Evidence validation: ตรวจว่า `evidence_spans` ทุกช่วงพบจริงใน narrative
- Grounding Judge: ตรวจ candidate ID, tactic, evidence และตัดสิน `needs_human_review`
- สร้าง confidence และ unit tests ของโมดูลทั้งหมดโดย mock Gemini

### วิธีทำ

1. Parser ต้องส่ง `ParsedAlert` ที่มี narrative, assets, observed_actions และ IOCs ตาม Schema
2. Router คืน tactic เดียวที่อยู่ในขอบเขต; ถ้าไม่แน่ใจให้ส่ง human review แทนการสร้างค่าใหม่
3. Inferencer รับ `list[TechniqueCandidate]`; ตัด ID ที่ไม่อยู่ในรายการนี้, ผิดรูปแบบ หรือเกิน 1–3 รายการ
4. Timeout, malformed JSON หรือ prompt injection ต้องไม่ทำให้ได้ prediction ที่ไม่ grounded; ให้คืน no-match หรือ review ตามกฎที่ตกลง
5. Evidence validator ตรวจแบบ exact substring กับ narrative ก่อนส่งต่อ Judge
6. Judge ต้องตั้ง review สำหรับ no-match, low confidence, ambiguous result, evidence ไม่ตรง, tactic ไม่ตรง หรือ candidate ไม่ถูกต้อง

### สิ่งส่งมอบ

- `alert_parser.py`, `tactic_router.py`, `technique_inferencer.py`, `evidence_linker.py`, `grounding_judge.py` ที่ผ่าน unit tests
- fake/mock Gemini client และ test cases สำหรับ valid, no-match, ambiguous, timeout, malformed output และ prompt injection
- prediction ที่เป็น `InferredTechnique` ถูกต้องตาม Schema และ evidence ตรวจย้อนกลับได้

## Owner 3 — Dataset และ Evaluation

### เป้าหมาย

วัดคุณภาพของ Retriever, Inference, Grounding และระบบรวมแบบทำซ้ำได้ พร้อมรักษา gold labels และเวอร์ชัน dataset

### งานที่รับผิดชอบ

- สร้าง evaluation dataset รวมทั้งหมด 35 Alerts
- ใน 35 Alerts มี ambiguous/multi-technique 10 รายการ และ negative controls 5 รายการ
- เริ่มจากชุดทดลอง 10 Alerts ก่อน แล้วจึงขยายเป็น 35 Alerts
- ดูแล Gold labels, dataset version และให้สมาชิกอย่างน้อยอีกหนึ่งคนช่วยตรวจ Gold labels
- คำนวณ `Recall@1`, `Recall@3` และ `Recall@5` จากผล Top-k ของ Owner 1
- ประเมิน inference, evidence grounding, hallucinated-ID, exact technique F1, parent technique recall, false-positive และ human-review rate
- สร้าง evaluation report พร้อม model, prompt, dataset และ STIX version

### วิธีทำ

1. Gold labels ต้องอยู่ใน pinned allowlist และอ้างอิง Enterprise ATT&CK `19.1`
2. ชุดทดลอง 10 Alerts ใช้ตรวจ schema ของ dataset และ metric ก่อนขยายชุดเต็ม
3. แยก test ของ metric ออกจาก provider; runner ต้องทำงานกับ saved predictions หรือ fake pipeline ได้
4. รับ Top-k จาก Owner 1 เพื่อคำนวณ Recall@k และส่งผลให้ Owner 1 ปรับ Retriever
5. ประเมิน output ของ Owner 2 และระบบที่ Owner 4 เชื่อม โดยไม่เรียก Gemini จริงใน automated tests

### สิ่งส่งมอบ

- dataset, README/schema และ version record
- `eval/metrics.py`, `eval/run_eval.py` และ tests ของ metric
- report ที่มี Recall@1/@3/@5, inference/grounding/hallucination metrics และ quality gates

## Owner 4 — API Integration, Reliability และ CI

### เป้าหมาย

เชื่อม workflow ทั้งระบบเข้ากับ `POST /alerts/infer` ให้ request และ response เป็นไปตาม Schema, มี error handling และทดสอบ integration ได้โดยไม่เรียก Gemini จริง

### งานหลักที่รับผิดชอบ

- ทำ `POST /alerts/infer`
- เชื่อม Pipeline: Parser/Router → Retriever → Inferencer/Evidence/Judge
- ตรวจ request และ response ด้วย Pydantic Schema
- คืน `ATTACKInferenceResult` ตาม Schema พร้อม `disclaimer`
- ทำ error handling ที่ไม่เผย stack trace หรือ secrets
- เขียน API และ integration tests โดย mock pipeline/provider
- ทำ CI smoke test สำหรับ test suite และ integration ที่สำคัญ

### วิธีทำ

1. เริ่มด้วย fixture/fake pipeline เพื่อให้ API tests เขียนและรันได้พร้อมกับงาน Owner อื่น
2. เมื่อ Owner 1 และ Owner 2 ส่ง interface ที่ล็อกแล้ว จึงเชื่อม implementation จริงตามลำดับ workflow
3. Validation ต้องยืนยันว่า response ไม่มี Technique นอก candidates/allowlist และไม่เพิ่ม top-level fields นอก `ATTACKInferenceResult`
4. API ต้องคง advisory disclaimer; MITRE URL อยู่ใน prediction และ STIX version อยู่ใน candidate ตาม Schema ไม่ใช่ top-level response fields
5. Provider timeout หรือ malformed output ต้องถูกจัดการเป็นผลลัพธ์/ข้อผิดพลาดที่ปลอดภัยตาม contract ที่ทีมตกลง

### สิ่งส่งมอบ

- `/alerts/infer` ใช้ pipeline จริง ไม่ใช่ no-match stub
- API/integration tests ที่ mock Gemini และรันได้แบบ deterministic
- CI smoke test และเอกสาร error behavior ของ endpoint

### งานเสริมเมื่อมีเวลา

- `POST /alerts/infer/batch`
- `POST /evaluate`
- Authentication
- Rate limiting
- Advanced structured logging

## การทำงานพร้อมกันและการรวมงาน

- ทุก Owner เริ่มพร้อมกันได้โดยใช้ mock หรือ fixture
- ต้องล็อก Schema และ Interfaces กลางในเอกสารนี้ก่อนเริ่ม implementation
- แต่ละ Owner ทำงานบน branch ของตนเองและเขียน tests ของส่วนที่รับผิดชอบ
- ลำดับการรวมงานจริงคือ Owner 2 → Owner 1 → Owner 2 → Owner 4
- Owner 3 ประเมินแต่ละโมดูลและระบบรวมตลอดการรวมงาน

## จุดนัดส่งมอบ

| จุดนัด | ผู้ส่ง | ผู้รับ | สิ่งที่ต้องส่ง |
| --- | --- | --- | --- |
| Interface lock | ทุกคน | ทุกคน | ยืนยัน `tactic: str`, interfaces กลาง, empty/error behavior และ fixture ร่วม |
| Parser/Router ready | Owner 2 | Owner 1, 4 | `ParsedAlert`, tactic เดียว และ unit-test fixtures |
| Retriever ready | Owner 1 | Owner 2, 3, 4 | Top-k candidates, deterministic ordering และ allowlist checks |
| Inference/Judge ready | Owner 2 | Owner 3, 4 | prediction, evidence validation และ review rules |
| Evaluation baseline | Owner 3 | Owner 1, 2, 4 | dataset version, Recall@k และ inference/grounding report |
| API ready | Owner 4 | ทุกคน | `/alerts/infer`, integration tests, CI smoke result และ known limitations |

## Definition of Done

งานของแต่ละ Owner เสร็จเมื่อมี code, tests และเอกสารของตนเองใน branch/PR; test ที่เกี่ยวข้องผ่านโดยไม่เรียก Gemini จริง; `git diff --check` ผ่าน; และงานไม่ละเมิด pinned STIX, allowlist, `tactic: str`, evidence grounding, advisory-only หรือ untrusted-input guardrails
