# รายงานตรวจโครงการปัจจุบัน

ตรวจวันที่ 7 กันยายน 2026 บน feature-c-integration (mai-work e2ee2da + yean-work 5d56d31) อ้างอิง [ข้อกำหนดหลัก](../security-alert-attack-technique-inference.md) หัวข้อ 3–10 และ milestones

## ผลรวม

A+B+D เชื่อมเป็น local baseline แล้ว มี single/batch inference, RAG search, taxonomy และ UI จริง C มี RC dataset, fixture/runtime metrics runner และ /evaluate แล้ว ยังไม่พร้อมประกาศผ่าน MVP quality gates หรือ production

ตรวจ tracked source, tests, UI, workflow, dependency declaration, prompts และเอกสารใน repository; ตรวจ raw STIX ด้วย ingestion และตรวจสำเนา clean checkout โดยใช้ Python environment เดิม ไม่ได้ทดสอบ live Gemini, browser automation, load test, cloud deployment หรือยืนยัน GitHub Actions run ล่าสุด; ตรวจ C 5d56d31 จาก remote และรวมแล้ว ไม่เปิดอ่านค่า secret ใน .env

## Findings เรียงตามผลกระทบ

| ระดับ | หลักฐาน | ผลกระทบและแนวทางเสนอ |
| --- | --- | --- |
| สูง | Runtime evaluation ของ C เชื่อมแล้ว | Exact F1 34.55% และ parent recall 52.70% ยังไม่ผ่านเป้าหมาย; ใช้ report ปรับ A/B ต่อ |
| สูง | inferencer จับคำร่วมอย่างน้อย 2 คำ; linker ตรวจ substring; judge คืน bool | ไม่เข้าใจ negation/benign context/semantic ambiguity; เพิ่มการตรวจเชิงความหมายและ negative tests ก่อนรับมอบ |
| สูง | alerts.py สร้าง RETRIEVER ระดับ module | clean startup ที่ไม่มี processed files ล้มก่อน route จัดการ 503; ingestion ใน CI แก้ขั้นเตรียมข้อมูลแล้ว แต่ lifecycle error handling ยังต้องพัฒนา |
| สูงก่อนใช้ข้อมูลจริง | main.py โหลด .env; parser/router ส่ง narrative ให้ provider เมื่อมี key | ยังไม่มี consent/redaction/retention enforcement; กำหนด sandbox และนโยบายก่อนเปิด provider กับ raw alerts |
| กลาง | SDK timeout 10,000 ms/3 attempts; parser/router จับ Exception แล้ว fallback | HTTP 504 ใช้ได้เมื่อ TimeoutError หลุดถึง route ไม่ใช่ทุก provider timeout; ไม่มี deadline รวมและ async route เรียก synchronous pipeline ซึ่งบล็อก event loop |
| กลาง | inference score เริ่ม 0.45 + 0.10 ต่อ matched term และชื่อ; cap 0.90 | ผ่าน 2 คำได้อย่างน้อย 0.65 เท่ากับ review threshold จึงไม่มี low-confidence flag จาก prediction ปกติ; ยังไม่มี calibration/ambiguity detector |
| กลาง | ingest_stix ได้ 127 candidates | ขัดกับเป้าหมาย 30–50; เลือกลด subset หรือให้ทีม/ผู้สอนอนุมัติแก้ข้อกำหนด ห้ามลดตามอำเภอใจ |
| กลาง | candidate มี tactic เดียว เลือกตาม sorted tactics; description 300 ตัวอักษร | สูญเสีย multi-tactic context และไม่มี platform/source metadata ตาม milestone; เสนอ sidecar metadata หรือ contract revision ที่ทีมเห็นชอบ |
| กลาง | schema ตรวจ ID format/confidence แต่ไม่บังคับ allowlist/evidence/candidate membership | ต้องใช้ pipeline guardrails; judge เพียงตั้ง review ไม่ได้ลบทุก prediction ที่ผิดเอง |
| กลาง | logger.exception ใน alerts.py; middleware log path และ alert error log มี client alert_id | client error body ถูกทำให้ทั่วไป แต่ยังรับประกันไม่ได้ว่า logs ไม่มี sensitive data; เพิ่ม redaction และ policy |
| กลาง | requirements ใช้ทั้ง == และ >=; prompts/v1 ทุกไฟล์ว่าง | dependency/prompt/model reproducibility ยังไม่ครบ; ทำ lock และ prompt metadata เมื่อมี evaluation |
| กลาง | tests/test_retriever.py skip ถ้า processed files หาย | test collection ของ API ล้มก่อน skip ใน fresh checkout; CI ต้อง ingestion และควรเพิ่ม independent fixtures/network sentinel |
| ต่ำ | taxonomy อ่าน JSON ทุก request แต่ retriever cache ตอน import | หาก regenerate ขณะ server ทำงาน taxonomy กับ inference อาจไม่ตรงกัน; restart หลัง rebuild |
| ต่ำ | taxonomy รับ tactic ที่ไม่รู้จักแล้วคืน empty list | พฤติกรรมต่างจาก rag/search ที่ 422; บันทึก contract ก่อนตัดสินใจ normalize |
| ต่ำ | UI ส่งเฉพาะ single infer และทดสอบเพียง HTML served | ยังไม่มี batch/search/evaluate controls หรือ browser E2E; อย่าอ้างว่าทดสอบ workflow browser ครบ |

ข้อขัดแย้งกับ specification ถูกบันทึกไว้ที่นี่ รอบนี้เพิ่ม evaluation integration และ explicit offline pipeline option โดยไม่เปลี่ยน canonical schema, subset, gold labels หรือ lexical rules เพื่อกลบข้อขัดแย้ง

## การตรวจที่ทำซ้ำได้

Python .venv 3.11.15, provider keys ทั้งสองว่าง:

~~~bash
python -m src.rag.ingest_stix
GOOGLE_API_KEY='' GEMINI_API_KEY='' python -m pytest -q
python -m compileall -q src eval tests
git diff --check
git status --short
~~~

Baseline ก่อน C: 62 passed; ชุด C เดิมร่วม A+B+D: 77 passed ส่วนผล integration รอบนี้ดู [C_IMPLEMENTATION_SUMMARY_TH.md](C_IMPLEMENTATION_SUMMARY_TH.md)

Ingestion พบ 25,843 STIX objects และ 127 candidates/IDs: credential-access 58, execution 48, initial-access 21 มี T1110 และ T1059.001; generated files ในสำเนาอยู่ใต้ /tmp ไม่ได้เพิ่มเข้า Git

Compileall ผ่าน ผล whitespace/status ตรวจซ้ำหลังแก้เอกสาร ไม่ได้ยืนยันว่าติดตั้ง dependencies ใหม่ทุกตัวใน fresh venv หรือ GitHub Actions ล่าสุดผ่าน

## ตัวอย่างตรวจพฤติกรรมจริงแบบ offline

เรียก run_inference กับ RETRIEVER จริงโดย key ทั้งสองว่าง ใช้ข้อความจำลอง ไม่ใช่ข้อมูลลูกค้าหรือ gold dataset ที่ผู้สอนรับรอง:

| Narrative | Predictions (confidence) | needs_human_review |
| --- | --- | --- |
| Host WIN-SRV-04 logged 847 failed RDP authentication attempts, followed by execution of encoded PowerShell. | T1059.001 (0.75), T1574.014 (0.65) | false |
| Authorized administrator used PowerShell commands for routine maintenance. No malicious activity was observed. | T1059.001 (0.75), T1072 (0.75), T1204 (0.65) | false |

ตัวอย่างแรกไม่คืน T1110 แม้ข้อความพูดถึง failed authentication; ตัวอย่างที่สองไม่ส่ง human review แม้มี benign/negation context เป็นหลักฐานว่าจับคำและ structural checks ยังไม่พอสำหรับตัดสินเจตนาหรือความกำกวม ผลนี้ไม่ใช่การคำนวณ F1/FPR บน dataset และยังไม่สรุป gold labels ของแต่ละรายการแทนผู้สอน

ตรวจ candidates/allowlist ใน workspace เท่ากัน 127 IDs และ candidate version ทุกตัวเป็น 19.1; OpenAPI มี /evaluate แล้วหลัง C integration

## ผล runtime evaluation บน RC dataset 35 alerts

| เกณฑ์ specification | เป้าหมาย | สถานะ |
| --- | --- | --- |
| Exact technique F1 | ≥70% | 34.55% ยังไม่ผ่าน |
| Parent technique recall | ≥90% | 52.70% ยังไม่ผ่าน; ใช้ partial credit 0.5 จาก C |
| Hallucinated ID rate | 0 | 0% ใน runtime run นี้ |
| Evidence grounding rate | ≥85% | substring 100%; ยังไม่พิสูจน์ semantic grounding |
| False-positive rate | รายงานบน benign controls | 40% หรือ 2/5 negatives |

ข้อกำหนดกล่าวถึง 35 alerts, ambiguous/multi-technique 10 และ negative 5 แต่ไม่ชัดว่ากลุ่มย่อยนับรวม 35 หรือเพิ่มเป็น 50; แผน C เดิมตีความเป็น 35 รวมทั้งหมด ต้องยืนยันกับผู้สอนก่อนล็อก dataset อย่าอ้างว่าการแบ่ง 20/5/5/5 เป็นข้อกำหนดตายตัว

ดูรายละเอียดไฟล์ใน [PROJECT_FILE_MAP_TH.md](PROJECT_FILE_MAP_TH.md) และลำดับแก้ใน [WORK_PLAN_TH.md](WORK_PLAN_TH.md)
