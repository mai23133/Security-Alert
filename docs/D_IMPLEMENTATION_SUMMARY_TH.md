# สรุปสาย D หลังรวมเข้า mai-work

อัปเดต 7 กันยายน 2026: PR #4 merge เป็น f567aa3 แล้ว รวม CI fix ec73b10; feature-d-integration เป็นชื่อ branch ในประวัติ ไม่ใช่ฐานที่ต้องใช้พัฒนาต่อ

## เครดิตและประวัติ

งาน D เดิมของ thitareesangrasamepen-cyber อยู่ที่ feature-branch commit c35c1562133776c8f35acc5c773d485a9e0509ac ถูก merge เป็น parent ของ 5718f2a เพื่อรักษาที่มางาน UI/layout/analyst workflow และแนวคิด product-shell tests ถูกนำมาปรับใช้ร่วมกับ A+B

## งานที่ส่งมอบ

| ส่วน | ผลลัพธ์ใน mai-work |
| --- | --- |
| Single API | เชื่อม run_inference และ schema ATTACKInferenceResult |
| Batch | /alerts/infer/batch 1–25 รายการ รักษาลำดับและ no-match/review เมื่อ item ล้ม |
| RAG | /rag/search เรียก BM25 พร้อม narrative/tactic/top_k validation |
| Tracing | validated/generated request ID และ MITRE version header |
| Errors | safe detail.code/message สำหรับ exceptions ที่ route จับได้ |
| Gemini wrapper | สร้าง client เมื่อเรียก; timeout 10,000 ms และ 3 attempts |
| UI | /ui แสดง prediction/evidence/candidates/review/disclaimer ใช้ textContent และ local CSS |
| CORS | จำกัด local origins ปรับผ่าน environment |
| CI | install → ingestion → offline pytest → whitespace check |

CI fix ec73b10 เพิ่ม python -m src.rag.ingest_stix ก่อน pytest เพราะ generated KB ไม่อยู่ใน clean checkout ผลตรวจล่าสุดในรอบ review: 62 passed ทั้ง workspace และ clean copy ที่ ingestion ใหม่ ไม่ได้ตรวจ run GitHub ล่าสุดในรอบนี้

## สิ่งที่ปรับจาก D เดิม

ใช้ canonical schema แทน prediction/confidence/candidates รูปแบบเก่า, เปลี่ยน fake runtime เป็น A+B pipeline, แก้ batch path และ tests, คง BM25/pinned ingestion แทน Chroma/Gemini embedding/duplicate agents อ่าน [บันทึก review D](D_INTEGRATION_REVIEW_TH.md) สำหรับสรุปประเด็นที่ปิดแล้ว

## ข้อจำกัดที่ยังเหลือ

D เป็น product shell ระดับ local ไม่ใช่การรับรองพร้อม production: ไม่มี total deadline/async worker, KB missing ตอน import ยังทำให้ startup ล้ม, traceback logging ยังต้อง redaction, ไม่มี auth/rate limit/retention enforcement UI มีเฉพาะ single inference ไม่ใช่หน้าจอ batch/evaluation

Parser/router จับ provider failure แล้ว fallback ดังนั้น timeout/retry ไม่ได้แปลว่า API คืน 504 เสมอ ดู [API contract](API_OVERVIEW_TH.md)

## จุดส่งต่อ C

D merge แล้ว ให้ C ใช้ mai-work ล่าสุด ตรวจ [C checklist](C_EVALUATION_REVIEW_TH.md) ก่อนนำ dataset/metrics/runner/tests มาเชื่อม /evaluate โดยคง API/schema/UI และ CI ingestion อ่าน [รายงานรวม](PROJECT_REVIEW_TH.md) สำหรับ subset/semantic/evaluation gaps
