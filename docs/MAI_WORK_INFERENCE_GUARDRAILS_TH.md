# Inference, evidence และ guardrails

อัปเดต 7 กันยายน 2026 อ้างอิง src/agents/ และ [specification](../security-alert-attack-technique-inference.md) หัวข้อ 5/6/10

| ฟังก์ชัน | พฤติกรรม |
| --- | --- |
| infer_techniques(narrative, candidates, max_results=3) | ตัดคำ a-z/0-9 ยาว≥4, ตัด stopwords, ต้องตรง≥2 คำ, เรียง score/ID และ deduplicate IDs |
| link_evidence(narrative, inferred) | เก็บ exact spans ที่มี token ASCII alphanumeric≥4 ตัว ตัด spans ซ้ำและ prediction ที่ไม่เหลือ span |
| judge_result(narrative, inferred, candidates) | คืน bool review เมื่อ no-match, >3, duplicate, ID/name/tactic ไม่ตรง, ไม่มี evidence ที่ผ่าน หรือ confidence<0.65 |
| parse_alert(narrative, generate=...) | คง narrative เดิม, validate provider JSON, fallback lists ว่าง |
| route_tactics(alert, generate=...) | กรองสาม tactics และ fallback ทั้งสามเมื่อ output/failure ใช้ไม่ได้ |

## สิ่งที่ไม่ควรตีความเกินโค้ด

- Judge ตั้ง flag ไม่ได้ลบ prediction ทุกตัวที่ผิด; ต้องใช้ร่วมกับ candidate-bounded inferencer/linker
- Exact substring ไม่พิสูจน์ความเกี่ยวข้องเชิงความหมายหรือการเป็นพฤติกรรมอันตราย
- Inferencer ให้คะแนนเริ่ม≥0.65 เมื่อผ่านเกณฑ์สองคำ; threshold<0.65 ของ judge จึงไม่ครอบคลุม ambiguous predictions ปกติ
- ภาษาไทยรับเข้า schema ได้ แต่ inferencer tokenization เป็น ASCII และ knowledge base ภาษาอังกฤษ ไม่ได้รับรอง Thai semantic inference
- Escaped prompt delimiters และ bounded IDs ลดบางความเสี่ยงของ injection แต่ยังไม่พิสูจน์ว่า in-scope false positives เกิดไม่ได้
- SDK timeout/retry มีแล้ว; parser/router จับ errors จึง fallback และผลอาจยังมี prediction

## Test coverage และงานต่อ

tests/test_agents.py และ tests/test_inference_guardrails.py ตรวจ candidate boundaries, duplicate, invalid evidence, malformed JSON, fake timeout และ delimiter injection; tests/test_gemini_client.py ตรวจ client config โดย mock ไม่ได้เรียก provider จริง

งานต่อคือ semantic grounding, negation/benign/ambiguous cases, calibrated confidence และ measurement จาก C ไม่ควรอ้างว่า structural test ที่ผ่านเท่ากับผ่าน evidence quality gate

ดู [รายงาน](PROJECT_REVIEW_TH.md) สำหรับ privacy/network/logging gaps และ [แผนงาน](WORK_PLAN_TH.md) สำหรับลำดับก่อนรับมอบ
