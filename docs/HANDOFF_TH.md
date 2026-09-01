# เอกสารส่งต่องาน Security-Alert

อัปเดต: 1 กันยายน 2026
สถานะ: สาย A และ B ถูกเชื่อมกับ `/alerts/infer` แล้วระดับ baseline; C และงาน API/deployment ที่เหลือยังดำเนินต่อ

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
| `POST /alerts/infer` | pipeline parser → router → BM25 retriever → inference → evidence → judge |
| สาย A | BM25 retrieval baseline พร้อมใช้งาน; ยังไม่มี platform/source metadata และมี 127 candidates |
| สาย B | candidate-bounded inference และ structural grounding พร้อมใช้งาน; semantic grounding ยังเป็น gap |
| สาย C | กำลังทำ dataset/metrics |
| สาย D | API integration ของ infer เสร็จแล้ว; batch/search, typed errors, CI และ UI ยังเหลือ |

ผลตรวจล่าสุด: `python -m pytest -q` ผ่าน 42 tests

## Contract ที่ใช้งานจริง

```python
parsed = parse_alert(narrative)
tactics = route_tactics(parsed)
candidates = retriever.search(parsed.narrative, tactic=tactics, top_k=5)
inferred = link_evidence(parsed.narrative, infer_techniques(parsed.narrative, candidates))
needs_human_review = judge_result(parsed.narrative, inferred, candidates)
```

ผลลัพธ์ต้องอยู่ใน `ATTACKInferenceResult` ตาม schema เดิม, คง disclaimer และไม่เพิ่ม Technique ID นอก candidates/allowlist

## ข้อห้ามสำคัญ

- ห้ามใช้ Mobile/ICS ATT&CK, TAXII online เป็น dependency หลัก หรือ automated response
- ห้ามให้ alert text หรือ provider output เปลี่ยนกติกา pipeline
- ห้ามให้ tests เรียก Gemini/network จริง หรือ commit secrets/raw alert ที่ยังไม่ sanitize
- ก่อนส่งงานให้รัน `python -m pytest -q`, `git diff --check` และ `git status --short`
