# สรุปการรวมงานสาย A และ B

เอกสารนี้สรุปงานที่รวมเข้ากับ branch `mai-work` เพื่อให้สมาชิกทีมเห็นภาพเดียวกันก่อนทำงานส่วนถัดไป (อัปเดต 1 กันยายน 2026)

## ตอนนี้ระบบทำอะไรได้แล้ว

เมื่อเรียก `POST /alerts/infer` ระบบจะรับข้อความ Alert แล้วส่งผ่านขั้นตอนนี้:

```text
Alert narrative
  → Alert Parser
  → Tactic Router
  → BM25 Retriever
  → Technique Inferencer
  → Evidence Linker
  → Grounding Judge
  → ATTACKInferenceResult
```

ผลลัพธ์ยังเป็น **คำแนะนำสำหรับ analyst เท่านั้น** ไม่ใช่การตอบสนองเหตุการณ์อัตโนมัติ

## สาย A: Retrieval

งานจาก branch `P-work` ถูก merge แล้ว และใช้ BM25 แบบ offline เพื่อค้นหา Technique จากไฟล์ที่ตรึงเวอร์ชันไว้:

- Candidate: `data/processed/technique_candidates.json`
- Allowlist: `data/processed/technique_ids.json`
- Dependency เพิ่มแล้ว: `rank-bm25==0.2.2`

Retriever มีการควบคุมสำคัญดังนี้:

- คืนเฉพาะ Technique ID ที่อยู่ใน allowlist
- กรองได้ทั้ง tactic เดียวหรือหลาย tactic
- กำหนด `top_k` ได้ และจะ reject ค่า `0`, ค่าติดลบ หรือค่าที่ไม่ใช่จำนวนเต็ม
- เรียงผลลัพธ์แบบทำซ้ำได้ โดย score สูงก่อน และ Technique ID เป็นตัวตัดสินกรณีคะแนนเท่ากัน

ข้อจำกัดปัจจุบัน: candidate model มี metadata เพียง ID, ชื่อ, tactic, description และ STIX version; ยังไม่มี platform/source ตามเกณฑ์ Week 2 และ subset ปัจจุบันมี 127 candidates ซึ่งเกินเป้าหมายประมาณ 30–50 techniques ใน specification

## สาย B: Inference และ Guardrails

หลัง Retriever คืน candidate แล้ว Inferencer จะเลือกได้ไม่เกิน 3 Technique และเลือกได้จาก candidate ที่ Retriever ส่งมาเท่านั้น จึงไม่สร้าง Technique ID ขึ้นเอง

Evidence Linker จะเก็บเฉพาะ evidence span ที่:

1. ปรากฏจริงใน Alert แบบ exact substring
2. มีข้อความที่สื่อความหมายอย่างน้อยหนึ่ง token ความยาว 4 ตัวอักษร/ตัวเลข

Grounding Judge จะตั้ง `needs_human_review: true` เมื่อพบ no-match, confidence ต่ำ, Technique ซ้ำ, เกิน 3 รายการ, candidate ไม่ตรงกัน หรือ evidence ไม่ผ่าน

ข้อจำกัดปัจจุบัน: grounding ตรวจความตรงของ ID/name/tactic และการมีอยู่ของ substring แต่ยังไม่พิสูจน์เชิงความหมายว่า span นั้นสนับสนุน Technique ที่เลือก จึงยังต้องเพิ่ม semantic grounding ก่อนผ่าน quality gate

## การทำงานเมื่อไม่มี Gemini API key

ระบบทดสอบและ endpoint ยังรันได้โดยไม่ต้องมี `GOOGLE_API_KEY` หรือ `GEMINI_API_KEY`:

- Parser จะคืนค่า parse แบบว่าง โดยคง narrative ต้นฉบับไว้
- Router จะ fallback ไปค้นทั้ง 3 tactics ในขอบเขต
- Retriever และส่วนอนุมานทำงานแบบ deterministic ต่อได้

ดังนั้น automated tests ไม่เรียก Gemini หรือ network จริง

## การป้องกัน input ที่ไม่น่าเชื่อถือ

Alert ถือเป็น untrusted input ตามข้อกำหนดของโครงการ

- Parser และ Router serialize ข้อความก่อนแทรกใน prompt เพื่อไม่ให้ Alert ปิด `<untrusted_alert>` delimiter ได้
- Provider error หรือข้อมูล JSON ที่ผิดรูปแบบจะ fallback แบบปลอดภัย แทนการทำให้ API ล้ม
- Candidate ที่ใช้สร้างผลลัพธ์ต้องมาจาก pinned STIX subset และ allowlist เท่านั้น

## ไฟล์สำคัญ

| ไฟล์ | หน้าที่ |
| --- | --- |
| `src/rag/embedder.py` | tokenize ข้อความสำหรับ BM25 |
| `src/rag/retriever.py` | ค้นหา candidate จาก pinned subset |
| `src/inference_pipeline.py` | รวมลำดับการทำงาน A และ B |
| `src/api/routes/alerts.py` | Endpoint `/alerts/infer` |
| `src/agents/technique_inferencer.py` | เลือก Technique จาก candidate ที่ค้นได้ |
| `src/agents/evidence_linker.py` | ตรวจ evidence span |
| `src/agents/grounding_judge.py` | กำหนด `needs_human_review` |

## การตรวจสอบที่ทำแล้ว

ใช้ environment `sec-alert311` (Python 3.11.15):

```bash
python -m pip install -r requirements.txt
python -m pytest -q
git diff --check
```

ผลล่าสุด: `42 passed` และ `git diff --check` ผ่าน

## งานถัดไป

ส่วนที่ยังอยู่ในแผนงาน:

1. เติม platform/source metadata และตัดสินใจเรื่อง subset 127 รายการเทียบเป้าหมาย 30–50
2. เพิ่ม semantic evidence-to-technique grounding
3. เพิ่ม `POST /alerts/infer/batch` และ `POST /rag/search`
4. เพิ่ม typed errors, request ID, timeout/retry และ structured logging
5. สร้าง evaluation dataset, metrics และรายงานที่ทำซ้ำได้
6. วัด Exact F1, parent recall, grounding rate, hallucinated-ID rate และ false-positive rate
7. เพิ่ม CI, UI และ deployment controls เช่น CORS, authentication และ rate limiting

ก่อนนำผลไปใช้จริง ต้องให้ผู้เชี่ยวชาญตรวจผลลัพธ์ทุกครั้ง
