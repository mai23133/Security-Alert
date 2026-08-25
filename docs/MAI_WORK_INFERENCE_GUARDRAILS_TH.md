# บันทึกงานสายงาน B: Inference, Evidence และ Guardrails

วันที่: 25 สิงหาคม 2026  
ขอบเขต: Agent Architecture, Data Schemas และ Security & Guardrails ตาม `security-alert-attack-technique-inference.md`

## สิ่งที่ทำแล้ว

สร้างโมดูลสายงาน B จำนวน 3 ส่วน พร้อม unit tests โดยยังไม่เชื่อม API และไม่เรียก Gemini จริง เพื่อให้ผลทดสอบทำซ้ำได้และไม่ให้ Alert ที่เป็น untrusted input สั่งการ provider

| ส่วน | ไฟล์ | พฤติกรรม |
| --- | --- | --- |
| Technique Inferencer | `src/agents/technique_inferencer.py` | จัดอันดับ candidates ด้วยคำสำคัญจากชื่อ/คำอธิบายที่ปรากฏใน narrative, คืนได้ 1–3 รายการ, เรียงผลแบบ deterministic และสร้าง no-match เมื่อหลักฐานคำไม่เพียงพอ |
| Evidence Linker | `src/agents/evidence_linker.py` | เก็บเฉพาะ `evidence_spans` ที่เป็น exact substring ของ narrative จึงตรวจย้อนกลับได้ |
| Grounding Judge | `src/agents/grounding_judge.py` | ตัดสิน `needs_human_review` สำหรับ no-match, ผลเกิน 3, ID/name/tactic ไม่ตรง candidate, evidence ไม่พบจริง, confidence ต่ำ หรือ ID ซ้ำ |

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

## Guardrails ที่บังคับใช้

- Inferencer คืนได้เฉพาะ technique ที่อยู่ใน `candidates` จาก Retriever; ไม่สร้าง ID เอง
- Alert ถูกอ่านเป็นข้อความสำหรับการจับหลักฐานเท่านั้น จึงไม่มีคำสั่งใน alert ที่เปลี่ยนกติกาหรือทำให้คืน ID นอก candidate ได้
- หลักฐานทุกช่วงต้องพบจริงใน narrative ก่อนส่งต่อ
- ค่า confidence ต่ำกว่า `0.65` ต้องส่ง human review
- no-match เป็นผลลัพธ์ปลอดภัยและต้องส่ง human review

## Tests ที่เพิ่ม

อยู่ใน `tests/test_agents.py` ครอบคลุม:

- inference ปกติของ PowerShell พร้อม evidence และ MITRE URL
- prompt injection ที่พยายามบังคับให้คืน `T9999` แล้วได้ no-match
- evidence ที่ถูกสร้างขึ้นแต่ไม่อยู่ใน alert ถูกตัดออก
- unknown ID, low confidence และ no-match ต้องตั้ง review

## ผลตรวจ

คำสั่งที่รัน:

```bash
python -m pytest -q
git diff --check
```

ผลล่าสุด: `21 passed` และ `git diff --check` ผ่าน

## สิ่งที่ยังไม่ทำ / ขั้นต่อไป

- เชื่อมโมดูลเข้ากับ `POST /alerts/infer` หลัง Retriever พร้อม
- หากจะใช้ Gemini ต้องมี timeout, retry, structured-output validation และ mock tests; output ต้องผ่าน Evidence Linker และ Grounding Judge เสมอ
- เพิ่มกรณี malformed provider output ตอนทำ integration เพราะ implementation รอบนี้ไม่มี provider call โดยเจตนา
- ประเมินผลกับ gold dataset เมื่อสายงาน Evaluation พร้อม
