# บันทึกงานสายงาน B: Inference, Evidence และ Guardrails

อัปเดต: 31 สิงหาคม 2026
สถานะ: **สายงาน B พร้อมส่งต่อให้ D เชื่อมระบบ**
ขอบเขต: Agent Architecture, Data Schemas และ Security & Guardrails ตาม `security-alert-attack-technique-inference.md`

## สิ่งที่ทำแล้ว

สร้างโมดูลสายงาน B พร้อม unit tests โดยยังไม่เชื่อม API และไม่เรียก Gemini จริง เพื่อให้ผลทดสอบทำซ้ำได้และไม่ให้ Alert ที่เป็น untrusted input สั่งการ provider

| ส่วน | ไฟล์ | พฤติกรรม |
| --- | --- | --- |
| Technique Inferencer | `src/agents/technique_inferencer.py` | จัดอันดับ candidates ด้วยคำสำคัญจากชื่อ/คำอธิบายที่ปรากฏใน narrative, คืนได้ 1–3 รายการ, เรียงผลแบบ deterministic และสร้าง no-match เมื่อหลักฐานคำไม่เพียงพอ |
| Evidence Linker | `src/agents/evidence_linker.py` | เก็บเฉพาะ `evidence_spans` ที่เป็น exact substring ของ narrative จึงตรวจย้อนกลับได้ |
| Grounding Judge | `src/agents/grounding_judge.py` | ตัดสิน `needs_human_review` สำหรับ no-match, ผลเกิน 3, ID/name/tactic ไม่ตรง candidate, evidence ไม่พบจริง, confidence ต่ำ หรือ ID ซ้ำ |
| Alert Parser (งานเสริม) | `src/agents/alert_parser.py` | รับ `generate` ที่ฉีดได้; output ที่ JSON เสียหรือ provider timeout จะคืน `ParsedAlert` ว่างโดยคง narrative เดิม |
| Tactic Router (งานเสริม) | `src/agents/tactic_router.py` | รับ `generate` ที่ฉีดได้; กรอง tactic นอก scope และ fallback ไปค้นทั้ง 3 tactic เมื่อ output/provider ใช้ไม่ได้ |

## Contract ที่ใช้

```python
infer_techniques(
    narrative: str,
    candidates: list[TechniqueCandidate],
    *,
    max_results: int = 3,
) -> list[InferredTechnique]

link_evidence(
    narrative: str,
    inferred: list[InferredTechnique],
) -> list[InferredTechnique]

judge_result(
    narrative: str,
    inferred: list[InferredTechnique],
    candidates: list[TechniqueCandidate],
) -> bool  # True = needs_human_review
```

`TechniqueCandidate.tactic` และ `InferredTechnique.tactic` ยังคงเป็น `str` ตาม schema หลัก ไม่มีการเพิ่ม field ใน `ATTACKInferenceResult` และ URL ของ MITRE สร้างจาก ID ที่ผ่าน allowlist แล้วเท่านั้น

สำหรับ integration ให้ D เรียกตามลำดับนี้ โดยไม่ต้องเรียก parser/router ใน MVP รอบแรก:

```python
candidates = retrieve_candidates(narrative, tactic=None, top_k=5)
inferred = infer_techniques(narrative, candidates)
inferred = link_evidence(narrative, inferred)
needs_human_review = judge_result(narrative, inferred, candidates)
```

## Guardrails ที่บังคับใช้

- Inferencer คืนได้เฉพาะ technique ที่อยู่ใน `candidates` จาก Retriever; ไม่สร้าง ID เอง
- Alert ถูกอ่านเป็นข้อความสำหรับการจับหลักฐานเท่านั้น จึงไม่มีคำสั่งใน alert ที่เปลี่ยนกติกาหรือทำให้คืน ID นอก candidate ได้
- หลักฐานทุกช่วงต้องพบจริงใน narrative ก่อนส่งต่อ
- ค่า confidence ต่ำกว่า `0.65` ต้องส่ง human review
- no-match เป็นผลลัพธ์ปลอดภัยและต้องส่ง human review
- candidate ซ้ำจะไม่ทำให้ inferencer คืน prediction ซ้ำ และ evidence span ซ้ำจะถูกตัดออก
- parser/router ใส่ alert ไว้ใน untrusted delimiters; provider ที่ตอบผิดรูปแบบหรือ timeout จะไม่ทำให้เกิด exception หรือ tactic นอก scope

## Tests ที่เพิ่ม

อยู่ใน `tests/test_agents.py` และ `tests/test_inference_guardrails.py` ครอบคลุม:

- inference ปกติของ PowerShell พร้อม evidence และ MITRE URL
- prompt injection ที่พยายามบังคับให้คืน `T9999` แล้วได้ no-match
- evidence ที่ถูกสร้างขึ้นแต่ไม่อยู่ใน alert ถูกตัดออก
- unknown ID, low confidence และ no-match ต้องตั้ง review
- prediction ซ้ำ, เกิน 3 รายการ, name/tactic ไม่ตรง candidate และ evidence ซ้ำหรือไม่พบจริง
- parser/router ที่ใช้ fake provider สำหรับ valid output, malformed JSON, timeout และ tactic ที่พยายามออกนอก scope

## ผลตรวจ

คำสั่งที่รัน:

```bash
python -m pytest -q
git diff --check
```

ผลล่าสุด: `27 passed` และ `git diff --check` ผ่าน

## สิ่งที่ยังไม่ทำ / ขั้นต่อไป

- D เชื่อมโมดูลเข้ากับ `POST /alerts/infer` หลัง Retriever พร้อม
- หากจะใช้ Gemini ใน runtime ต้องเพิ่ม timeout, retry, typed error และ structured-output validation ที่ระดับ provider/API; output ต้องผ่าน Evidence Linker และ Grounding Judge เสมอ
- C นำ saved predictions ไปประเมินผลกับ gold dataset เมื่อพร้อม
