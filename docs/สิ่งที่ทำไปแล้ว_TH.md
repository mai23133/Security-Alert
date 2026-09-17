# สิ่งที่ทำไปแล้ว

อัปเดต 17 กันยายน 2026

เอกสารนี้สรุปงานที่ทำในโปรเจกต์ด้วยภาษาง่าย สำหรับอ่านก่อนดูรายงานเชิงเทคนิคฉบับเต็มใน [PROJECT_COMPLETION_IMPLEMENTATION_TH.md](PROJECT_COMPLETION_IMPLEMENTATION_TH.md)

## ระบบนี้ทำอะไร

ระบบรับข้อความ Security Alert แล้วแนะนำ MITRE ATT&CK Technique ที่อาจเกี่ยวข้อง พร้อมชื่อ Technique, คะแนนความมั่นใจ, ข้อความหลักฐาน และสถานะว่าควรให้คนตรวจหรือไม่

ผลลัพธ์เป็นเพียงคำแนะนำสำหรับนักวิเคราะห์ ไม่ได้สั่งบล็อกเครื่องหรือจัดการเหตุการณ์อัตโนมัติ

## งานที่ทำแล้ว

### 1. ทำให้ฐานข้อมูล ATT&CK เชื่อถือได้มากขึ้น

- ใช้ไฟล์ MITRE ATT&CK Enterprise 19.1 ที่ตรึงไว้
- ตรวจ checksum ของไฟล์ก่อนสร้างฐานข้อมูล
- ตัด Technique ที่ deprecated หรือ revoked ออก
- เก็บข้อมูล Technique, tactic, platform และคำอธิบายไว้ใน snapshot ชุดเดียว
- เมื่อสร้างฐานข้อมูลใหม่ ระบบจะเขียน snapshot แบบ atomic เพื่อลดโอกาสได้ไฟล์ครึ่งเดียว
- ตอน API เริ่มทำงาน จะตรวจว่า snapshot ตรงกับไฟล์ MITRE ที่ตรึงไว้

### 2. ปรับการค้นหาและการอนุมาน

- Retriever ค้นจากคำอธิบาย MITRE แบบเต็มและรองรับคำที่พบใน alert เช่น PowerShell, RDP และ failed login
- ระบบเลือกได้เฉพาะ Technique ที่อยู่ใน candidate list จากฐานข้อมูลเท่านั้น จึงไม่สร้าง ID ขึ้นเอง
- เพิ่มกฎตรวจพฤติกรรมในข้อความ เช่น brute force, PowerShell, credential dumping, phishing และ remote access
- หลักฐานต้องเป็นข้อความที่มีอยู่จริงใน alert และต้องอยู่ในบริบทที่สัมพันธ์กับ Technique
- ตรวจคำปฏิเสธและบริบทที่ไม่ใช่การโจมตี เช่น `authorized`, `patch management`, `training`, `simulation` และ prompt injection
- กรณีไม่พบผล, ข้อมูลไม่ชัด, confidence ต่ำ หรือมี candidate แข่งกัน ระบบจะตั้ง `needs_human_review=true`

### 3. ปรับ API และความปลอดภัย

- API เปิดได้แม้ฐานข้อมูลยังไม่พร้อม โดย endpoint ที่จำเป็นจะตอบ 503 แบบปลอดภัย
- เพิ่ม `/ready` สำหรับตรวจว่าระบบพร้อมใช้งาน
- จำกัดขนาดข้อความ, จำนวน alert ใน batch, จำนวน worker และเวลารวมต่อ request
- รองรับ API key, rate limit และ CORS allowlist สำหรับการตั้งค่าตาม environment
- Error response และ log ไม่สะท้อนข้อความ alert, secret, alert ID หรือ traceback ภายใน
- ค่าเริ่มต้นทำงานแบบ offline และไม่ส่ง alert ไปยัง Gemini/provider
- ผู้ใช้เลือก Gemini/OpenRouter ได้สำหรับ reviewed synthetic alerts; Online path มี LLM Inferencer/Judge, consent/redaction, circuit breaker และ offline fallback พร้อม human review
- หน้า UI มี disclaimer, MITRE attribution, ปุ่มล้างข้อมูล และไม่ใช้ browser storage

### 4. เพิ่มการประเมินและการทดสอบ

- แยก development fixtures ออกจากชุดประเมิน 35 alerts ของรายวิชา
- เพิ่ม development cases 56 กรณี ครอบคลุม positive, multi-technique, ambiguity, benign, negation และ prompt injection
- เพิ่มรายงาน error ว่าพลาดเพราะ retrieval, inference, evidence หรือ ambiguity
- บันทึก version/hash ของ STIX, dataset, code, prompt และ dependencies ใน evaluation report
- เพิ่ม CI สำหรับ test, runtime development gates, browser acceptance และ full runtime quality gate
- ทำ browser E2E และ demo ตาม 5 สถานการณ์ที่ข้อกำหนดระบุ

## ผลล่าสุด

| รายการ | ผล |
| --- | ---: |
| Tests | 207 ผ่าน |
| Exact F1 | 97.30% — ผ่านเกณฑ์ 70% |
| Parent recall | 97.30% — ผ่านเกณฑ์ 90% |
| Hallucinated ID rate | 0% — ผ่าน |
| Evidence grounding ตามการตรวจข้อความ/กฎ | 100% — ผ่านเกณฑ์ 85% |
| False-positive rate ใน negative controls 5 รายการ | 0% |
| Browser acceptance | ผ่าน |
| Demo 5 ขั้น | ผ่านด้านการทำงาน |
| Gemini full-set | Incomplete: rate-limit ที่ eval-005 หลัง 4 alerts ผ่าน strict stages |
| OpenRouter full-set | Incomplete: rate-limit ที่ eval-001 |

## สิ่งที่ยังทำไม่เสร็จ

โครงการยังไม่ควรประกาศว่าเสร็จ 100% เพราะยังมีเรื่องต่อไปนี้:

1. ผู้สอนยังต้องยืนยันรายชื่อ Technique subset ที่อนุญาต 30–50 IDs หรืออนุมัติเป็นกรณีพิเศษให้ใช้ 127 IDs
2. Gold labels ของ alert 35 รายการยังต้องมีผู้ตรวจคนที่สองและผู้สอนยืนยัน
3. ต้องมีการตรวจ semantic grounding และ calibration โดยผู้ตรวจอิสระ ไม่ใช่อาศัยกฎที่ระบบเขียนเอง
4. ต้องยืนยันผล `runtime-quality` บน GitHub Actions หลัง commit/push
5. หากจะ deploy จริง ต้องยืนยัน target environment, privacy, retention และการควบคุมระดับ gateway

## ไฟล์ที่ควรเปิดอ่านต่อ

- [รายงานเชิงเทคนิคเต็ม](PROJECT_COMPLETION_IMPLEMENTATION_TH.md)
- [แผนปิดโครงการ](PROJECT_COMPLETION_PLAN_TH.md)
- [Decision record ที่รอผู้สอนยืนยัน](PROJECT_COMPLETION_DECISIONS_TH.md)
- [คู่มือ privacy และ deployment](DEPLOYMENT_PRIVACY_TH.md)
- [ผลประเมิน runtime ล่าสุด](reports/runtime-final.json)
- [ลำดับการทำงานตามไฟล์โค้ด](SYSTEM_FLOW_CODE_GUIDE_TH.md)
- [ผลเปรียบเทียบโมเดล](MODEL_EVALUATION_RESULTS_TH.md)
- [ผลทดสอบทั้งหมด](reports/tests.xml)

## วิธีตรวจซ้ำแบบสั้น

```bash
.venv/bin/python -m src.rag.ingest_stix
GOOGLE_API_KEY='' GEMINI_API_KEY='' .venv/bin/python -m pytest -q
.venv/bin/python -m eval.run_eval --mode runtime --subset full --require-quality-gates
git diff --check
```

คำสั่ง evaluation ตัวสุดท้ายคืน exit 0 ในผล local ปัจจุบัน เพราะ numeric quality gates ผ่านแล้ว; ยังต้องยืนยันผลเดียวกันใน GitHub Actions และทำ approval/review ที่เหลือ
