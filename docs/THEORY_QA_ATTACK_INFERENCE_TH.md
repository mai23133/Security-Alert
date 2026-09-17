# คำถาม–คำตอบเชิงทฤษฎี: Security Alert → MITRE ATT&CK Inference

อัปเดต 17 กันยายน 2026 เอกสารนี้ใช้เตรียมตอบคำถามหลังการนำเสนอ โดยยึด `security-alert-attack-technique-inference.md` และ implementation ปัจจุบันเป็นหลัก

> คำศัพท์สำคัญ: ระบบนี้เป็นระบบช่วยแนะนำ Technique แก่นักวิเคราะห์ ไม่ใช่ระบบยืนยันเหตุการณ์หรือทำ Incident Response อัตโนมัติ

## 1. แนวคิดพื้นฐาน

### 1. MITRE ATT&CK คืออะไร?

**คำตอบสั้น:** MITRE ATT&CK เป็นฐานความรู้ที่จัดหมวดหมู่พฤติกรรมและวิธีการที่ผู้โจมตีใช้ โดยแบ่งเป็น Tactic, Technique และ Sub-technique ช่วยให้ทีมความปลอดภัยใช้ภาษากลางในการอธิบายเหตุการณ์

**ขยายความ:** Tactic อธิบายเป้าหมายของผู้โจมตี เช่น Execution หรือ Credential Access ส่วน Technique อธิบายวิธีการ เช่น `T1110 Brute Force` และ Sub-technique ให้รายละเอียดเฉพาะขึ้น เช่น `T1059.001 PowerShell`

### 2. Tactic, Technique และ Sub-technique ต่างกันอย่างไร?

**คำตอบสั้น:** Tactic คือ “ทำไปเพื่ออะไร” Technique คือ “ทำอย่างไร” และ Sub-technique คือรูปแบบย่อยที่เฉพาะเจาะจงของ Technique

ตัวอย่าง:

- Tactic: Execution
- Technique: `T1059 Command and Scripting Interpreter`
- Sub-technique: `T1059.001 PowerShell`

### 3. STIX 2.1 คืออะไร?

**คำตอบสั้น:** STIX เป็นมาตรฐานโครงสร้างข้อมูล Threat Intelligence ที่อ่านได้ด้วยเครื่อง โปรเจกต์ใช้ไฟล์ ATT&CK Enterprise ในรูป STIX 2.1 เพื่อดึง ID, ชื่อ, คำอธิบาย, tactic, platform และสถานะ deprecated/revoked มาสร้างฐานความรู้

### 4. ทำไมต้องตรึง ATT&CK ที่เวอร์ชัน 19.1?

**คำตอบสั้น:** เพื่อให้ taxonomy และผลประเมินทำซ้ำได้ หากใช้ข้อมูลออนไลน์ล่าสุดตลอดเวลา Technique หรือ metadata อาจเปลี่ยน ทำให้แต่ละกลุ่มหรือแต่ละรอบได้ผลไม่เหมือนกัน

### 5. ทำไมไม่รองรับ ATT&CK ทั้งหมด?

**คำตอบสั้น:** การจำกัด subset ลดพื้นที่ค้นหา ลด false positive และทำให้ประเมินผลได้ชัดเจน โปรเจกต์นี้กำหนดเฉพาะ Initial Access, Execution และ Credential Access บน Windows/Linux

### 6. Deprecated กับ revoked Technique คืออะไร?

**คำตอบสั้น:** Deprecated คือรายการที่เลิกแนะนำให้ใช้ ส่วน revoked คือรายการที่ MITRE ถอนหรือแทนที่แล้ว ระบบคัดทั้งสองประเภทออกจาก candidates เพื่อไม่เสนอรหัสที่ไม่ควรใช้งาน

### 7. ปัญหาหลักที่ระบบนี้แก้คืออะไร?

**คำตอบสั้น:** ช่วยลดเวลาและความไม่สม่ำเสมอในการอ่าน Security Alert แบบข้อความอิสระแล้วจับคู่กับ ATT&CK โดยให้ Technique ที่เป็นไปได้พร้อมหลักฐานให้นักวิเคราะห์ตรวจสอบ

### 8. ทำไมระบบต้องรองรับหลาย label?

**คำตอบสั้น:** Alert หนึ่งรายการอาจมีหลายพฤติกรรม เช่น authentication failures และ encoded PowerShell จึงอาจตรงกับทั้ง Brute Force และ PowerShell พร้อมกัน

### 9. ทำไมระบบคืนได้ 0–3 Techniques?

**คำตอบสั้น:** แม้ข้อกำหนดเน้นการอนุมาน 1–3 รายการ แต่ระบบต้องคืน 0 ได้เมื่อไม่มีหลักฐานเพียงพอ การจำกัดสูงสุด 3 รายการช่วยลด over-tagging และทำให้ Analyst ตรวจผลได้ง่าย

### 10. Zero-shot inference คืออะไรในบริบทนี้?

**คำตอบสั้น:** คือการจับคู่ Alert กับ Technique โดยไม่ฝึกโมเดลจำแนกใหม่จากตัวอย่างของทุก Technique แต่ใช้คำอธิบาย ATT&CK, retrieval, rules หรือ LLM reasoning เพื่ออนุมานจากข้อความที่ได้รับ

## 2. RAG และ Retrieval

### 11. RAG คืออะไร?

**คำตอบสั้น:** RAG ย่อจาก Retrieval-Augmented Generation หรือในกรณีนี้คือ retrieval-augmented inference ระบบค้นข้อมูล Technique ที่เกี่ยวข้องจากฐานความรู้ก่อน แล้วจึงให้ Inferencer เลือกจาก candidates เหล่านั้น

### 12. ทำไมโปรเจกต์นี้ยังเรียกว่า RAG แม้ Offline mode ใช้ rules?

**คำตอบสั้น:** เพราะ retrieval จาก ATT&CK knowledge base ยังเกิดก่อน inference เสมอ ส่วน rules เป็น inference backend ที่เลือกจาก retrieved candidates ไม่จำเป็นว่า RAG ทุกระบบต้องใช้ LLM สร้างคำตอบ

### 13. Retrieval ต่างจาก Inference อย่างไร?

**คำตอบสั้น:** Retrieval ตอบว่า “Technique ใดควรถูกนำมาพิจารณา” ส่วน Inference ตอบว่า “Technique ใดมีหลักฐานเพียงพอที่จะเสนอเป็นผลลัพธ์” Candidate จึงไม่เท่ากับ prediction

### 14. BM25 คืออะไร?

**คำตอบสั้น:** BM25 เป็นวิธีจัดอันดับเอกสารจากความสัมพันธ์ของคำใน query กับเอกสาร โดยพิจารณาความถี่ของคำ ความหายากของคำ และปรับผลตามความยาวเอกสาร

### 15. ทำไมเลือก BM25?

**คำตอบสั้น:** BM25 ทำงานแบบ deterministic, รันในเครื่อง, อธิบายง่าย และเหมาะกับคำเฉพาะทาง เช่น Technique ID, PowerShell, RDP หรือ credential dumping โดยไม่ต้องดาวน์โหลด embedding model ภายนอก

### 16. ข้อจำกัดของ BM25 คืออะไร?

**คำตอบสั้น:** BM25 เน้น lexical similarity จึงอาจพลาดข้อความที่ความหมายเหมือนกันแต่ใช้คนละคำ และอาจคืน candidate จากคำที่คล้ายกันแม้บริบทไม่ใช่การโจมตี จึงต้องมี Inferencer และ Grounding Judge ต่อท้าย

### 17. `top_k` คืออะไร?

**คำตอบสั้น:** คือจำนวน candidates สูงสุดที่ Retriever คืนมา ใน pipeline ปัจจุบันค่าเริ่มต้นคือ 5 เพื่อให้มีตัวเลือกพอสำหรับ inference โดยไม่เปิดพื้นที่ค้นหากว้างเกินไป

### 18. ถ้า `top_k` ต่ำเกินไปจะเกิดอะไรขึ้น?

**คำตอบสั้น:** Technique ที่ถูกต้องอาจไม่ติด candidates ทำให้ Inferencer ไม่มีสิทธิ์เลือก เกิด false negative และ Recall@k ลดลง

### 19. ถ้า `top_k` สูงเกินไปจะเกิดอะไรขึ้น?

**คำตอบสั้น:** Inferencer ต้องพิจารณารายการที่ไม่เกี่ยวข้องมากขึ้น เพิ่มความกำกวม ค่าใช้จ่ายของ LLM และโอกาสเกิด false positive

### 20. Tactic Router ช่วย Retrieval อย่างไร?

**คำตอบสั้น:** Router จำกัดการค้นหาให้เหลือ tactics ที่น่าจะเกี่ยวข้อง เช่น Execution หรือ Credential Access ทำให้ candidate space เล็กลงและลด Technique ที่ไม่เกี่ยวข้อง

### 21. Allowlist มีหน้าที่อะไร?

**คำตอบสั้น:** Allowlist กำหนด Technique ID ที่ระบบอนุญาตจาก pinned subset แม้ข้อความหรือโมเดลเสนอรหัสรูปแบบถูกต้อง แต่ถ้าไม่อยู่ใน allowlist ก็ใช้เป็นผลลัพธ์ไม่ได้

### 22. ทำไม benign alert ยังอาจมี candidates?

**คำตอบสั้น:** Retrieval หาเอกสารที่มีคำใกล้เคียง ไม่ได้ตัดสินเจตนาหรือความเป็นอันตราย Candidates จึงมีได้ แต่ Inferencer และ Judge ต้องไม่ยกระดับเป็น prediction หากไม่มีหลักฐานเชิงพฤติกรรม

## 3. Agent Architecture และ Pipeline

### 23. ทำไมต้องแบ่งเป็นหลาย Agent?

**คำตอบสั้น:** การแบ่งหน้าที่ทำให้แต่ละขั้นตรวจสอบ ทดสอบ และเปลี่ยนแปลงได้อิสระ เช่น Parser มีหน้าที่จัดโครงสร้างข้อมูล ส่วน Judge มีหน้าที่ตรวจผล ไม่ควรให้ขั้นเดียวทำทุกอย่างโดยไม่มีจุดตรวจ

### 24. Alert Parser ทำอะไร?

**คำตอบสั้น:** ทำข้อความ Alert ให้อยู่ในโครงสร้าง `ParsedAlert` และแยก narrative, assets, observed actions และ IOCs เพื่อให้ขั้นต่อไปใช้ข้อมูลได้สม่ำเสมอ

### 25. Tactic Router ทำอะไร?

**คำตอบสั้น:** ประเมินว่า Alert น่าจะเกี่ยวข้องกับ tactics ใด แล้วส่งขอบเขตนั้นให้ Retriever ใช้กรองฐานความรู้

### 26. Technique Inferencer ทำอะไร?

**คำตอบสั้น:** เลือก Technique 0–3 รายการจาก retrieved candidates โดย Offline mode ใช้ behavior rules ส่วน Online mode สามารถใช้ LLM ที่เลือก

### 27. Evidence Linker ทำอะไร?

**คำตอบสั้น:** เชื่อมแต่ละ Technique กับช่วงข้อความจริงใน Alert เพื่อให้ผลลัพธ์ตรวจย้อนกลับได้ และไม่ยอมรับ evidence ที่ไม่มีอยู่ใน input

### 28. Grounding Judge ทำอะไร?

**คำตอบสั้น:** ตรวจว่าผลมี candidate รองรับ, ID/ชื่อ/tactic/URL ตรงกัน, evidence อยู่ใน Alert, คะแนนถึงเกณฑ์ และไม่มีเงื่อนไขกำกวม หากไม่ผ่านจะปฏิเสธผลหรือกำหนดให้มนุษย์ตรวจ

### 29. Grounding ต่างจากความถูกต้องทางความหมายอย่างไร?

**คำตอบสั้น:** Grounding ยืนยันว่าคำตอบมีหลักฐานอ้างกลับไปยัง input ได้ แต่ไม่ได้รับประกันว่าการตีความหลักฐานนั้นถูกต้องทั้งหมด จึงยังต้องมี Analyst ตรวจ semantic correctness

### 30. ทำไม Parser กับ Judge ไม่ควรเป็นขั้นเดียวกัน?

**คำตอบสั้น:** เพราะจะขาด separation of duties หากโมเดลเดียวสร้างและรับรองคำตอบของตัวเอง ความผิดพลาดหรือ bias เดิมอาจไม่ถูกตรวจพบ การแยก Judge ทำให้กำหนด validation ที่เป็นอิสระได้

### 31. Pydantic ช่วยอะไร?

**คำตอบสั้น:** Pydantic บังคับชนิดข้อมูลและข้อจำกัดของ request/response เช่นรูปแบบ Technique ID, ช่วงคะแนน 0–1, ขนาด narrative และฟิลด์ที่อนุญาต ลด malformed input/output

### 32. Schema validation ป้องกัน hallucination ได้ทั้งหมดหรือไม่?

**คำตอบสั้น:** ไม่ได้ Schema ตรวจเพียงรูปแบบ เช่น `T9999` ยังมีรูปแบบ `T####` ที่ถูกต้อง จึงต้องตรวจ allowlist, candidates, metadata และ evidence เพิ่มด้วย

### 33. ทำไมต้องตรวจชื่อ, tactic และ URL นอกจาก ID?

**คำตอบสั้น:** เพื่อป้องกันผลที่จับคู่ metadata ผิด เช่น ID ถูกแต่ตั้งชื่อหรือ tactic คนละรายการ และป้องกัน URL ที่ถูกสร้างผิดหรือชี้ไปยังตำแหน่งที่ไม่สัมพันธ์กับ ID

### 34. Deterministic pipeline มีข้อดีอย่างไร?

**คำตอบสั้น:** ให้ผลทำซ้ำได้ ทดสอบ regression ได้ ไม่ขึ้นกับ network/quota และเหมาะเป็น baseline ที่ตรวจสอบได้ ข้อจำกัดคือ rules อาจไม่ครอบคลุมภาษาหรือพฤติกรรมใหม่

## 4. Offline, LLM และ Fallback

### 35. Offline mode ทำงานอย่างไร?

**คำตอบสั้น:** ใช้ local Parser/Router fallback, BM25 retrieval, behavior-rule inferencer, evidence linking และ deterministic grounding โดยไม่ส่ง Alert ไปยัง external provider

### 36. Online mode ใช้ LLM ในขั้นใดบ้าง?

**คำตอบสั้น:** Gemini/OpenRouter path ใช้ provider ที่เลือกกับ Parser, Router, LLM Inferencer และ LLM Grounding Judge แต่ผลยังต้องผ่าน structural guardrails เดียวกับ Offline mode

### 37. ทำไมต้องมี Offline mode ถ้ามี LLM?

**คำตอบสั้น:** เพื่อให้ระบบใช้งานและประเมินซ้ำได้แม้ไม่มี key, network หรือ quota รวมทั้งช่วยลดความเสี่ยงด้าน privacy และเป็น baseline สำหรับเปรียบเทียบ LLM

### 38. Fallback คืออะไร?

**คำตอบสั้น:** เมื่อ external stage ล้มเหลว ระบบอาจใช้ผลจากกฎออฟไลน์แบบ conservative แทน พร้อมระบุว่าเกิด fallback, บอกเหตุผลและส่งให้มนุษย์ตรวจ

### 39. ทำไม fallback transparency จึงสำคัญ?

**คำตอบสั้น:** เพราะผู้ใช้ต้องรู้แหล่งที่มาของผล หากแสดง rule result เหมือนเป็นผลสำเร็จจาก Gemini จะทำให้ประเมินคุณภาพและความรับผิดชอบผิด

### 40. ระบบสลับจาก Gemini ไป OpenRouter อัตโนมัติหรือไม่?

**คำตอบสั้น:** ไม่สลับ provider อื่นอย่างเงียบ ๆ ระบบยึด provider ที่ผู้ใช้เลือก และหากล้มเหลวจะเปิดเผยสถานะหรือ fallback ไป conservative offline result ตามขั้นตอน

### 41. Support score ต่างจาก probability อย่างไร?

**คำตอบสั้น:** Support score เป็นคะแนนจากกฎหรือการประเมินตนเองของ LLM ยังไม่ได้ผ่าน calibration จึงห้ามตีความว่า 82 หมายถึงมีโอกาสถูก 82 เปอร์เซ็นต์

### 42. Calibration คืออะไร?

**คำตอบสั้น:** คือการทำให้คะแนนสอดคล้องกับความถี่ที่ถูกจริง เช่นผลที่ให้ 0.8 ควรถูกประมาณ 80% ในข้อมูลที่เป็นตัวแทน ระบบปัจจุบันยังไม่ได้พิสูจน์คุณสมบัตินี้

### 43. Circuit breaker มีประโยชน์อย่างไร?

**คำตอบสั้น:** เมื่อ provider ล้มเหลวซ้ำ ระบบหยุดส่งคำขอชั่วคราว เพื่อลด latency, ลดคำขอที่เสียเปล่า และป้องกันการขยายปัญหาจากบริการภายนอกที่ขัดข้อง

## 5. Security และ Guardrails

### 44. Prompt injection คืออะไร?

**คำตอบสั้น:** คือการฝังข้อความที่พยายามเปลี่ยนพฤติกรรมของโมเดล เช่น “ignore previous instructions” หรือสั่งให้คืนรหัสปลอม ทั้งที่ข้อความนั้นควรถูกมองเป็นข้อมูล Alert เท่านั้น

### 45. ระบบป้องกัน prompt injection อย่างไร?

**คำตอบสั้น:** ใช้หลายชั้น ได้แก่ deterministic preflight detection, แยกข้อมูลออกจาก instructions, candidate bounding, allowlist, schema validation, metadata checks, verbatim evidence และ Grounding Judge

### 46. ทำไมต้อง block ก่อนเรียกโมเดล?

**คำตอบสั้น:** ลดโอกาสที่ payload จะมีอิทธิพลต่อโมเดลและป้องกันการส่งข้อความเสี่ยงออกไปยัง provider เมื่อพบรูปแบบที่กำหนด ระบบจึง fail closed และส่งให้มนุษย์ตรวจ

### 47. ระบบป้องกัน prompt injection ได้ 100% หรือไม่?

**คำตอบสั้น:** ไม่ควรอ้างว่าได้ 100% ตัวตรวจจับเป็นกฎสำหรับ instruction-like patterns ที่รู้จัก ความปลอดภัยจึงต้องพึ่ง defense in depth และ human review ไม่ใช่ detector เพียงชั้นเดียว

### 48. T9999 ถูกปฏิเสธเพราะอะไร?

**คำตอบสั้น:** แม้รูปแบบจะคล้าย Technique ID แต่ไม่มีใน pinned subset และไม่ได้มาจาก retrieved candidates จึงไม่ผ่าน allowlist และ candidate validation นอกจากนี้ sample injection ถูก block ก่อน inference อยู่แล้ว

### 49. Fail closed คืออะไร?

**คำตอบสั้น:** เมื่อระบบไม่แน่ใจหรือพบความเสี่ยง ระบบเลือกหยุดหรือไม่คืน prediction แทนการเดินหน้าด้วยสมมติฐานที่อาจไม่ปลอดภัย แล้วส่งสถานะให้มนุษย์ตรวจ

### 50. Human-in-the-loop คืออะไร?

**คำตอบสั้น:** ระบบช่วยกรองและเสนอข้อมูล แต่การตัดสินใจสุดท้ายยังเป็นของมนุษย์ โดยเฉพาะ no-match, low support, ambiguous evidence, injection และ provider fallback

### 51. ทำไม no-match ต้องขึ้น human review?

**คำตอบสั้น:** เพราะ no-match แปลเพียงว่าไม่มีหลักฐานพอภายใต้ subset และกฎปัจจุบัน ไม่ได้พิสูจน์ว่าไม่เกิดการโจมตี อาจเป็นพฤติกรรมนอกขอบเขตหรือ telemetry ไม่ครบก็ได้

### 52. ระบบดูแล Privacy อย่างไร?

**คำตอบสั้น:** Offline mode ไม่ส่ง Alert ไป provider ภายนอก ส่วน Online mode ต้องมี explicit consent, ใช้เฉพาะ reviewed synthetic data และทำ redaction ขั้นต้นก่อนส่ง

### 53. Redaction ป้องกันข้อมูลส่วนบุคคลได้ทั้งหมดหรือไม่?

**คำตอบสั้น:** ไม่ได้ ปัจจุบันเป็นการลดความเสี่ยงเบื้องต้นสำหรับรูปแบบอย่าง IP, email และ secret บางชนิด ไม่ใช่ระบบตรวจ PII ที่ครอบคลุมทุกประเภท

### 54. ทำไม API key ต้องอยู่ฝั่ง server?

**คำตอบสั้น:** หากส่ง key ไป browser ผู้ใช้หรือ attacker สามารถอ่านและนำไปใช้ได้ การเก็บ server-side ช่วยจำกัดการเปิดเผยและบังคับ policy เช่น consent, timeout และ rate limiting ได้

### 55. Disclaimer มีความสำคัญอย่างไร?

**คำตอบสั้น:** ทำให้ผู้ใช้ทราบข้อจำกัดของระบบอย่างต่อเนื่องว่าเป็น advisory tagging ไม่ใช่ autonomous SOC action และต้องตรวจสอบโดยผู้เชี่ยวชาญ

## 6. Evaluation และ Metrics

### 56. Gold label คืออะไร?

**คำตอบสั้น:** คือ Technique ID ที่ถือเป็นคำตอบอ้างอิงของแต่ละ Alert ใช้เปรียบเทียบกับ prediction เพื่อคำนวณ metrics โดยชุดนี้เป็น synthetic course dataset ที่ต้องได้รับการตรวจ label

### 57. Precision คืออะไร?

**คำตอบสั้น:** สัดส่วน Technique ที่ระบบทำนายแล้วถูกต้อง ค่าสูงหมายถึงระบบสร้าง false positive น้อย

```text
Precision = True Positives / (True Positives + False Positives)
```

### 58. Recall คืออะไร?

**คำตอบสั้น:** สัดส่วน Technique ที่ควรพบและระบบค้นพบ ค่าสูงหมายถึงระบบพลาด Technique จริงน้อย

```text
Recall = True Positives / (True Positives + False Negatives)
```

### 59. F1 score คืออะไร?

**คำตอบสั้น:** ค่าเฉลี่ยฮาร์มอนิกของ precision และ recall ใช้สรุปสมดุลระหว่างการทำนายเกินกับการทำนายขาด

```text
F1 = 2 × Precision × Recall / (Precision + Recall)
```

### 60. Exact Technique F1 วัดอะไร?

**คำตอบสั้น:** วัดการตรงกันของ Technique IDs แบบ exact ในโจทย์ multi-label เช่นทำนาย parent `T1059` จะยังไม่ถือว่าตรงกับ gold `T1059.001`

### 61. Parent Technique Recall มีไว้ทำไม?

**คำตอบสั้น:** ใช้วัดว่าระบบอย่างน้อยจับครอบครัว Technique ได้หรือไม่ แม้พลาดระดับ Sub-technique ช่วยแยกความผิดพลาดที่ใกล้เคียงออกจากการพลาดทั้งหมด

### 62. Evidence Grounding Rate คืออะไร?

**คำตอบสั้น:** สัดส่วน prediction ที่มี evidence ย้อนกลับไปยัง Alert ได้ ในระบบนี้เป็น structural/verbatim grounding ไม่ใช่การรับรองความถูกต้องเชิงความหมายทั้งหมด

### 63. Hallucinated ID Rate คืออะไร?

**คำตอบสั้น:** สัดส่วน Technique IDs ที่ระบบทำนายแต่ไม่มีใน pinned allowlist เป้าหมายต้องเป็นศูนย์ เพราะการสร้างรหัสที่ไม่มีจริงเป็นความผิดพลาดร้ายแรง

### 64. False-positive rate ของ benign controls คืออะไร?

**คำตอบสั้น:** สัดส่วน benign alerts ที่ระบบติด Technique ให้อย่างผิดพลาด ใช้วัดว่าระบบ over-tag กิจกรรมปกติมากน้อยเพียงใด

### 65. Human-review rate สูงแปลว่าระบบไม่ดีหรือไม่?

**คำตอบสั้น:** ไม่เสมอไป ในระบบความปลอดภัย การส่งเคสกำกวมให้มนุษย์ตรวจเป็นพฤติกรรมที่ปลอดภัย แต่ถ้าสูงเกินไปจะเพิ่มภาระ Analyst จึงต้องดูคู่กับ precision, recall และความเสี่ยงของงาน

### 66. Recall@k ของ Retriever คืออะไร?

**คำตอบสั้น:** วัดว่าสำหรับ Alert หนึ่ง ๆ Technique ที่เป็น gold ปรากฏใน top-k candidates หรือไม่ หากไม่ติด candidates Inferencer ก็ไม่มีโอกาสเลือกถูก

### 67. ทำไมต้องมี negative controls?

**คำตอบสั้น:** หากประเมินเฉพาะเหตุการณ์โจมตี ระบบที่ทำนาย Technique ให้ทุก Alert อาจดูเหมือน recall สูง Negative controls ช่วยวัดความสามารถในการ abstain และ false positives

### 68. ทำไมไม่ควรอ้างคะแนน Offline เป็นคะแนน Gemini?

**คำตอบสั้น:** ทั้งสองใช้ inference backend ต่างกัน หาก Gemini evaluation ไม่ครบเพราะ quota จะนำคะแนนจาก rules มาแทนไม่ได้ ต้องรายงานสถานะแยกกันเพื่อรักษาความถูกต้องของการทดลอง

### 69. คะแนนบน synthetic dataset ใช้อ้างกับระบบจริงได้หรือไม่?

**คำตอบสั้น:** ใช้เป็นหลักฐานว่า pipeline ทำงานตามชุดทดสอบได้ แต่ยังไม่รับรองประสิทธิภาพบน production data เพราะรูปแบบภาษา distribution และ label quality อาจต่างกัน ต้องมี external validation เพิ่ม

### 70. Data leakage คืออะไร?

**คำตอบสั้น:** คือข้อมูลจากชุดประเมินมีอิทธิพลต่อการสร้างหรือปรับระบบมากเกินไป ทำให้คะแนนสูงแต่ generalize ไม่ได้ ชุดข้อมูลที่เคยใช้วิเคราะห์ข้อผิดพลาดจึงไม่ควรถูกเรียกว่า blind holdout

## 7. API และ Operational Design

### 71. API หลักรับและคืนอะไร?

**คำตอบสั้น:** `POST /alerts/infer` รับ narrative, optional alert ID และ inference mode แล้วคืน `ATTACKInferenceResult` ซึ่งมี predictions, candidates, review flag และ disclaimer

### 72. ทำไมต้องจำกัดความยาว Alert?

**คำตอบสั้น:** เพื่อควบคุมหน่วยความจำ เวลา ค่าใช้จ่ายของ provider และลดความเสี่ยง denial-of-service จาก input ขนาดใหญ่ ปัจจุบันจำกัด 20,000 ตัวอักษร

### 73. ทำไมต้องมี timeout?

**คำตอบสั้น:** ป้องกัน request ค้างไม่สิ้นสุดเมื่อ retrieval หรือ provider ช้า และช่วยควบคุมทรัพยากรของ server เมื่อ timeout ระบบต้องคืนข้อผิดพลาดที่ปลอดภัยและให้มนุษย์ตรวจ

### 74. ทำไมต้องมี request ID หรือ alert ID?

**คำตอบสั้น:** เพื่อ trace การทำงานและเชื่อมผลกับ request โดยไม่ต้องบันทึก narrative ทั้งหมด ช่วย debugging และ audit โดยลดการเปิดเผยข้อมูล

### 75. Batch endpoint มีประโยชน์อย่างไร?

**คำตอบสั้น:** รองรับการวิเคราะห์หลาย Alerts ใน request เดียวและรักษาลำดับผล หากรายการหนึ่งล้มเหลว ระบบสามารถคืน safe no-match สำหรับรายการนั้นโดยไม่ทิ้งผลทั้งหมด

### 76. ทำไม response status ของ provider อยู่ใน headers?

**คำตอบสั้น:** เพื่อคง business response schema ตามข้อกำหนด ขณะยังเปิดเผย operational metadata เช่น stage status, provider, model, fallback reason และ confidence source ให้ UI แสดงได้

## 8. คำถามเชิงวิพากษ์และข้อจำกัด

### 77. จุดอ่อนสำคัญของระบบปัจจุบันคืออะไร?

**คำตอบสั้น:** Subset ยังจำกัด, dataset เป็นข้อมูลจำลอง, rules อาจไม่ครอบคลุมภาษาจริง, support score ยังไม่ calibrated, prompt-injection detector ไม่สมบูรณ์ และ full-set LLM evaluation ยังขึ้นกับ quota/provider

### 78. ทำไม Alert เดียวอาจได้ Technique เกิน gold label?

**คำตอบสั้น:** Alert อาจมีข้อความเพิ่มที่สื่อพฤติกรรมอีกชนิด หรือ rules อาจ over-tag เช่นมีทั้ง PowerShell และ cmd.exe Gold label เองก็อาจไม่ครบ จึงต้องวิเคราะห์ทั้ง prediction, evidence และ label quality

### 79. ถ้า Retriever ไม่คืน Technique ที่ถูกต้อง จะแก้อย่างไร?

**คำตอบสั้น:** ตรวจ Recall@k และ error cases แล้วปรับ tokenization, metadata, tactic routing, query weighting หรือใช้ hybrid lexical-semantic retrieval โดยยังคง pinned allowlist และ deterministic evaluation

### 80. ถ้า Grounding Rate 100% แปลว่าคำตอบถูกทั้งหมดหรือไม่?

**คำตอบสั้น:** ไม่ใช่ แปลเพียงว่าทุก prediction มีข้อความอ้างอิงอยู่จริง แต่ข้อความนั้นอาจถูกตีความผิด Technique ได้ จึงต้องดู Exact F1 และ semantic review ร่วมด้วย

### 81. ระบบนี้แทน SOC Analyst ได้หรือไม่?

**คำตอบสั้น:** ไม่ได้ ระบบช่วยลดพื้นที่ค้นหาและจัด evidence ให้ตรวจง่ายขึ้น แต่ไม่เห็นบริบททั้งหมดขององค์กร ไม่ได้ทำ incident response และกรณีกำกวมยังต้องอาศัยผู้เชี่ยวชาญ

### 82. ทำไมไม่ให้ LLM ตอบ Technique จากความรู้ภายในโดยตรง?

**คำตอบสั้น:** เพราะความรู้ภายในโมเดลอาจล้าสมัยหรือสร้าง ID ผิด การบังคับให้เลือกจาก pinned candidates ทำให้ taxonomy ทำซ้ำได้และลด hallucination

### 83. ถ้าจะนำไปใช้จริงต้องเพิ่มอะไร?

**คำตอบสั้น:** ต้องมี dataset จากสภาพแวดล้อมจริงที่ผ่าน governance, independent label review, authentication, rate limiting, monitoring, retention policy, calibration, drift detection, external validation และ incident-response integration ที่ผ่านการอนุมัติ

### 84. ทำไมระบบไม่ทำ automated response?

**คำตอบสั้น:** การทำนาย Technique อาจผิดและข้อมูลอาจไม่ครบ การบล็อกบัญชีหรือเครื่องโดยอัตโนมัติสร้างผลกระทบสูงและอยู่นอกขอบเขต ระบบจึงจำกัดตัวเองเป็น decision support

### 85. ถ้ามี Technique ใหม่ใน ATT&CK จะทำอย่างไร?

**คำตอบสั้น:** ต้องอัปเดต pinned STIX อย่างมี version, สร้าง subset/index/allowlist ใหม่ ตรวจ deprecated/revoked, rerun tests และ evaluation แล้วจึงประกาศเวอร์ชันใหม่ ไม่อัปเดตเงียบ ๆ ระหว่างการประเมิน

## 9. คำถามเร็วสำหรับซ้อมตอบ

| คำถาม | คำตอบหนึ่งประโยค |
| --- | --- |
| ระบบนี้คือ classifier หรือ search engine? | เป็น pipeline ที่ใช้ retrieval จำกัด candidates แล้วทำ multi-label inference พร้อม grounding |
| Candidate คือคำตอบหรือไม่? | ไม่ใช่ Candidate เป็นเพียงรายการที่ Inferencer นำมาพิจารณา |
| No-match แปลว่าปลอดภัยหรือไม่? | ไม่แปลว่าปลอดภัย แปลเพียงว่าหลักฐานไม่พอภายใต้ขอบเขตระบบ |
| คะแนน 0.82 แปลว่าถูก 82% หรือไม่? | ไม่ใช่ เป็น support score ที่ยังไม่ calibrated |
| ทำไมต้อง pinned STIX? | เพื่อความทำซ้ำได้และป้องกัน taxonomy เปลี่ยนระหว่างการทดลอง |
| ทำไม T9999 ไม่ผ่าน? | ไม่อยู่ใน pinned allowlist/candidates และ injection sample ถูก block ก่อน inference |
| Offline ยังเป็น RAG หรือไม่? | เป็น เพราะมี retrieval จาก knowledge base ก่อนใช้ rules ทำ inference |
| Grounding รับรองว่าถูกหรือไม่? | รับรองการอ้างกลับไปยังข้อความ ไม่ได้รับรอง semantic correctness ทั้งหมด |
| Provider ล่มแล้วทำอย่างไร? | เปิดเผย failure/fallback ใช้ conservative result หากเหมาะสม และส่ง human review |
| ระบบส่ง Alert จริงไป Gemini ได้หรือไม่? | Policy ปัจจุบันอนุญาตเฉพาะ reviewed synthetic alerts พร้อม explicit consent และ redaction ขั้นต้น |
| ทำไมต้องมีมนุษย์ตรวจ? | เพราะ telemetry, taxonomy, rules และโมเดลมีข้อจำกัดและผลกระทบด้าน security สูง |
| ระบบตอบสนองเหตุการณ์อัตโนมัติหรือไม่? | ไม่ ระบบให้คำแนะนำ Technique เท่านั้น |

## 10. แนวทางตอบคำถามต่อหน้ากรรมการ

1. เริ่มด้วยคำตอบตรง ๆ หนึ่งประโยคก่อน แล้วค่อยขยายเหตุผล
2. แยกให้ชัดว่าอะไรคือข้อกำหนด อะไรคือ implementation ปัจจุบัน และอะไรคือสิ่งที่เสนอในอนาคต
3. ใช้คำว่า “support score” แทน “ความน่าจะเป็น”
4. ไม่กล่าวว่า no-match คือ benign หรือ Grounding คือการรับรองความถูกต้องทั้งหมด
5. ไม่กล่าวว่าป้องกัน prompt injection ได้ 100%
6. หากถูกถามเรื่องคะแนน ให้ระบุ dataset, mode และข้อจำกัดของการประเมินทุกครั้ง
7. หากไม่แน่ใจ ให้ชี้กลับไปที่ evidence, pinned version และ human-review policy แทนการคาดเดา

## ไฟล์อ้างอิงในโปรเจกต์

- `security-alert-attack-technique-inference.md` — ข้อกำหนดหลัก
- `docs/PRESENTATION_SCRIPT_PERSON_3_ANALYST_WORKSPACE_TH.md` — บทพูดและ live demo
- `docs/SYSTEM_FLOW_CODE_GUIDE_TH.md` — เส้นทางการทำงานของโค้ด
- `docs/MODEL_EVALUATION_RESULTS_TH.md` — ผลและข้อจำกัดของการประเมิน
- `docs/API_OVERVIEW_TH.md` — API modes, security และ fallback
- `src/inference_pipeline.py` — orchestration
- `src/rag/retriever.py` — retrieval
- `src/agents/grounding_judge.py` — grounding/review rules
- `src/agents/provider_safety.py` — external-provider consent และ redaction

