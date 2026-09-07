# บันทึกปิด review สาย D เดิม

อัปเดต 7 กันยายน 2026 เอกสารนี้เป็นประวัติ ไม่ใช่รายการสั่งให้รวม D อีกครั้ง

ตรวจเดิมที่ feature-branch c35c156 ของ thitareesangrasamepen-cyber; ผลการปรับรวมอยู่ใน 5718f2a และ merge PR #4 เข้า mai-work ที่ f567aa3 พร้อม CI fix ec73b10

| ประเด็น review เดิม | สถานะหลังรวม |
| --- | --- |
| API schema คนละรูปแบบ | ใช้ ATTACKInferenceResult กลางแล้ว |
| Fake inference ทับ A+B | เรียก run_inference จริง |
| Batch path/test ไม่ตรง | ใช้ /alerts/infer/batch |
| ขาด RAG inspection | เพิ่ม /rag/search |
| UI binding ไม่ตรง | ปรับเป็น inferred_techniques/candidates_considered |
| Duplicate agents/STIX/Chroma | คง A+B BM25 และ ingestion เดิม |
| CI ไม่มี KB ใน clean checkout | เพิ่ม ingestion ก่อน pytest |
| เครดิตผู้ทำ D | เก็บ commit เดิมเป็น ancestor และปรับ UI/layout ต่อจากงานเดิม |

ย่อขั้นตอนสร้าง branch, checklist เปิด PR และ error-model ข้อเสนอเดิมออกจากเอกสารใช้งาน เพราะงานดังกล่าวเสร็จแล้วและบางข้อเสนอไม่ใช่ contract ที่เลือกจริง เนื้อหาเดิมเรียกดูจาก Git history ก่อนการอัปเดตรอบนี้ได้

งานที่ยังเหลือให้ดู [รายงานล่าสุด](PROJECT_REVIEW_TH.md); รายละเอียด D และเครดิตอยู่ใน [D_IMPLEMENTATION_SUMMARY_TH.md](D_IMPLEMENTATION_SUMMARY_TH.md) เกณฑ์ต่อไปคือรวม C และปิด quality/deployment gaps
