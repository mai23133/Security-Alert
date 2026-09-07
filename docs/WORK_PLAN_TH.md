# แผนงานปัจจุบัน

อัปเดต 7 กันยายน 2026 บน mai-work f567aa3 อ้างอิง [specification](../security-alert-attack-technique-inference.md) เป็นข้อกำหนด และเอกสารนี้เป็นสถานะงาน

## สถานะหลัง merge D

| สาย | ส่งมอบใน mai-work | งานเหลือ |
| --- | --- | --- |
| A | ingestion, BM25, allowlist/tactic/top-k และ deterministic ranking | subset 127 เทียบ 30–50, platform/source metadata |
| B | parser/router fallback, lexical inference, evidence และ review rules | semantic grounding, ambiguity/negation และ confidence calibration |
| C | มีเพียงไฟล์ evaluation ว่าง | dataset, metrics, runner, runtime report และ /evaluate |
| D | single/batch/search, UI, validation, tracing, SDK retry และ CI ingestion | KB lifecycle, total timeout/concurrency, log/privacy และ deployment controls |

PR #4 merge แล้วที่ f567aa3 และ CI fix ec73b10 อยู่ในประวัติ ไม่ต้องเปิด branch D เดิมเพื่อรวมซ้ำ ผลตรวจรอบนี้ 62 passed ทั้ง workspace และ clean checkout ที่ทำ ingestion ก่อน tests ดู [รายงาน](PROJECT_REVIEW_TH.md) สำหรับขอบเขตการตรวจ

## ลำดับงานถัดไป

1. ให้ C ใช้ mai-work ล่าสุดเป็นฐาน ตรวจ diff ของ branch C ใหม่ ไม่ใช้ review commit เก่าเป็นสถานะล่าสุด
2. ตกลงกับทีม/ผู้สอนเรื่องจำนวน dataset (35 รวม/50 แยก), subset และ parent partial-credit formula
3. ตรวจ dataset IDs, labels, categories, evidence และให้ผู้สอนตรวจ gold labels; saved predictions ต้องแยก fixture จาก runtime
4. รวม metrics/runner/tests ก่อน แล้วกำหนด request/response ของ /evaluate ให้เข้ากับ canonical schema
5. รัน pipeline จริงกับ dataset และบันทึก model/prompt/STIX/dataset versions รวม provider/fallback mode
6. ใช้ false positives/negatives ที่พบพัฒนา semantic grounding/negation/ambiguity และ confidence
7. ปิด KB lifecycle, timeout/concurrency, privacy/logging และ deployment controls ตาม target ก่อนรับข้อมูลจริง

## งานที่ต้องตัดสินใจก่อนแก้ contract

- จำนวน candidates ปัจจุบันเกินเป้าหมาย: ลดด้วย subset policy หรือขอปรับข้อกำหนด
- metadata เพิ่มแบบ sidecar หรือแก้ schema ด้วยข้อตกลงร่วม; คง tactic: str จนกว่าจะตกลงใหม่
- Grounding Judge คืน review flag ปัจจุบัน; แยกการ reject/drop predictions กับ semantic review ให้ชัด
- CORS ไม่ใช่ authentication; เลือก auth/rate limit/retention และ acceptance tests สำหรับการ deploy

## เกณฑ์รับมอบ

Tests ผ่านเพียงอย่างเดียวไม่ใช่ quality gate ต้องมี Exact F1 ≥70%, parent recall ≥90%, hallucinated ID = 0, evidence grounding ≥85% และรายงาน false-positive rate ตาม spec ผลยังไม่มีใน mai-work

ตรวจทุกครั้งด้วย ingestion ก่อนเปิด API บนเครื่องใหม่, pytest โดย key ทั้งสองว่าง, git diff --check และ git status --short ใช้ [handoff](HANDOFF_TH.md) เป็น checklist ส่งงาน
