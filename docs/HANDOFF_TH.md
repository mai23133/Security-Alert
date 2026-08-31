# เอกสารส่งต่องาน Security-Alert

อัปเดต: 31 สิงหาคม 2026
สถานะ: สาย B ส่งมอบแล้ว; สาย A, C และ D กำลังทำงานตาม `TEAM_WORK_PARALLEL_PROPOSAL_TH.md`

## ภาพรวมสำหรับผู้รับงาน

Security-Alert รับข้อความ alert และมีเป้าหมายคืน MITRE ATT&CK Technique 1–3 รายการพร้อม confidence, tactic, evidence spans และ `needs_human_review` ผลลัพธ์เป็น advisory เท่านั้น ไม่มี automated response

เอกสารที่ต้องอ่านก่อนทำงาน:

1. `security-alert-attack-technique-inference.md` — Source of Truth
2. `docs/TEAM_WORK_PARALLEL_PROPOSAL_TH.md` — หน้าที่ของ A/B/C/D และ integration contract
3. `docs/WORK_PLAN_TH.md` — สถานะล่าสุดและงานคงเหลือ

## สถานะ repository ที่ยืนยันแล้ว

| ส่วน | สถานะ |
| --- | --- |
| Pinned STIX, allowlist, schema และ taxonomy API | พร้อมใช้งาน |
| `POST /alerts/infer` | safe no-match stub; ยังไม่เรียก pipeline |
| สาย B | พร้อมเชื่อม: `infer_techniques`, `link_evidence`, `judge_result` และ tests guardrails |
| สาย A | กำลังทำ retriever/index |
| สาย C | กำลังทำ dataset/metrics |
| สาย D | กำลังทำ API integration, CI และ UI |

ผลตรวจล่าสุด: `python -m pytest -q` ผ่าน 27 tests

## Contract สำหรับ D

```python
candidates = retrieve_candidates(narrative, tactic=None, top_k=5)
inferred = infer_techniques(narrative, candidates)
inferred = link_evidence(narrative, inferred)
needs_human_review = judge_result(narrative, inferred, candidates)
```

ผลลัพธ์ต้องอยู่ใน `ATTACKInferenceResult` ตาม schema เดิม, คง disclaimer และไม่เพิ่ม Technique ID นอก candidates/allowlist

## ข้อห้ามสำคัญ

- ห้ามใช้ Mobile/ICS ATT&CK, TAXII online เป็น dependency หลัก หรือ automated response
- ห้ามให้ alert text หรือ provider output เปลี่ยนกติกา pipeline
- ห้ามให้ tests เรียก Gemini/network จริง หรือ commit secrets/raw alert ที่ยังไม่ sanitize
- ก่อนส่งงานให้รัน `python -m pytest -q`, `git diff --check` และ `git status --short`
