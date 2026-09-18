# คำถาม–คำตอบสำหรับการนำเสนอระบบ Security Alert → MITRE ATT&CK

เอกสารนี้รวบรวมคำถามที่อาจได้รับระหว่างการนำเสนอ พร้อมคำตอบสั้นที่สอดคล้องกับ implementation ปัจจุบัน

เอกสารข้อกำหนดหลักคือ `security-alert-attack-technique-inference.md` หากเนื้อหาในเอกสารนี้ขัดกับข้อกำหนด ให้ยึดเอกสารข้อกำหนดเป็น Source of Truth

## 1. คำถามภาพรวมระบบ

### 1.1 โปรเจกต์นี้แก้ปัญหาอะไร?

ระบบช่วยนักวิเคราะห์จับคู่ข้อความ Security Alert กับ MITRE ATT&CK Technique โดยคืน Technique ID, ชื่อ, Tactic, Confidence และข้อความหลักฐาน ระบบเป็นเครื่องมือแนะนำเท่านั้น ไม่ได้ตอบสนองหรือบล็อกเหตุการณ์อัตโนมัติ

### 1.2 Flow ของระบบเป็นอย่างไร?

ผู้ใช้ส่ง Alert เข้า API จากนั้น Parser แยกข้อมูล Router เลือก Tactic Retriever ค้น Candidate จาก MITRE ATT&CK แล้ว Inferencer เลือก Technique ก่อนส่งผ่าน Evidence Linker และ Grounding Judge เพื่อยืนยันว่ามีหลักฐานรองรับ

```text
Alert
→ Parser
→ Tactic Router
→ Retriever
→ Technique Inferencer
→ Evidence Linker
→ Grounding Judge
→ Result
```

### 1.3 ทำไมต้องใช้ MITRE ATT&CK?

MITRE ATT&CK เป็นฐานความรู้มาตรฐานที่อธิบายพฤติกรรมและเทคนิคของผู้โจมตี ทำให้ผลลัพธ์มีรหัสและคำอธิบายที่อ้างอิงร่วมกันได้ แทนการสร้างชื่อพฤติกรรมขึ้นเอง

### 1.4 ทำไมต้องตรึง STIX version 19.1?

เพื่อให้ทุกครั้งที่รันใช้ Taxonomy ชุดเดียวกันและประเมินผลซ้ำได้ หากใช้ข้อมูลออนไลน์ที่เปลี่ยนตลอด Candidate และผลประเมินอาจไม่เหมือนเดิม

## 2. คำถามเกี่ยวกับ RAG และ Retriever

### 2.1 RAG ในโปรเจกต์นี้คืออะไร?

ระบบค้น Top-k Technique จาก pinned MITRE ATT&CK ก่อน แล้วส่ง Alert พร้อม Candidate เหล่านั้นให้ LLM เลือกคำตอบ LLM จึงไม่ได้ตอบจากความจำของโมเดลเพียงอย่างเดียว

```text
Alert
→ BM25 Retrieval
→ Top-k Candidates
→ LLM Inference
```

### 2.2 Retriever ใช้อะไรในการค้นหา?

ใช้ BM25 โดยค้นจาก Technique ID, ชื่อ และคำอธิบาย Technique พร้อมกรองด้วย Tactic และ Allowlist นอกจากนี้ยังมี behavior-rule reranking เพื่อเพิ่มคะแนนให้ Candidate ที่มีหลักฐานชัดเจน

### 2.3 ทำไมใช้ BM25 แทน Vector Database?

BM25 ทำงานออฟไลน์ อธิบายคะแนนได้ ทำซ้ำได้ และเหมาะกับขอบเขตข้อมูลขนาดเล็กของโครงการ ส่วน `embed()` ถูกเตรียมเป็น contract สำหรับเปลี่ยนเป็น dense retrieval ในอนาคต แต่ยังไม่ได้ใช้งานจริง

### 2.4 Stop words ถูกตัดหรือไม่?

ปัจจุบันยังไม่มี explicit stop-word removal แต่ BM25 ลดน้ำหนักคำที่ปรากฏบ่อยด้วยค่า IDF โดยธรรมชาติ Tokenizer ปัจจุบันทำ lowercase, แยกคำ และขยาย alias เช่น `rdp` เป็น `remote desktop protocol`

### 2.5 ทำไมต้องมี Tactic Router ก่อน Retriever?

เพื่อจำกัดพื้นที่ค้นหา เช่น หาก Alert เกี่ยวกับ PowerShell Router จะเลือก Execution ทำให้ Retriever เน้นค้น Technique ในกลุ่มนั้นและลด Candidate ที่ไม่เกี่ยวข้อง

### 2.6 ถ้า Tactic Router เลือกผิดจะทำอย่างไร?

หาก Router ตอบผิดรูปแบบหรือล้มเหลว ระบบจะค้นทั้งสาม Tactic ที่อยู่ในขอบเขตแทน วิธีนี้ลดความเสี่ยงที่ Technique ที่ถูกต้องจะถูกตัดออกเพราะ Router ผิด

### 2.7 `top_k=5` หมายความว่าอะไร?

Retriever จะคืน Candidate ที่มีคะแนนสูงสุดไม่เกินห้ารายการให้ Inferencer พิจารณา ในผลประเมิน Offline Runtime ปัจจุบัน Recall@1 ประมาณ 81.1%, Recall@3 ประมาณ 97.3% และ Recall@5 เท่ากับ 100% บนชุดข้อมูล 35 รายการ

## 3. คำถามเกี่ยวกับ LLM

### 3.1 LLM ทำหน้าที่อะไรบ้าง?

ในโหมดออนไลน์ LLM มีสี่หน้าที่ ได้แก่ แยก Alert เป็นโครงสร้าง เลือก Tactic เลือก Technique จาก Candidate และตรวจเชิงความหมายว่าหลักฐานสนับสนุน Technique หรือไม่

### 3.2 ทำไมต้องแบ่ง LLM เป็นหลาย Agent?

เพื่อแยกหน้าที่และตรวจสอบแต่ละขั้นได้ หากใช้ Prompt เดียวทำทุกอย่าง จะตรวจได้ยากว่าความผิดพลาดเกิดที่ Parsing, Routing, Retrieval หรือ Inference และทำ fallback รายขั้นได้ยากกว่า

### 3.3 LLM สร้าง Technique ID ขึ้นเองได้หรือไม่?

ไม่ได้ Inferencer เลือกได้เฉพาะ ID ที่ Retriever ส่งมา และ Candidate ต้องอยู่ใน pinned allowlist หาก LLM ตอบ `T9999` หรือ ID นอก Candidate ระบบจะปฏิเสธทันที

```python
if tid not in by_id:
    raise ValueError()
```

### 3.4 Confidence หมายถึงโอกาสถูกกี่เปอร์เซ็นต์หรือไม่?

ไม่ใช่ Confidence เป็นคะแนนที่บอกว่าหลักฐานสนับสนุน Technique มากเพียงใด แต่ยังไม่ได้ calibrate เป็นความน่าจะเป็น จึงไม่ควรอ่านค่า 0.9 ว่าถูกแน่นอน 90%

### 3.5 ถ้า LLM ตอบไม่เป็น JSON จะเกิดอะไรขึ้น?

ระบบจะปฏิเสธคำตอบและ fallback ไปใช้ deterministic behavior rules พร้อมตั้ง `needs_human_review=True` และบันทึกสาเหตุเป็น `invalid-response`

### 3.6 ถ้า Gemini ใช้งานไม่ได้ ระบบเปลี่ยนไป OpenRouter หรือไม่?

ไม่เปลี่ยนอัตโนมัติ ระบบใช้เฉพาะ Provider ที่ผู้ใช้เลือกเพื่อไม่ให้ข้อมูลถูกส่งไปยังผู้ให้บริการอื่นโดยไม่ได้รับอนุญาต หาก Provider ล้ม ระบบจะ fallback เป็น Offline Rules

### 3.7 `ProviderChain` ทำหน้าที่อะไร?

ทำหน้าที่เลือก Gemini หรือ OpenRouter บันทึก Provider และ Model ลง trace จำแนกสาเหตุของข้อผิดพลาด และใช้ circuit breaker หยุดเรียก Provider ซ้ำหลังล้มเหลวภายใน Request เดียวกัน

### 3.8 Offline mode ยังเป็น LLM อยู่หรือไม่?

ไม่ใช่ Offline mode ไม่เรียก External LLM ใช้ narrative ต้นฉบับ ค้นทั้งสาม Tactic และใช้ deterministic behavior rules ในการเลือก Technique

## 4. คำถามเกี่ยวกับ Evidence และ Grounding

### 4.1 ป้องกัน LLM แต่งหลักฐานอย่างไร?

LLM ไม่ได้ส่งข้อความหลักฐานใหม่ แต่เลือก `evidence_id` จากช่วงข้อความ Alert ที่ระบบกำหนดไว้ จากนั้น Evidence Linker ตรวจอีกครั้งว่าข้อความนั้นอยู่ใน Alert ต้นฉบับจริง

### 4.2 Grounding Judge ทำหน้าที่อะไร?

ตรวจว่า Technique มีหลักฐานรองรับหรือไม่ ชื่อและ Tactic ตรงกับ Candidate หรือไม่ Confidence เพียงพอหรือไม่ และควรส่งให้มนุษย์ตรวจหรือไม่

### 4.3 Semantic Judge ต่างจาก Deterministic Judge อย่างไร?

Deterministic Judge ตรวจโครงสร้างและกฎที่ระบุชัด เช่น ID, URL, Evidence และ Confidence ส่วน Semantic Judge ใช้ LLM ประเมินความหมายของ Evidence ว่าสนับสนุนคำอธิบาย Technique จริงหรือไม่

### 4.4 ถ้า Semantic Judge ล้มเหลวเกิดอะไรขึ้น?

ระบบจะไม่ถือว่าผล LLM ผ่าน Grounding แต่ย้อนกลับไปใช้ผลจาก deterministic rules และตั้ง Human Review

### 4.5 `needs_human_review` เป็นจริงเมื่อใด?

เป็นจริงเมื่อไม่พบคำตอบ Confidence ต่ำ มีข้อความกำกวม Evidence ถูกตัดออก Technique ไม่ตรง Candidate Inferencer fallback หรือ Semantic Judge ตอบ `review` หรือล้มเหลว

### 4.6 No-match หมายความว่า Alert ปลอดภัยหรือไม่?

ไม่ได้หมายความว่าปลอดภัย หมายถึงระบบไม่มีหลักฐานเพียงพอสำหรับ Technique ที่อยู่ใน subset ปัจจุบัน จึงต้องให้มนุษย์ตรวจต่อ

## 5. คำถามด้าน Security

### 5.1 ป้องกัน Prompt Injection อย่างไร?

ใช้หลายชั้น เริ่มจาก regex preflight ก่อนเรียก LLM จากนั้นครอบ Alert เป็น untrusted data และ escape delimiter บังคับ output เป็น JSON จำกัด Technique ด้วย Candidate ตรวจ Evidence กับข้อความต้นฉบับ และใช้ Grounding Judge ตรวจอีกครั้ง

### 5.2 Prompt Injection Detector ตรวจได้ทุกแบบหรือไม่?

ไม่ได้ เป็น regex แบบ conservative ที่ครอบคลุมรูปแบบภาษาอังกฤษที่กำหนดไว้ อาจไม่จับคำสั่งภาษาอื่นหรือข้อความที่ถูก obfuscate ได้ทั้งหมด จึงต้องใช้ Candidate bounding, strict validation และ Evidence grounding เป็นแนวป้องกันชั้นถัดไป

### 5.3 ข้อมูล Alert ถูกส่งออกไปภายนอกหรือไม่?

ค่าเริ่มต้นเป็น Offline จึงไม่ส่งออก หากใช้ Gemini หรือ OpenRouter ต้องเลือกโหมดอย่างชัดเจนและตั้ง `PROVIDER_CONSENT=reviewed-synthetic-only` ระบบยัง redact IP, email และค่าที่ดูเหมือน password, token หรือ secret ก่อนส่ง

### 5.4 Redaction ป้องกันข้อมูลลับได้ทุกชนิดหรือไม่?

ไม่ได้ เป็น defense in depth และตรวจได้เฉพาะรูปแบบที่กำหนด จึงจำกัดการใช้ External Provider ไว้กับข้อมูลสังเคราะห์ที่ผ่านการตรวจแล้วเท่านั้น

## 6. คำถามเกี่ยวกับ API

### 6.1 Endpoint หลักคืออะไร?

Endpoint หลักคือ `POST /alerts/infer` สำหรับวิเคราะห์ Alert หนึ่งรายการ ส่วน `POST /rag/search` ใช้ดู Candidate, `/taxonomy/techniques` ใช้ดูข้อมูลใน subset และ `POST /evaluate` ใช้ประเมินระบบ

### 6.2 ถ้า Request ผิดรูปแบบเกิดอะไรขึ้น?

Pydantic จะปฏิเสธก่อนเข้า Pipeline และตอบ HTTP 422 เช่น narrative ว่าง เป็น object หรือมีฟิลด์ที่ไม่ได้กำหนดไว้ จึงไม่เรียก LLM

### 6.3 ทำไมต้องมี Response Headers จำนวนมาก?

เพื่อให้ตรวจสอบย้อนกลับได้ เช่น Agent ใดสำเร็จหรือ fallback ใช้ Provider และ Model อะไร Confidence มาจาก LLM หรือ Rules และ Prompt Injection Guardrail ผ่านหรือถูกบล็อก

## 7. คำถามเกี่ยวกับ Evaluation

### 7.1 ประเมินระบบด้วยข้อมูลแบบใด?

ใช้ Alert สังเคราะห์ 35 รายการ แบ่งเป็น positive 20, multi-technique 5, ambiguous 5 และ negative control 5 รายการ Gold labels ยังมีสถานะรอการตรวจอิสระ

### 7.2 ใช้ Metrics อะไร?

ใช้ Exact Technique F1, Parent Technique Recall, Evidence Grounding Rate, Hallucinated ID Rate, False-positive Rate, Recall@k, Tactic Accuracy และ Human-review Rate

### 7.3 ผลประเมินปัจจุบันเป็นอย่างไร?

รายงาน Offline Runtime ล่าสุดได้ Exact F1 ประมาณ 97.3%, Parent Recall ประมาณ 97.3%, Evidence Grounding 100%, Hallucinated ID Rate 0% และ False-positive Rate 0% บนข้อมูล 35 รายการ แต่ยังไม่ถือว่า Acceptance Ready เพราะ Gold Labels และ subset ยังรอการตรวจและอนุมัติอิสระ

### 7.4 Hallucinated ID Rate เป็นศูนย์เพราะ LLM เก่งหรือไม่?

ไม่ใช่เพราะ LLM อย่างเดียว แต่เป็นผลจาก Candidate bounding และ Allowlist ทำให้ ID นอก pinned subset ถูกปฏิเสธก่อนแสดงผล

### 7.5 ทำไม Human-review Rate ไม่เป็นศูนย์?

เพราะระบบตั้งใจส่งกรณีกำกวม, no-match, Confidence ต่ำ หรือ Provider fallback ให้มนุษย์ตรวจ Human Review จึงเป็น Guardrail ไม่ใช่ข้อผิดพลาดทั้งหมด

## 8. คำถามเจาะข้อจำกัด

### 8.1 ระบบรองรับภาษาไทยหรือไม่?

API รับข้อความ Unicode ได้ แต่ Tokenizer และ behavior rules ปัจจุบันเน้นภาษาอังกฤษ Alert ภาษาไทยอาจให้ Retrieval ต่ำกว่า แม้ LLM จะเข้าใจข้อความ จึงควรใช้ Alert ภาษาอังกฤษในการสาธิต และถือว่าการรองรับภาษาไทยเต็มรูปแบบเป็นงานต่อยอด

### 8.2 ระบบรองรับ Technique ทั้งหมดของ MITRE หรือไม่?

ไม่รองรับทั้งหมด ขอบเขตคือ Enterprise ATT&CK เฉพาะ Initial Access, Execution และ Credential Access ไม่รองรับ Mobile, ICS หรือ Enterprise Matrix ทั้งหมด

### 8.3 ถ้า Alert เป็น Exfiltration หรือ Impact จะเกิดอะไรขึ้น?

เพราะอยู่นอก Tactic subset ระบบควร abstain หรือคืน no-match และตั้ง Human Review ไม่ควรฝืนจับคู่เป็น Technique ในขอบเขต

### 8.4 ในข้อกำหนดบอกประมาณ 30–50 Techniques แต่ระบบมีเท่าไร?

Snapshot ปัจจุบันมี 127 Candidates และมีสถานะ `provisional_full_in_scope` ซึ่งมากกว่าเป้าหมายประมาณ 30–50 Techniques ในข้อกำหนด เนื่องจาก ingestion ปัจจุบันรวมทุก Technique ที่เกี่ยวข้องกับสาม Tactic ก่อน การอนุมัติ subset ขั้นสุดท้ายยังเป็นงานค้างและเป็นหนึ่งใน Acceptance Blockers

ไม่ควรตอบว่าส่วนนี้ตรงตามข้อกำหนดแล้ว เพราะ implementation ปัจจุบันยังมีความขัดแย้งกับเป้าหมายขนาด subset

### 8.5 จุดอ่อนสำคัญของระบบตอนนี้คืออะไร?

มีสามจุดหลัก ได้แก่ subset ยังเป็น provisional และใหญ่กว่าเป้าหมาย Gold Labels ยังรอ independent review และ Retrieval/behavior rules เน้นภาษาอังกฤษ นอกจากนี้ Confidence จาก LLM ยังไม่ได้ calibrate เป็น probability

### 8.6 หากมีเวลาพัฒนาต่อจะปรับอะไร?

ควรอนุมัติ subset ให้เหลือประมาณ 30–50 Techniques ตามข้อกำหนด ทำ independent label review เพิ่มชุดทดสอบ Prompt Injection ภาษาอื่น ทดลอง dense retrieval เทียบกับ BM25 และ calibrate Confidence กับชุด validation

## 9. การแบ่งคนตอบ

| กลุ่มคำถาม | ผู้รับผิดชอบ |
| --- | --- |
| ภาพรวมระบบ, API และ UI | ผู้ดูแล API/UI |
| MITRE ATT&CK, Knowledge Base, RAG และ Retriever | ผู้ดูแล Knowledge Base/Retrieval |
| Parser, Router, LLM Inferencer, Semantic Judge และ Provider | ผู้ดูแล LLM |
| Evidence, Guardrails, Security, Evaluation และข้อจำกัด | ผู้ดูแล Security/Evaluation |

หากคำถามคาบเกี่ยว ให้ผู้รับผิดชอบส่วนต้นทางตอบก่อน แล้วส่งให้ส่วนปลายทางเสริม เช่น คำถามว่า “ทำไม LLM สร้าง ID เองไม่ได้” ให้ผู้ดูแล LLM อธิบายการตรวจ `tid in candidates` แล้วให้ผู้ดูแล Retriever เสริมว่า Candidate มาจาก pinned STIX Allowlist

## 10. ประโยคสรุปสำหรับปิดการตอบคำถาม

> ความน่าเชื่อถือของระบบไม่ได้มาจาก LLM เพียงอย่างเดียว แต่มาจาก pinned STIX, Allowlist, BM25 Retrieval, candidate-bounded inference, evidence validation, grounding และ human review ที่ทำงานร่วมกัน
