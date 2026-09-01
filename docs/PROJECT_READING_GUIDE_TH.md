# คู่มืออ่านโปรเจกต์ Security-Alert

เอกสารนี้เป็นลำดับการอ่านสำหรับคนที่เพิ่งเข้ามาในโครงการ เพื่อเข้าใจเป้าหมาย สถานะปัจจุบัน โค้ดที่ทำงานแล้ว และงานที่ยังเหลืออยู่

## สรุปในหนึ่งนาที

Security-Alert รับข้อความ security alert แล้วมีเป้าหมายจะแนะนำ MITRE ATT&CK Enterprise Technique 1–3 รายการ พร้อม confidence, tactic และ evidence spans ให้ analyst ตรวจสอบต่อ

ปัจจุบัน repository มี knowledge base ที่กรองจาก MITRE STIX, Pydantic schemas, taxonomy endpoints และ pipeline baseline แล้ว: `/alerts/infer` เชื่อม parser, router, BM25 retrieval, inference, evidence และ grounding อยู่ ส่วน evaluation, API contract ที่เหลือ และ production controls ยังอยู่ระหว่างพัฒนา

## ลำดับการอ่านที่แนะนำ

### 1. เข้าใจเป้าหมายและกติกาก่อน

อ่าน [security-alert-attack-technique-inference.md](../security-alert-attack-technique-inference.md) ซึ่งเป็น Source of Truth ของโครงการ โดยเริ่มจากหัวข้อต่อไปนี้:

| หัวข้อ | สิ่งที่ต้องเข้าใจ |
| --- | --- |
| 1 และ 3 | ปัญหา เป้าหมาย In Scope และ Out of Scope |
| 4 | ใช้ MITRE Enterprise ATT&CK STIX 2.1 รุ่นตรึง `enterprise-attack-19.1` |
| 5 | pipeline เป้าหมายของ agents |
| 6 | Pydantic schemas และชื่อ field ที่ API ต้องใช้ |
| 8 | API contract เป้าหมาย |
| 9 | metrics และ quality gates |
| 10 | security guardrails ที่ห้ามละเมิด |

กติกาสำคัญ: ระบบเป็น advisory เท่านั้น, ห้ามสร้าง Technique ID เอง, ใช้เฉพาะ subset ที่ตรึงไว้ และถือว่า alert text เป็น untrusted input

### 2. ดูวิธีรันและขอบเขต MVP

อ่าน [README.md](../README.md) เพื่อดู environment, dependencies, วิธีรัน test และวิธีเปิด FastAPI ในเครื่อง

```bash
conda run -n sec-alert311 python -m pytest -q
conda run -n sec-alert311 python -m uvicorn src.api.main:app --reload
```

เมื่อรันแล้ว เปิด Swagger UI ที่ `http://127.0.0.1:8000/docs`

### 3. เช็กว่างานเดินถึงขั้นไหน

อ่าน [WORK_PLAN_TH.md](WORK_PLAN_TH.md) ซึ่งเป็นสถานะงานล่าสุด แล้วดู [TEAM_WORK_PARALLEL_PROPOSAL_TH.md](TEAM_WORK_PARALLEL_PROPOSAL_TH.md) สำหรับหน้าที่และจุดส่งต่องานของแต่ละสาย

สถานะปัจจุบันโดยย่อ:

| ส่วน | สถานะ |
| --- | --- |
| STIX ingestion และ pinned subset | ทำแล้ว |
| Schemas และ taxonomy API | ทำแล้ว |
| `/alerts/infer` | pipeline baseline ใช้งานได้ พร้อม human-review guardrail |
| Retriever / RAG | BM25 baseline พร้อมใช้; platform/source metadata และ subset decision ยังเหลือ |
| Inference, evidence และ grounding | เชื่อมแล้ว; semantic grounding ยังเหลือ |
| Evaluation | กำลังพัฒนาโดยสาย C |
| API integration, CI และ UI | กำลังพัฒนาโดยสาย D |

### 4. ดูภาพรวม API ก่อนอ่าน routes

อ่าน [API_OVERVIEW_TH.md](API_OVERVIEW_TH.md) เพื่อดู Mermaid diagram ของ client → FastAPI → inference pipeline และ endpoint เป้าหมายทั้งหมด

จากนั้นอ่าน [architecture.md](architecture.md) เพื่อเปรียบเทียบ architecture ปัจจุบันแบบ walking skeleton กับ target architecture

### 5. อ่านโค้ดตามเส้นทางข้อมูล

อ่านตามลำดับนี้:

```text
src/schemas.py
  → src/rag/ingest_stix.py
  → src/api/main.py
  → src/api/routes/taxonomy.py
  → src/api/routes/alerts.py
```

| ไฟล์ | หน้าที่ |
| --- | --- |
| `src/schemas.py` | นิยาม `ParsedAlert`, `TechniqueCandidate`, `InferredTechnique` และ `ATTACKInferenceResult` |
| `src/rag/ingest_stix.py` | กรอง STIX ให้เหลือ tactics และ platforms ใน scope; ตัด deprecated/revoked |
| `src/api/main.py` | สร้าง FastAPI app, register routes และเพิ่ม MITRE version header |
| `src/api/routes/taxonomy.py` | list/detail API ของ Technique จาก processed candidates |
| `src/api/routes/alerts.py` | endpoint infer ที่เรียก `src/inference_pipeline.py` |

อ่าน `src/inference_pipeline.py` ต่อจาก route เพื่อเห็นการเชื่อม parser/router → retriever → inferencer → evidence linker → grounding judge. Retriever และ agents อยู่ในระดับ baseline; evaluation และ semantic grounding ยังเป็นงานถัดไป

### 6. อ่าน tests ควบคู่กับโค้ด

```text
tests/test_schemas.py
tests/test_ingest_stix.py
tests/test_taxonomy_api.py
tests/test_alerts_api.py
tests/test_agents.py
tests/test_inference_guardrails.py
tests/test_retriever.py
```

tests บอกพฤติกรรมที่ระบบรับประกันได้แล้วในปัจจุบัน เช่น format ของ Technique ID, การกรอง STIX, taxonomy endpoints, pipeline `/alerts/infer`, BM25 retrieval และ guardrails ของสาย B

## ภาพรวมเส้นทางข้อมูลปัจจุบันและเป้าหมาย

```mermaid
flowchart TD
    A["Alert text"] --> B["FastAPI /alerts/infer"]
    B --> D["Alert Parser"]
    D --> E["Tactic Router"]
    E --> F["BM25 Technique Retriever"]
    G["Pinned ATT&CK STIX 19.1"] --> F
    F --> H["Technique Inferencer"]
    H --> I["Evidence Linker"]
    I --> J["Grounding Judge"]
    J --> K["ATTACKInferenceResult"]
```

## ประเด็นที่ต้องจำให้แม่น

- ข้อมูลหลักของ taxonomy คือ `data/raw/enterprise-attack-19.1.json`; processed candidates และ allowlist อยู่ใน `data/processed/`
- field ที่ใช้ใน candidate และ prediction คือ `tactic: str` ไม่ใช่ `tactics`
- prediction ต้องเลือกจาก retrieved candidates เท่านั้น และมีได้ 1–3 IDs ต่อ alert
- evidence span ต้องเป็นข้อความที่พบจริงใน narrative
- no-match, low confidence หรือผลกำกวมต้องตั้ง `needs_human_review: true`
- ห้ามให้ tests เรียก Gemini หรือ network จริง

## ถ้าจะเริ่มพัฒนาต่อ

ทำตาม [WORK_PLAN_TH.md](WORK_PLAN_TH.md): ปิด gap ของ A/B (metadata, subset และ semantic grounding), C ปิด evaluation และ D เติม API/CI/UI ที่เหลือ
