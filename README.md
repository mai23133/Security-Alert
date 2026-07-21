# Security-Alert

Security-Alert เป็นโปรเจกต์ MVP ช่วงต้นสำหรับรับข้อความ Security Alert แล้วช่วยแนะนำ MITRE ATT&CK Technique ที่เกี่ยวข้องในรูปแบบ advisory tagging เพื่อช่วยนักวิเคราะห์ SOC ตรวจสอบและตัดสินใจต่อ ไม่ใช่ระบบตอบสนองเหตุการณ์อัตโนมัติ

> สถานะปัจจุบัน: early MVP. Endpoint `/alerts/infer` คืน no-match ที่ต้องให้มนุษย์ตรวจแบบ deterministic ระหว่างรอพัฒนา retriever, inferencer, evidence linker, grounding judge และ evaluation pipeline

## ขอบเขตปัจจุบัน

โปรเจกต์นี้จำกัดขอบเขต ATT&CK ไว้เพื่อทำ MVP:

- Dataset: MITRE Enterprise ATT&CK `19.1`
- Tactics: `initial-access`, `execution`, `credential-access`
- Platforms: Windows และ Linux
- วัตถุประสงค์: ให้คำแนะนำสำหรับ analyst review เท่านั้น

## Environment ที่ตรวจแล้ว

ตรวจใน conda environment `sec-alert311`:

```bash
conda run -n sec-alert311 python --version
```

ผลที่ตรวจได้:

```text
Python 3.11.15
```

Library หลักที่โปรเจกต์ใช้:

| Package | Version ที่ตรวจใน `sec-alert311` | ใช้ทำอะไร |
|---|---:|---|
| `google-genai` | `2.12.1` | เรียก Google Gemini API |
| `fastapi` | `0.139.2` | ทำ REST API |
| `uvicorn` | `0.51.0` | รัน ASGI server |
| `pydantic` | `2.13.4` | validate schema/request/response |
| `python-dotenv` | `1.2.2` | โหลดค่า `.env` |
| `pytest` | `9.1.1` | รัน automated tests |
| `httpx` | `0.28.1` | client สำหรับ API test และ SDK |

ผลตรวจล่าสุด: `conda run -n sec-alert311 python -m pytest -q` ผ่าน 17 tests

## ติดตั้งจากศูนย์ด้วย Conda

วิธีนี้ตรงกับ environment ปัจจุบันที่ใช้ชื่อ `sec-alert311`

1. Clone repository:

```bash
git clone https://github.com/mai23133/Security-Alert.git
cd Security-Alert
```

2. สร้าง conda environment:

```bash
conda create -n sec-alert311 python=3.11 -y
conda activate sec-alert311
```

3. อัปเดต pip และติดตั้ง dependencies:

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pytest -q
```

4. เช็คว่าใช้ environment ถูกตัว:

```bash
which python
python --version
python -m pip show google-genai fastapi uvicorn pydantic python-dotenv pytest httpx
```

ควรเห็น Python อยู่ใต้ path ประมาณนี้:

```text
/home/mai/anaconda3/envs/sec-alert311/bin/python
```

## ติดตั้งจากศูนย์โดยไม่ใช้ Conda

ถ้าไม่ต้องการใช้ Anaconda/Conda สามารถใช้ `venv` ได้:

```bash
git clone https://github.com/mai23133/Security-Alert.git
cd Security-Alert
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pytest -q
```

## ตั้งค่า Gemini API Key

โปรเจกต์อ่าน key ได้จาก `GOOGLE_API_KEY` หรือ `GEMINI_API_KEY` โดยแนะนำให้ใช้ `GOOGLE_API_KEY`

> API และ tests ในสถานะปัจจุบันไม่เรียก Gemini จึงไม่ต้องมี key เพื่อ install, run หรือทดสอบ `/alerts/infer` แบบ no-match. Key จะจำเป็นเมื่อเชื่อม inference pipeline จริงในภายหลัง

สร้าง `.env` จากไฟล์ตัวอย่าง:

```bash
cp .env.example .env
```

แก้ไฟล์ `.env`:

```bash
GOOGLE_API_KEY=your_google_api_key_here
```

ห้าม commit ไฟล์ `.env` หรือ secret จริงขึ้น repository เพราะ `.env` ถูก ignore ไว้ใน `.gitignore`

ถ้ายังไม่มี key ให้สร้างจาก Google AI Studio:

```text
https://aistudio.google.com/app/apikey
```

## โครงสร้างโปรเจกต์

```text
src/
  api/                 FastAPI application และ routes
  agents/              Alert parser และ tactic router สำหรับ pipeline ในอนาคต
  rag/                 STIX ingestion และส่วน retrieval ที่กำลังพัฒนา
  schemas.py           Pydantic schemas สำหรับ request/response และ ATT&CK data
data/
  raw/                 MITRE ATT&CK STIX bundle ที่ pin version ไว้
  processed/           ไฟล์ technique candidates ที่ generate แล้ว
prompts/v1/            Prompt files สำหรับ versioned prompts ในอนาคต
tests/                 Tests สำหรับ schema, ingestion และ taxonomy API
eval/                  Evaluation placeholders
```

## เตรียมข้อมูล ATT&CK

API taxonomy อ่านข้อมูลจากไฟล์ processed เหล่านี้:

- `data/processed/technique_ids.json`
- `data/processed/technique_candidates.json`

ถ้าต้องการ regenerate จาก raw STIX bundle:

```bash
python -m src.rag.ingest_stix
```

## รัน API

```bash
python -m uvicorn src.api.main:app --reload
```

จากนั้นเปิด:

- API root: `http://127.0.0.1:8000/`
- OpenAPI docs: `http://127.0.0.1:8000/docs`

ทุก response จะมี header:

```text
X-MITRE-ATTaCK-Version: enterprise-attack-19.1
```

## ตัวอย่างเรียก API

Health check:

```bash
curl http://127.0.0.1:8000/
```

ดูรายการ technique ทั้งหมดใน scope:

```bash
curl http://127.0.0.1:8000/taxonomy/techniques
```

Filter ตาม tactic:

```bash
curl "http://127.0.0.1:8000/taxonomy/techniques?tactic=credential-access"
```

ดู technique รายตัว:

```bash
curl http://127.0.0.1:8000/taxonomy/techniques/T1110
```

Infer ATT&CK tags จาก alert:

```bash
curl -X POST http://127.0.0.1:8000/alerts/infer \
  -H "Content-Type: application/json" \
  -d '{
    "alert_id": "demo-001",
    "narrative": "Host WIN-SRV-04 logged 847 failed RDP authentication attempts from IP 203.0.113.44, followed by a successful login and execution of encoded PowerShell."
  }'
```

หมายเหตุ: endpoint นี้ยังไม่เชื่อม inference pipeline จึงคืน no-match พร้อม human-review flag และไม่เรียก Gemini

ผลลัพธ์ปัจจุบันจะมี `inferred_techniques` และ `candidates_considered` เป็นรายการว่าง และ `needs_human_review` เป็น `true` เสมอ จึงเป็นผลสำหรับทดสอบ API contract เท่านั้น ไม่ใช่การวิเคราะห์ ATT&CK

## Components ที่มีแล้ว

- `GET /` สำหรับ health check และ STIX version
- `GET /taxonomy/techniques` สำหรับ list technique candidates
- `GET /taxonomy/techniques/{technique_id}` สำหรับดูรายละเอียด technique จาก pinned subset
- `POST /alerts/infer` สำหรับรับ alert narrative และคืน no-match ที่ต้องให้มนุษย์ตรวจจนกว่าจะเชื่อม inference pipeline
- `src/rag/ingest_stix.py` สำหรับ filter MITRE ATT&CK STIX bundle ให้เหลือ scope ของ MVP
- `src/agents/gemini_client.py` สำหรับ pipeline Gemini ที่ยังไม่เชื่อมกับ endpoint

## Development และตรวจสอบ

ตรวจ syntax:

```bash
python -m compileall -q src eval tests
```

รัน tests:

```bash
python -m pytest -q
```

ผลตรวจล่าสุดใน `sec-alert311`:

- `python -m compileall -q src eval tests`: ผ่าน
- `python -m pytest -q`: `17 passed`

## Roadmap

แผนงานรายละเอียดอยู่ใน `WORK_PLAN_TH.md` โดยงานสำคัญถัดไปคือ:

- เชื่อม `/alerts/infer` กับ retrieval/inference pipeline จริง
- ทำ retrieval จาก pinned ATT&CK subset
- ทำ technique inferencer, evidence linker และ grounding judge
- เพิ่ม tests ที่ mock Gemini เพื่อให้รันซ้ำได้โดยไม่ใช้ API quota
- สร้าง evaluation dataset และ metrics
- ปรับ API validation, error handling, config และ CORS สำหรับ production

## Security และ Privacy

Security alert อาจมีข้อมูลอ่อนไหว เช่น IP address, hostname, username, domain, file path และ hash จึงควรถือว่า `.env`, raw alerts, logs และ evaluation data เป็นข้อมูล sensitive จนกว่าจะ sanitize แล้ว

ระบบนี้ออกแบบมาเพื่อช่วย analyst เท่านั้น การ map ATT&CK ที่ระบบแนะนำควรถูกตรวจสอบโดยมนุษย์ก่อนนำไปใช้ตัดสินใจเชิงปฏิบัติการ

## Attribution

โปรเจกต์นี้ใช้ข้อมูล MITRE ATT&CK Enterprise. MITRE ATT&CK เป็น trademark ของ The MITRE Corporation ดู framework และเงื่อนไขต้นทางได้ที่ https://attack.mitre.org/
