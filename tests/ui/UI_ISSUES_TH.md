# ผลตรวจและเชื่อมข้อมูล UI — ตรวจทานล่าสุด 18 กันยายน 2026

อ่าน `security-alert-attack-technique-inference.md` ทั้งไฟล์ก่อนทำงาน และอ้างอิงหัวข้อ 6 Data Schemas, 8 API Contract, 9 Evaluation, 10 Security & Guardrails และ 11 UI สัปดาห์ที่ 6

## ขอบเขตครั้งนี้

คงหน้าตา React เดิม: สองแท็บ การ์ดคะแนน 4 ใบ ตาราง 5 คอลัมน์ ตัวกรอง และ Guardrail cards 4 ใบ ไม่แก้ CSS หรือจัดหน้าใหม่ เปลี่ยนเฉพาะข้อมูล ข้อความที่อ้างผลเกินจริง สถานะตามผลจริง และจุดเชื่อม API ที่เกี่ยวข้อง ไม่มีการเพิ่ม launcher หรือ deploy ในงานรอบนี้

## วิเคราะห์ก่อนแก้

| ส่วน | สถานะก่อนแก้ | สิ่งที่แก้ครั้งนี้ |
| --- | --- | --- |
| ข้อความ Alert และ sample picker | เรียก `/alerts/infer` จริงแล้ว | คงการเชื่อมเดิม; ล้างผลเก่าเมื่อแก้ข้อความ/เลือก sample และยกเลิกการรอผลเดิม |
| Technique ID, name, tactic | แสดงข้อมูลจริงจาก API | คงไว้ |
| Confidence | รับค่าจริง แต่เดาหน่วยได้ทั้ง 0–1/0–100 | ใช้ 0–1 ตาม schema และแปลงเป็นเปอร์เซ็นต์ |
| Evidence | แสดง API แต่ตัดเครื่องหมายคำพูดในข้อความ | แสดง evidence ต้นฉบับครบถ้วน |
| Human review และ no-match | ใช้ flag จริง แต่ข้อความอ้าง semantic verification/benign เกินจริง | ระบุ structural check และไม่ยืนยันว่า no-match คือปลอดภัย |
| Disclaimer/Alert ID | Disclaimer เป็นข้อความคงที่; ไม่แสดง Alert ID | ใช้ disclaimer และ Alert ID จาก response ในพื้นที่เดิม |
| Candidates | ID/ชื่อจริง แต่หัวข้อเขียน TOP-5 ตายตัว | แสดงจำนวนจริง คงตาราง ID/ชื่อเดิม |
| Metric scorecards | 78/93/88/0 เป็นตัวเลขจำลอง | อ่าน metrics และ quality_gates จาก `/evaluate` |
| Run Full Evaluation | จับเวลาแล้วแสดงว่าสำเร็จ | เรียก runtime evaluation จริง พร้อมสถานะรอ/ข้อผิดพลาด/timeout |
| Test breakdown | 22 แถวจำลอง มี ID นอกขอบเขต | ใช้ `case_results` จาก backend รองรับ multi-label และตัวกรองเดิม |
| จำนวนชุดทดสอบ | ระบุ 35+10+5 โดยไม่ตรง dataset | อ่าน `category_counts` จากรายงาน |
| Security guardrails | PASS และตัวเลขตั้งไว้ทั้งหมด | แสดง membership check ที่วัดได้จริง; การตรวจที่ยังไม่มีข้อมูลแสดง NOT MEASURED |
| Version badge | v2.4.1 ไม่มีที่มาจากระบบ | ใช้ข้อความ API แทนการอ้างเลขรุ่นปลอม |

## การเชื่อมและความเข้ากันได้

- UI ส่ง `POST /evaluate` ด้วย `{ "mode": "runtime", "top_k": 5 }` ประเมิน pipeline กับ bundled dataset โดยปิด Gemini เสมอ
- เพิ่ม `case_results` และ `metadata.category_counts` ในรายงานโดยรักษา request, endpoints และ fields เดิมทั้งหมด ไม่เปลี่ยน `ATTACKInferenceResult`, taxonomy, gold labels หรือสูตร metrics
- `case_results` มี gold/predicted IDs, Exact/Parent/Miss, grounded, review และ ID ที่อยู่นอก subset แต่ไม่มีข้อความ Alert/evidence
- Exact เทียบ label sets ทั้งชุด; Parent ต้องครอบคลุม gold ทุกตัวด้วย ID เดิมหรือ parent โดยไม่มี prediction เกินที่ไม่เกี่ยวข้อง; ที่เหลือเป็น Miss การจัดแถวนี้ไม่เปลี่ยนสูตร aggregate metrics
- ไม่มี prediction แสดง grounding เป็น N/A; ค่ารวม grounding ยังคำนวณเฉพาะ predictions ตาม evaluator เดิม
- ก่อนรันและหลังรันผิดพลาด คะแนนเป็น — / NOT RUN ไม่ใช้ค่าศูนย์หรือผลเก่ามาแทน
- ป้องกันกดรันซ้ำระหว่างรอ ยกเลิกการรอเมื่อออกจากแท็บ และ timeout ฝั่ง UI 120 วินาที การยกเลิกฝั่ง browser ไม่รับประกันว่าจะหยุดงาน backend ที่เริ่มแล้ว
- เพิ่ม proxy `/evaluate` ใน Vite เช่นเดียวกับ `/alerts` เพื่อใช้ได้ทั้ง dev server และหน้า `/ui` บน FastAPI
- อัปเดต HTML แบบรวมไฟล์จาก source ล่าสุด และแก้การสร้าง newline/whitespace ให้ผ่าน diff check

## ผลทดสอบจริง

- Python test suite: **117 passed** (ปิด provider keys)
- TypeScript และ Vite production build: ผ่าน
- Browser smoke บน Edge กับ FastAPI จริงที่แยกพอร์ตและปิด provider: ผ่าน inference, evaluation, ตัวกรอง Exact/Parent/Miss, API 503, report ผิดรูปแบบ, timeout และการออกจากแท็บระหว่างรอ ไม่มี page error
- เทียบคะแนนและ gold/predicted IDs ทุกแถวบน UI กับ response จริง: ตรงกันทั้ง 35 แถว
- ตรวจภาพหน้าเว็บแล้ว ยังคงโครงหน้าเดิม; CSS ไม่ได้แก้
- `git diff --check` ผ่าน และตรวจ `git status --short` ก่อนส่งงาน

| ตัวชี้วัด runtime offline ชุดปัจจุบัน | ผล | เป้าหมาย |
| --- | --- | --- |
| Exact technique F1 | 34.5% | ≥70% — ไม่ผ่าน |
| Parent technique recall | 52.7% | ≥90% — ไม่ผ่าน |
| Evidence grounding (exact substring) | 100% | ≥85% — ผ่านเฉพาะวิธีวัดนี้ |
| Hallucinated ID rate | 0% | 0% — ผ่าน |
| False-positive rate | 40.0% | ไม่มี gate กำหนดใน evaluator |
| Human-review rate | 22.9% | ไม่มี gate กำหนดใน evaluator |

ผลนี้เป็น lexical-baseline offline บน 35 รายการ ไม่ใช่ผลประเมิน Gemini และไม่ใช่การรับรองพร้อมใช้งาน production ความสำเร็จของการเชื่อม UI ไม่ได้ทำให้คุณภาพโมเดลผ่านเกณฑ์

## ยังขาด/ข้อขัดแย้งที่ต้องตัดสินใจต่อ

1. ข้อมูลจริงมี 20 positive + 5 multi-technique + 5 ambiguous + 5 negative รวม 35 รายการ ซึ่งไม่ตรงองค์ประกอบ 35 + 10 + 5 ตาม specification ต้องยืนยันกับผู้สอน; รอบนี้ไม่สร้างหรือเปลี่ยน gold labels เอง
2. Subset backend เดิมมี 127 candidates เกินเป้าหมาย 30–50; ต้องตกลง subset ก่อนปรับ ไม่เปลี่ยน allowlist เพื่อทำคะแนนให้ดีขึ้น
3. ยังไม่มีผล runtime วัด prompt injection, leakage, action containment หรือ confidence calibration จึงไม่แสดง PASS ปลอม การมี unit tests บางรายการไม่เท่ากับวัดตัวเลขเหล่านี้แล้ว
4. Grounding ปัจจุบันตรวจข้อความตรงกัน ไม่ใช่ semantic correctness; gold-label review และ final acceptance ยังไม่ผ่าน
5. UI ยังไม่แสดงรายละเอียด candidate ทั้ง description/tactic/version รายตัว หรือ parsed assets/IOCs/actions; candidate details มีบางส่วนใน API แต่ parsed entities ไม่อยู่ใน final response schema จึงไม่เพิ่มข้อมูลเดาเพื่อเติมหน้าจอ
6. การตรวจ taxonomy แบบแยกหน้า, batch และ RAG search แบบอิสระยังไม่มีหน้าจอเฉพาะ แม้มี API; ไม่จำเป็นต้องเพิ่มเพื่อแก้ข้อมูลจำลองครั้งนี้
7. Header แสดง pinned version ไม่ใช่ health check ของ provider; ไม่มีการอ้างว่า inference ทุกครั้งใช้ Gemini สำเร็จ
8. `/evaluate` ปัจจุบันทำ synchronous work ภายใน async route อาจ block event loop; รองรับใช้งาน local ทดสอบได้ แต่ควรแยก worker/จัดการ concurrency ก่อนใช้งานหลายคน
9. Authentication, rate limiting, retention/privacy enforcement และการ deploy ส่วนกลางยังต้องทำตามข้อกำหนดก่อนใช้ Alert จริง

ทางเลือกถัดไปคือยืนยัน dataset/subset กับผู้สอนแล้วปรับคุณภาพ backend และเพิ่มผลตรวจ guardrails ที่มีแหล่งข้อมูลจริง โดยคง UI ชุดนี้เป็นหน้ารับข้อมูลจากระบบ

## วิธีใช้

หน้า `/ui` บน FastAPI: เปิด backend แล้วเข้า `http://127.0.0.1:8000/ui` เลือกแท็บ **Eval & Guardrails** และกด **Run Full Evaluation** ครั้งนี้ build ไฟล์หน้าเว็บให้แล้ว ต้องรีสตาร์ต backend ที่เปิดค้างอยู่เพื่อโหลด evaluator รุ่นใหม่

หากแก้ source ภายหลัง ให้รัน `npm run build` ใน `ui` หนึ่งครั้ง แล้วรีเฟรชหน้า หากใช้ Vite dev server ให้เปิด backend พอร์ต 8000 และรัน `npm run dev` ใน `ui`; `/alerts` และ `/evaluate` จะถูกส่งต่อผ่าน proxy

ไฟล์ `เปิดหน้า-UI.html` เปิดดูหน้าได้ แต่การวิเคราะห์/ประเมินต้องเปิดผ่านเว็บที่เชื่อม backend ไม่มีผลจำลองสำรองเมื่อ API ใช้ไม่ได้

ทดสอบ browser ซ้ำด้วย `node ui/tests/evaluation.smoke.cjs` หลัง build ต้องมี Playwright และ Edge ในเครื่อง (หรือกำหนด NODE_PATH ไปยังชุดเครื่องมือที่ติดตั้งไว้) ตัวทดสอบเปิด backend พอร์ตชั่วคราวและปิดให้อัตโนมัติ ไม่ใช้ API key จริง
