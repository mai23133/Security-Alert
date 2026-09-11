# แผนงานหลังรวม C

อัปเดต 7 กันยายน 2026 บน mai-work: ฐาน e2ee2da รวม yean-work 5d56d31 ที่ commit 6b3a38c แล้ว [ข้อกำหนดหลัก](../security-alert-attack-technique-inference.md) ยังคงเดิม

| สาย | ส่งมอบ | งานคงเหลือ |
| --- | --- | --- |
| A | pinned ingestion, BM25, allowlist/top-k/tactic filters | subset/metadata และ retrieval quality |
| B | parser/router fallback, lexical inference, structural guards | semantic grounding/ambiguity/negation และ confidence |
| C | RC dataset, metrics, fixture/runtime runner, bounded /evaluate | ผู้สอนตรวจ labels/จำนวน/parent credit และ runtime gates |
| D | API/UI/CI ingestion/tracing | KB startup lifecycle, concurrency/deadline, auth/rate-limit/privacy |

## ลำดับถัดไป

1. Review ผล integration และนำ branch นี้เข้า mai-work เมื่อผู้ใช้พร้อม
2. ยืนยัน dataset composition, labels, partial-credit formula และ subset กับผู้สอน
3. ใช้ runtime report ที่มีแล้ววิเคราะห์ false-positive/false-negative โดยไม่ปรับ gold ให้เข้ากับ output
4. พัฒนา semantic grounding/negation/ambiguity และ retrieval บน development data พร้อมแยก evaluation set
5. รัน --mode runtime --require-quality-gates ตรวจ F1/parent/grounding/hallucination และ review semantic evidence เพิ่ม
6. ปิด operational controls และ acceptance tests ก่อนรับ alert จริงหรือ deploy

ผลปัจจุบัน F1 34.55%, parent recall 52.70%, FPR 40%; ยังไม่ผ่านรับมอบแม้ integration tests ผ่าน ดู [สรุป C](C_IMPLEMENTATION_SUMMARY_TH.md) สำหรับคำสั่งและขอบเขตหลักฐาน
