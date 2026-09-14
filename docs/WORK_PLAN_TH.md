# สถานะงานตามแผนปิดโครงการ

อัปเดต 14 กันยายน 2026 บน mai-work โดยยึด [ข้อกำหนดหลัก](../security-alert-attack-technique-inference.md) และ [PROJECT_COMPLETION_PLAN_TH](PROJECT_COMPLETION_PLAN_TH.md)

| งาน | ผลล่าสุด | งานคงเหลือ |
| --- | --- | --- |
| KB/retrieval | ตรวจ pinned hash, atomic snapshot, metadata ครบ, full-description BM25 และ behavior reranking | approved subset 30–50 IDs และ retrieval misses ที่ยังเหลือ |
| Inference/guardrails | behavior-rules-v2, contextual evidence, negation/ambiguity, candidate/ID/URL guard | parent recall, กรณีกำกวม, independent semantic review/calibration |
| API/security | lifespan, typed 503, bounded workers/deadline, auth/rate limit/CORS, safe logs, offline API | target deployment approval และ controls ระดับ gateway หาก deploy จริง |
| Evaluation | 47 development cases, error taxonomy, confidence audit, fixture/full runtime gates | locked course dataset/gold review และ full parent-recall gate |
| Acceptance | tests 125 ผ่าน, browser E2E, demo 5 ขั้น, clean-copy verification scripts | final acceptance เมื่อ quality และ approval ครบ |

Full course pack: F1 81.82%, parent recall 72.97%, FPR 0%, hallucinated ID 0%, verbatim grounding 100%.
Parent recall ยังต่ำกว่า 90%; ห้ามสรุปว่า quality gates หรือโครงการเสร็จ 100%.

ดู [ไฟล์อธิบายสิ่งที่ทำทั้งหมด](PROJECT_COMPLETION_IMPLEMENTATION_TH.md), [decision record](PROJECT_COMPLETION_DECISIONS_TH.md) และ [หลักฐาน](reports/runtime-final.json)

## ลำดับที่ยังต้องปิด

1. ผู้สอนยืนยัน subset, composition, gold labels, parent credit, FPR threshold และ environment โดยบันทึกหลักฐานจริง
2. ใช้ approved manifest ทำ ingestion และตรวจ snapshot/allowlist ให้ตรงกับ evaluation ก่อนล็อกข้อมูล
3. แก้ retrieval/inference misses บน development fixtures และตรวจ ambiguity โดยใช้ diagnostics; ไม่เปลี่ยน gold/threshold ให้เข้ากับ output
4. ตรวจ semantic grounding และ confidence บนชุดข้อมูลที่ผู้ตรวจอิสระรับรอง
5. รัน full runtime quality gates จนผ่าน แล้วทำ acceptance/release ใน environment ที่อนุมัติ

ผลใน docs/reports เป็นผล local ไม่ใช่การรับรอง GitHub Actions หรือ deployment ภายนอก
