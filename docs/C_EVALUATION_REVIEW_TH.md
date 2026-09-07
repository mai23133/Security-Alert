# Checklist สาย C ก่อนรวมเข้า mai-work

อัปเดต 7 กันยายน 2026 หลัง D merge f567aa3; เอกสารนี้เป็นเกณฑ์ตรวจรับ ไม่ใช่ผล review branch C ล่าสุด

Review เดิมอ้าง origin/yean-work cf1bbbf ซึ่งเก่ากว่า remote-tracking ref ที่เคยพบ 5d56d31 รอบนี้ตรวจโครงการบน mai-work เท่านั้น จึงไม่ยืนยันว่าข้อแก้ใดเสร็จหรือยังค้างบน C ปัจจุบัน ต้องเทียบ diff และรัน tests จาก branch C ใหม่ก่อน merge

## สถานะในฐานรวม

eval/metrics.py, eval/run_eval.py และ src/api/routes/evaluate.py ว่าง ไม่มี tracked data/eval/; การรัน module runner ว่างแล้ว exit 0 ไม่ได้แปลว่า evaluation สำเร็จ

## 1. ยืนยัน dataset contract

Spec ระบุ 35 alerts, ambiguous/multi-technique 10 และ negative controls 5 แต่ไม่ชัดว่ารวมใน 35 หรือแยกเพิ่ม แผนเดิม C ใช้รวม 35 แบ่ง 20 positive/5 multi/5 ambiguous/5 negative ให้ยืนยันการนับกับผู้สอนก่อนล็อก ไม่ถือรายละเอียดแบ่งย่อยนี้เป็นข้อกำหนดใหม่

ตรวจ unique alert_id, category ที่ตกลง, nonempty narrative, gold IDs 1–3 ในกรณีโจมตีและ [] สำหรับ negative; IDs ต้องอยู่ pinned allowlist Labels ต้องผ่านการตรวจของผู้สอนและระบุ provenance/sanitization/version

## 2. Metrics ต้องวัดข้อผิดพลาดได้จริง

Exact multi-label F1, parent recall แบบ partial credit, evidence grounding, hallucinated IDs, false positives บน negative controls รวม top-k recall/human-review ตาม milestones

กำหนดน้ำหนัก parent match เช่น 0.5 เป็นข้อเสนอ ไม่ใช่ค่าที่ spec กำหนด พร้อมทดสอบ exact/parent/sibling/empty cases และ denominator ของทุก metric

ตรวจ duplicate/missing/extra prediction alert IDs แยก schema errors จาก quality errors: runtime prediction ที่มี hallucinated ID ต้องนับใน metric หรือรายงานผิด contract อย่างชัดเจน ไม่กรองทิ้งเงียบ ๆ จนได้ hallucinated-ID rate=0

## 3. ผูก taxonomy กับ pinned source

ใช้ processed technique_ids.json ที่สร้างจาก raw 19.1 เป็น default หรือถ้ามี snapshot ต้องตรวจ equality/hash/version หลัง ingestion ไม่สร้าง allowlist อีกชุดที่ล้าสมัย

## 4. แยก fixture report กับ runtime report

Saved predictions ที่สร้างให้ถูกใช้ทดสอบ metrics เท่านั้น ระบุ report_kind=fixture_validation และ not_a_runtime_quality_gate=true

Runtime report ต้องมาจาก run_inference/API จริง เก็บ commit, dataset/STIX/prompt/model versions, timestamp, provider/fallback mode และ parameters; ห้ามตีความ fixture 100% ว่าโมเดลผ่าน gates

## 5. รวมงานตามลำดับ

1. อัปเดต branch C จาก mai-work หลังรวม D และตรวจ conflicts รายไฟล์
2. ตรวจ data/metrics/runner/tests และรายงานก่อนรวม
3. กำหนด contract ของ /evaluate และวิธีเลือก dataset ที่ validate ได้ ไม่ยอมให้ client อ่าน path ใดก็ได้
4. คง single/batch/search/UI และ workflow ingestion พร้อม empty provider keys
5. รัน pytest และ runner ที่มี implementation จริง แล้วตรวจผล gates ตาม specification
6. ใช้เอกสารสถานะ mai-work เป็นฐาน เพิ่มรายละเอียด C ที่ยืนยันแล้วเท่านั้น

เกณฑ์ quality gates และ gaps รวมอยู่ใน [PROJECT_REVIEW_TH.md](PROJECT_REVIEW_TH.md); วิธีเตรียมระบบใน [README](../README.md)
