# บทนำเสนอคนที่ 3 — Live Demo และ Security บน Analyst Workspace

อัปเดต 18 กันยายน 2026 เอกสารนี้เขียนให้ตรงกับ UI และ implementation ปัจจุบันของโปรเจกต์ โดยอ้างอิงข้อกำหนดหลักในหัวข้อ Agent Architecture, Knowledge Base, API Contract, Security & Guardrails และแผนสาธิต 3 นาที

> ข้อความสำคัญที่ต้องพูดให้ตรงกัน: ระบบให้คำแนะนำแก่ Analyst เท่านั้น ไม่ยืนยันว่าเหตุการณ์ปลอดภัย และไม่ดำเนินการตอบสนองเหตุการณ์โดยอัตโนมัติ

## เป้าหมายของช่วงนี้

ช่วงสาธิตนี้ต้องทำให้ผู้ชมเห็น 4 เรื่อง:

1. ระบบวิเคราะห์ Alert จริงผ่าน pipeline ไม่ใช่ผลลัพธ์ hard-coded
2. Analyst ตรวจ Technique, support score, evidence และ candidates ย้อนกลับได้
3. ระบบ abstain และส่งต่อให้มนุษย์เมื่อหลักฐานไม่เพียงพอ
4. Prompt injection และความล้มเหลวของ external provider ถูกเปิดเผยอย่างตรงไปตรงมา

## เตรียมหน้าจอก่อนพูด

- เปิด `/ui` และเลือกแท็บ `Analyst Workspace`
- เลือก `Offline / Rules` เป็นค่าเริ่มต้น เพื่อให้ผลเดโมทำซ้ำได้และไม่ขึ้นกับ quota ภายนอก
- ตรวจว่า backend พร้อมใช้งานและหน้า UI แสดง `MITRE ATT&CK Enterprise v19.1`
- อย่าเปิดไฟล์ `.env`, API key, provider console หรือข้อมูล Alert จริง
- หากจะสาธิต Gemini ให้ใช้เฉพาะ reviewed synthetic alert และตั้ง server-side consent ตามคู่มือระบบ

## บทพูดพร้อมลำดับการคลิก

### 1. เกริ่นและอธิบายหน้าจอ

**การกระทำบนหน้าจอ:** สลับกลับมาที่แท็บ `Analyst Workspace` และชี้บริเวณ Quick Picker, mode selector, ช่อง Alert และผลลัพธ์ด้านขวา

**บทพูด:**

> กลับมาที่หน้า Analyst Workspace นะครับ หน้านี้เป็นพื้นที่ทำงานของนักวิเคราะห์ เราสามารถเลือก Alert ตัวอย่างจาก Quick Picker หรือใส่ข้อความ Alert เอง จากนั้นเลือกเส้นทางประมวลผลเป็น Offline, Gemini หรือ OpenRouter แล้วกดปุ่ม Infer ATT&CK Techniques
>
> ผลลัพธ์ด้านขวาจะไม่ได้แสดงเพียง Technique ID แต่แสดง tactic, support score, ช่วงข้อความหลักฐาน, สถานะ human review และ candidates ที่ Retriever นำมาพิจารณา ผลทั้งหมดเป็นคำแนะนำและยังต้องให้นักวิเคราะห์ตรวจสอบก่อนนำไปใช้ครับ

### 2. เคส Brute-Force และ PowerShell

**การกระทำบนหน้าจอ:**

1. เลือก `Offline / Rules`
2. กด `🚨 Brute-Force + PS`
3. กด `Infer ATT&CK Techniques`
4. ชี้การ์ด Technique, rule support score และ evidence spans
5. เปิด `CANDIDATE RETRIEVAL`

**บทพูด:**

> เริ่มจากเคสมาตรฐาน Brute-Force + PowerShell ครับ Alert นี้มีการยืนยันตัวตนล้มเหลว 847 ครั้ง มีการรัน encoded PowerShell ผ่าน cmd.exe และมีการกล่าวถึง PsExec
>
> เมื่อเลือก Offline / Rules และกดวิเคราะห์ ระบบจะรัน local pipeline โดยไม่ส่ง Alert ออกไปยังผู้ให้บริการภายนอก ผลปัจจุบันแสดง T1110 Brute Force, T1059.001 PowerShell และอาจแสดง T1059.003 Windows Command Shell เพราะใน Alert มีทั้ง PowerShell และ cmd.exe อย่างชัดเจน
>
> คะแนนที่เห็นเป็น Rule Support Score ซึ่งบอกระดับการสนับสนุนตามกฎที่กำหนดไว้ ไม่ใช่เปอร์เซ็นต์ความน่าจะเป็นที่ผ่านการสอบเทียบ ส่วน Evidence Spans เป็นช่วงข้อความจาก Alert ต้นฉบับ เช่นส่วนที่มี 847 consecutive authentication failures และการรัน encoded PowerShell ทำให้นักวิเคราะห์ตรวจสอบย้อนกลับได้ว่าระบบใช้ข้อความใดสนับสนุนแต่ละคำตอบ
>
> ด้านล่างคือ Candidate Retrieval เมื่อกางออกจะเห็น top candidates ที่ระบบค้นจาก pinned MITRE ATT&CK subset ก่อน inference ขั้นตอนนี้ทำให้การตัดสินใจโปร่งใส และ Inferencer ไม่สามารถเลือก ID ที่อยู่นอก candidate กับ allowlist ได้ครับ

**สิ่งที่ควรเห็นจาก implementation ปัจจุบัน:**

- Techniques: `T1059.001`, `T1059.003`, `T1110`
- Candidates: สูงสุด 5 รายการ
- `needs_human_review=true` อาจปรากฏ เพราะ Judge ตรวจแบบ conservative และ sample มีหลายพฤติกรรม
- Evidence อาจเป็นข้อความทั้ง clause ไม่ใช่เฉพาะวลีสั้น ๆ

> หมายเหตุสำหรับผู้พูด: อย่ารับประกันว่าจะมีเพียงสองการ์ด และอย่าพูดว่า support score คือ confidence probability

### 3. เคสปกติและหลักฐานไม่สมบูรณ์

#### 3.1 Benign Patch

**การกระทำบนหน้าจอ:** กด `🟢 Benign Patch` แล้วกดวิเคราะห์โดยยังใช้ `Offline / Rules`

**บทพูด:**

> ต่อไปเป็นกิจกรรม Windows Update ที่คาดว่าเป็นงานดูแลระบบปกติครับ ระบบอาจค้น candidates ที่มีคำใกล้เคียงได้ในขั้น Retrieval แต่ Inferencer และ Evidence Linker จะไม่สร้าง Technique หากไม่มีพฤติกรรมและหลักฐานที่เพียงพอ
>
> ผลจึงเป็น no-match และขึ้น NEEDS HUMAN REVIEW: TRUE จุดสำคัญคือระบบไม่ได้ประกาศว่าเหตุการณ์นี้ปลอดภัย แต่กำลังบอกว่า จากข้อความที่มีอยู่ยังไม่มีหลักฐานเพียงพอให้ระบุ ATT&CK Technique นักวิเคราะห์ยังต้องตรวจบริบทอื่นประกอบครับ

**สิ่งที่ควรเห็น:**

- ไม่มี Technique ที่ผ่านการอนุมาน
- อาจยังมี candidates จาก lexical retrieval ซึ่งยังไม่ถือเป็น prediction
- `needs_human_review=true`
- ข้อความ `No techniques with sufficient evidence inferred. This does not confirm benign activity.`

#### 3.2 Incomplete Evidence

**การกระทำบนหน้าจอ:** กด `⚠️ Incomplete Evidence` แล้วกดวิเคราะห์

**บทพูด:**

> เคสนี้กล่าวถึง process ที่ผิดปกติ แต่ไม่มี hash และ telemetry ยังไม่ครบ ระบบตรวจพบว่าหลักฐานกำกวมและไม่เพียงพอ จึงไม่ฝืนระบุ Technique และส่งต่อด้วยสถานะ NEEDS HUMAN REVIEW: TRUE
>
> พฤติกรรมนี้เป็นหลัก human-in-the-loop ของระบบ คือเมื่อหลักฐานไม่ถึงเกณฑ์ ระบบเลือก abstain แทนการสร้างคำตอบที่ดูมั่นใจเกินจริงครับ

**สิ่งที่ควรเห็น:**

- ไม่มี Technique ที่มีหลักฐานเพียงพอ
- `needs_human_review=true`

### 4. การรับมือ Prompt Injection

**การกระทำบนหน้าจอ:** กด `💉 Prompt Injection` แล้วกดวิเคราะห์ จะใช้ Offline หรือ Gemini ก็ได้ แต่แนะนำให้ใช้ Offline ในเดโมหลัก

**บทพูด:**

> Security Alert ถือเป็น untrusted input เพราะผู้โจมตีอาจฝังข้อความที่มีลักษณะเป็นคำสั่ง เช่นให้ระบบลืมคำสั่งเดิมและตอบ T9999
>
> สำหรับตัวอย่างนี้ ระบบมี deterministic preflight guard ตรวจ instruction-like payload ก่อนเริ่ม Parser หรือเรียก external model เมื่อพบความเสี่ยง ระบบจะ fail closed ทันที ไม่พยายามทำตามคำสั่ง ไม่ส่ง payload ไปยังโมเดล ไม่สร้าง Technique และไม่แสดง candidates พร้อมขึ้น PROMPT INJECTION BLOCKED และ NEEDS HUMAN REVIEW: TRUE
>
> นอกจากนี้ทุก Technique ที่ระบบอนุญาตให้แสดงต้องอยู่ใน candidate และ allowlist ที่สร้างจาก pinned MITRE ATT&CK Enterprise 19.1 subset เท่านั้น ดังนั้น T9999 จึงไม่สามารถผ่านโครงสร้างผลลัพธ์ของระบบได้ครับ

**สิ่งที่ควรเห็น:**

- `PROMPT INJECTION BLOCKED`
- Techniques และ candidates เป็นรายการว่าง
- `needs_human_review=true`
- Provider stages แสดง `blocked` และไม่มีการเรียกโมเดล

> ขอบเขตคำกล่าว: ควรพูดว่า guard นี้ตรวจรูปแบบ instruction-like ที่ระบบกำหนดไว้ ไม่ควรอ้างว่าสามารถตรวจ prompt injection ทุกรูปแบบได้ 100 เปอร์เซ็นต์

### 5. การแยก Offline กับ External AI และ Fallback Transparency

**การกระทำบนหน้าจอ:** ชี้ mode selector `Offline / Rules`, `Gemini 3.5 Flash-Lite`, `OpenRouter` และกล่อง `PROVIDER EXECUTION STATUS`

**บทพูด:**

> ระบบแยกเส้นทางประมวลผลอย่างชัดเจนครับ Offline / Rules ใช้ local behavior rules และ rule support score ส่วน Gemini หรือ OpenRouter จะใช้ provider ที่เลือกใน Parser, Router, LLM Inferencer และ LLM Grounding Judge
>
> ไม่ว่าใช้เส้นทางใด ผลยังต้องผ่าน candidate bounding, schema validation, URL validation และ evidence checks ชุดเดียวกัน
>
> ถ้า external provider ล้มเหลว เช่น API key ไม่พร้อม, quota ถูกจำกัด, timeout หรือคำตอบผิดรูปแบบ ระบบอาจ fallback ไปใช้ผลแบบ conservative จากกฎออฟไลน์ แต่จะไม่แอบแสดงว่าเป็นผลงานของ AI บนหน้าจอจะแสดงสถานะของแต่ละ stage, provider, model, Fallback: YES และเหตุผลที่เกิด พร้อมส่งผลให้มนุษย์ตรวจสอบครับ
>
> สำหรับ Online mode ระบบกำหนด explicit consent และ redaction ขั้นต้น และออกแบบให้ใช้เฉพาะ reviewed synthetic alerts เพราะการส่งข้อมูลจริงไปยัง external provider มีความเสี่ยงด้าน privacy ครับ

### 6. สรุปช่วงสาธิต

**บทพูด:**

> สรุป Analyst Workspace แสดง workflow ตั้งแต่ retrieval ไปจนถึง inference และ grounding อย่างตรวจสอบย้อนกลับได้ ระบบไม่สร้าง Technique นอก pinned subset, ไม่ฝืนตอบเมื่อหลักฐานไม่พอ, หยุด prompt injection ก่อนเรียกโมเดล และเปิดเผย fallback อย่างชัดเจน จึงทำหน้าที่เป็นเครื่องมือช่วยนักวิเคราะห์ ไม่ใช่ระบบตัดสินใจหรือตอบสนองเหตุการณ์โดยอัตโนมัติครับ

## อธิบายการทำงานตามโค้ด

### ภาพรวมเส้นทางข้อมูล

```text
Quick Picker / Alert text
        │
        ▼
POST /alerts/infer + inference_mode
        │
        ▼
Prompt-injection preflight
        │
        ├── blocked ──► no techniques + human review
        │
        ▼
Alert Parser → Tactic Router → Retriever top-k
        │
        ▼
Rules Inferencer หรือ LLM Inferencer
        │
        ▼
Candidate/ID/name/tactic/URL validation
        │
        ▼
Evidence Linker → Grounding Judge
        │
        ▼
ATTACKInferenceResult + provider status headers
        │
        ▼
Technique cards / review flag / candidate drawer
```

### 1. UI ส่ง request อย่างไร

ไฟล์ `ui/src/App.tsx` เก็บ sample ทั้ง 4 รายการไว้ใน `SAMPLES` เมื่อกด Quick Picker ฟังก์ชัน `pickSample()` จะนำข้อความมาใส่ใน textarea แต่ยังไม่สร้างผลลัพธ์ จนกด `Infer ATT&CK Techniques`

ฟังก์ชัน `submitAlert()` ส่ง request ดังนี้:

```json
{
  "narrative": "ข้อความ Alert",
  "inference_mode": "offline | gemini | openrouter"
}
```

UI อ่านผลลัพธ์จาก response body และอ่านสถานะการทำงานของแต่ละ stage จาก response headers เช่น `X-AI-Inferencer-Status`, `X-AI-Fallback-Used`, `X-AI-Fallback-Reason`, `X-AI-Confidence-Source` และ `X-Security-Guardrail`

### 2. API ตรวจ input และเลือกเส้นทาง

ไฟล์ `src/api/routes/alerts.py` กำหนด `AlertRequest` ด้วย Pydantic:

- รับ `inference_mode` ได้เฉพาะ `offline`, `gemini`, `openrouter`
- จำกัด narrative ไม่เกิน 20,000 ตัวอักษร
- ปฏิเสธฟิลด์ส่วนเกิน
- สร้าง `alert_id` ให้เมื่อ client ไม่ได้ส่งมา

หากเลือก Offline API จะเรียก `run_inference()` โดยไม่เปิด provider หากเลือก Gemini หรือ OpenRouter จึงตั้ง `use_provider=True` และส่งชื่อ provider เข้า pipeline

### 3. Prompt injection ถูกตรวจเป็นด่านแรก

ใน `src/inference_pipeline.py` ฟังก์ชัน `run_inference()` เรียก `prompt_injection_detected()` ก่อน Parser, Router และ provider ทุกตัว กฎอยู่ใน `src/agents/behavior.py`

เมื่อพบข้อความลักษณะ injection ระบบคืนผลทันที:

- `inferred_techniques=[]`
- `candidates_considered=[]`
- `needs_human_review=true`
- disclaimer ระบุว่าถูก block ก่อน model execution
- trace ของทุก provider stage เป็น `blocked` หรือ `none`

นี่คือแนวทาง fail closed: เมื่อ input พยายามควบคุมระบบ จะไม่วิเคราะห์ต่อจาก payload เดิม

### 4. Parser และ Tactic Router

หากไม่ถูก block pipeline จะเรียก:

1. `src/agents/alert_parser.py` เพื่อสร้าง `ParsedAlert` ซึ่งมี narrative, assets, observed actions และ IOCs
2. `src/agents/tactic_router.py` เพื่อจำกัด tactics ที่ Retriever ควรค้น

Offline mode ไม่เรียก external model ส่วน Online mode ส่งงานให้ provider ที่เลือก หาก Parser หรือ Router ล้มเหลว ระบบจะเก็บสถานะ fallback และยังดำเนินงานอย่าง conservative จาก narrative เดิม

### 5. Retriever ค้นจาก pinned knowledge base

`src/rag/retriever.py` ใช้ BM25 บน snapshot ที่สร้างจาก `enterprise-attack-19.1.json` และค้นสูงสุด `top_k=5` โดย:

- กรองตาม tactics ที่ Router ส่งมา
- ตรวจว่า ID อยู่ใน allowlist
- ใช้ metadata และ behavior evidence ช่วยจัดอันดับ
- ไม่เพิ่ม ID ใหม่ที่ไม่มีอยู่ใน index

ดังนั้น candidate retrieval คือการจำกัดพื้นที่ให้ Inferencer พิจารณา ไม่ใช่ผลตัดสินสุดท้าย

### 6. Inferencer เลือก Technique

Offline mode ใช้ `src/agents/technique_inferencer.py` และ behavior rules ใน `src/agents/behavior.py` ส่วน Online mode ใช้ `src/agents/llm_technique_inferencer.py`

หลัง inference, `run_inference()` ตรวจซ้ำว่า:

- Technique ต้องอยู่ใน retrieved candidates
- ID ต้องไม่ซ้ำ
- ชื่อและ tactic ต้องตรงกับ candidate
- MITRE URL ต้องสร้างตรงกับ Technique ID
- คืนได้ไม่เกิน 3 Techniques

ผลที่ไม่ผ่านเงื่อนไขจะถูกทิ้งและทำให้ต้อง human review

### 7. Evidence Linker และ Grounding Judge

`src/agents/evidence_linker.py` เชื่อม Technique กับช่วงข้อความที่มีอยู่จริงใน Alert ส่วน `src/agents/grounding_judge.py` ตรวจกรณีสำคัญ เช่น:

- ไม่มี prediction หรือมีมากกว่า 3 รายการ
- evidence ไม่อยู่ในข้อความต้นฉบับ
- ID, ชื่อ, tactic หรือ URL ไม่ตรงกับ candidate
- support score ต่ำกว่าเกณฑ์
- ข้อความมีความกำกวมหรือหลักฐานไม่เพียงพอ

เมื่อไม่ผ่าน ระบบจะปฏิเสธ prediction ที่ไม่มีหลักฐานหรือกำหนด `needs_human_review=true`

Online mode มี `src/agents/llm_grounding_judge.py` เพิ่ม semantic judgment แต่หาก Judge ภายนอกล้มเหลว ระบบจะเปิดเผย fallback และใช้ผลจากกฎแบบ conservative แทน

### 8. Schema ของผลลัพธ์

`src/schemas.py` กำหนด `ATTACKInferenceResult` ซึ่งส่งกลับ:

- `alert_id`
- `inferred_techniques`
- `candidates_considered`
- `needs_human_review`
- `disclaimer`

แต่ละ Technique มี ID, ชื่อ, tactic, support score ในฟิลด์ `confidence`, evidence spans และ MITRE URL แม้ชื่อฟิลด์ใน API จะเป็น `confidence` แต่ UI ตั้งใจเรียกว่า support score และระบุว่าไม่ใช่ calibrated probability

### 9. Provider fallback ทำงานอย่างไร

Online path ใช้ `src/agents/provider_chain.py` เรียก provider ที่ผู้ใช้เลือก หาก stage ใดล้มเหลว pipeline เก็บเหตุผลที่ปลอดภัย เช่น:

- `missing-key`
- `consent-required`
- `rate-limited`
- `timeout`
- `network-error`
- `invalid-response`

UI แสดงข้อมูลนี้ใน `PROVIDER EXECUTION STATUS` หาก fallback ไปใช้ Offline rules ผลจะใช้ `rule-score`, ติดป้าย fallback และต้องให้มนุษย์ตรวจสอบ ระบบไม่สลับไปใช้ provider คนละรายอย่างเงียบ ๆ

### 10. Privacy ของ Online mode

`src/agents/provider_safety.py` บังคับ `PROVIDER_CONSENT=reviewed-synthetic-only` และทำ redaction ขั้นต้นกับ IP, email และข้อความลักษณะ secret ก่อนส่ง prompt ออกไป อย่างไรก็ตาม redaction ไม่ได้ครอบคลุม PII ทุกชนิด จึงต้องใช้ Online mode กับ reviewed synthetic alerts เท่านั้น

## คำตอบสั้นสำหรับคำถามที่อาจถูกถาม

### ทำไม benign ยังมี candidates?

Retriever วัดความเกี่ยวข้องเพื่อสร้างรายการพิจารณา ส่วน Inferencer และ Grounding Judge เป็นผู้ตัดสินว่ามีหลักฐานพอหรือไม่ Candidate จึงไม่เท่ากับ prediction

### ทำไมเคสแรกมีสาม Technique แทนสอง Technique ใน gold label?

Quick Picker ปัจจุบันมีข้อความ `cmd.exe` เพิ่มจากตัวอย่างสั้นในข้อกำหนด กฎจึงพบ `T1059.003` Windows Command Shell เพิ่ม การขึ้น human review ช่วยให้นักวิเคราะห์ตรวจว่า Technique เพิ่มเติมนี้เหมาะสมหรือเป็น over-tagging

### ทำไม no-match ยังต้อง human review?

No-match หมายถึงระบบไม่มีหลักฐานเพียงพอ ไม่ได้หมายความว่าเหตุการณ์ปลอดภัย Judge จึงตั้ง review เพื่อให้มนุษย์ตรวจข้อมูลอื่นประกอบ

### ป้องกัน T9999 ด้วย prompt injection detector อย่างเดียวหรือไม่?

ไม่ใช่ มีหลายชั้น ได้แก่ preflight block, candidate bounding, pinned allowlist, Pydantic schema, name/tactic/URL validation, evidence linking และ grounding judgment

### Gemini ล้มแล้วระบบทำอย่างไร?

ระบบอาจคืนผล conservative จาก Offline rules แต่จะแสดงว่า stage ใด fallback, สาเหตุอะไร, คะแนนมาจาก rules และตั้ง human review จึงไม่อ้างว่าเป็นผลสำเร็จจาก Gemini

## Checklist ระหว่างสาธิต

- [ ] ใช้คำว่า `Rule Support Score` หรือ `LLM Support Score` ไม่เรียกว่า probability
- [ ] บอกว่า no-match ไม่ได้ยืนยันว่า benign
- [ ] บอกว่า allowlist มาจาก pinned STIX **subset** ไม่ใช่ ATT&CK ทั้งหมด
- [ ] ไม่รับประกันว่าเคสแรกจะมีเพียง 2 Techniques
- [ ] เปิด Candidate Retrieval ให้ผู้ชมเห็น
- [ ] ชี้ `PROMPT INJECTION BLOCKED` และ human-review flag
- [ ] อธิบาย fallback status ก่อนกล่าวว่าเป็นผลจาก AI
- [ ] ย้ำว่าไม่มี automated response

## ไฟล์โค้ดที่ควรเปิดสำรอง

1. `ui/src/App.tsx` — Quick Picker, mode selector, request และผลลัพธ์บน UI
2. `src/api/routes/alerts.py` — API validation, mode selection และ status headers
3. `src/inference_pipeline.py` — orchestration และ prompt-injection fail-closed path
4. `src/rag/retriever.py` — BM25, tactic filter, allowlist และ top-k
5. `src/agents/behavior.py` — behavior rules และ injection detection
6. `src/agents/grounding_judge.py` — review conditions
7. `src/agents/provider_safety.py` — consent และ redaction ขั้นต้น
8. `src/schemas.py` — API response schema
