# สถานะงานตามแผนปิดโครงการ

อัปเดต 17 กันยายน 2026 บน base commit `0a9071e` โดยยึด [ข้อกำหนดหลัก](../security-alert-attack-technique-inference.md)

| งาน | ผลปัจจุบัน | งานคงเหลือ |
| --- | --- | --- |
| KB/Retrieval | pinned STIX hash, atomic snapshot, metadata, BM25 + behavior reranking | ผู้สอนอนุมัติ subset 30–50 IDs หรืออนุมัติ 127 IDs |
| Offline inference | `behavior-rules-v3`, contextual evidence, candidate/ID/URL guards | independent semantic review/calibration |
| Online inference | Gemini/OpenRouter ครบ Parser → Router → Inferencer → Judge, consent/redaction/circuit breaker | full-set metrics หลังได้ quota ที่เพียงพอ |
| API/Security | lifespan, typed errors, 4 workers, 60s default deadline, auth, rate limit, CORS, safe logs | gateway/HTTPS/distributed quota หาก deploy จริง |
| Evaluation | 35 gold alerts, Iteration 2 comparison, diagnostics, prompt/model/hash metadata | locked labels และ independent review |
| Acceptance | 207 tests, browser E2E รวม prompt-injection fail-closed, demo 5 ขั้น, clean-copy verification และ numeric gates ผ่าน | final course approval และ CI confirmation หลัง push |
| Presentation | 10-minute script, 3-minute demo, model-results table | ซ้อมเวลาและ commit/push เอกสารล่าสุด |

## ผลล่าสุด

- Exact F1: 97.30% (เกณฑ์ ≥70%)
- Parent recall: 97.30% (เกณฑ์ ≥90%)
- Evidence grounding: 100% (เกณฑ์ ≥85%)
- Hallucinated ID: 0%
- False-positive rate บน negative controls 5 รายการ: 0%
- Tests: 207 ผ่าน, failures/errors/skipped = 0

ตัวเลขทั้งหมดเป็นผล Offline `behavior-rules-v3` บน full gold set 35 alerts ไม่ใช่คะแนน Gemini/OpenRouter

## ลำดับที่ยังต้องปิด

1. ผู้สอนยืนยัน subset, composition, gold labels, parent credit, FPR threshold และ target environment
2. ทำ ingestion ด้วย approved manifest แล้วรัน full gates ใหม่โดยไม่เปลี่ยน gold/threshold ตาม output
3. ให้ผู้ตรวจอิสระตรวจ semantic grounding และ confidence
4. หากต้องการคะแนน LLM ให้ใช้ quota/model ที่ระบุแน่นอน แล้วรัน strict full-set ใหม่
5. ยืนยัน CI/release หลัง commit/push

ผล local ผ่าน numeric gates แต่ `acceptance_ready` ยังเป็น false เพราะ approval สองรายการแรกยังไม่ครบ
