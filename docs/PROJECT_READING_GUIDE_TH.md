# คู่มือเอกสาร

อัปเดต 7 กันยายน 2026: A+B+C+D บน feature-c-integration อ่าน [สรุป C](C_IMPLEMENTATION_SUMMARY_TH.md) ก่อน

## ลำดับอ่าน

| ลำดับ | เอกสาร | ใช้ตอบคำถาม |
| --- | --- | --- |
| 1 | [ข้อกำหนดหลัก](../security-alert-attack-technique-inference.md) | โครงการต้องทำอะไร ขอบเขต/schema/quality gates คืออะไร |
| 2 | [README](../README.md) | ติดตั้ง ingestion ทดสอบและเปิด UI อย่างไร |
| 3 | [PROJECT_REVIEW_TH](PROJECT_REVIEW_TH.md) | ตอนนี้ทำได้อะไร มีข้อจำกัดอะไร ผลตรวจพิสูจน์แค่ไหน |
| 4 | [PROJECT_FILE_MAP_TH](PROJECT_FILE_MAP_TH.md) | ทุกไฟล์ทำอะไร เชื่อมกันอย่างไร |
| 5 | [architecture](architecture.md) | เส้นทางข้อมูลและ provider boundaries |
| 6 | [API_OVERVIEW_TH](API_OVERVIEW_TH.md) | request/response/errors จริง |
| 7 | [WORK_PLAN_TH](WORK_PLAN_TH.md) | งานถัดไปตามลำดับ |
| 8 | [HANDOFF_TH](HANDOFF_TH.md) | checklist สำหรับคนรับงาน C |

## เอกสารเฉพาะสาย

- [TEAM_WORK_PARALLEL_PROPOSAL_TH](TEAM_WORK_PARALLEL_PROPOSAL_TH.md): เจ้าภาพ A/B/C/D และขอบเขตการแก้ไฟล์
- [C_EVALUATION_REVIEW_TH](C_EVALUATION_REVIEW_TH.md): สถานะปิดประเด็น review C และข้อจำกัดคงเหลือ
- [D_IMPLEMENTATION_SUMMARY_TH](D_IMPLEMENTATION_SUMMARY_TH.md): งาน D ที่รวมแล้ว เครดิต และข้อจำกัด
- [D_INTEGRATION_REVIEW_TH](D_INTEGRATION_REVIEW_TH.md): บันทึกปิด review D เดิม ย่อแทนคู่มือ merge ที่หมดอายุ
- [A_B_PIPELINE_INTEGRATION_TH](A_B_PIPELINE_INTEGRATION_TH.md): contract ระหว่าง A/B กับ API
- [MAI_WORK_INFERENCE_GUARDRAILS_TH](MAI_WORK_INFERENCE_GUARDRAILS_TH.md): กฎ inference/evidence/judge และสิ่งที่ยังไม่รับประกัน

## การจัดเอกสารรอบนี้

ปรับสถานะเอกสารทั้งชุดเป็นฐาน mai-work, แทนรายงานเก่าด้วย findings ปัจจุบัน และย่อขั้นตอน D ที่ทำเสร็จแล้วเพื่อไม่ให้สั่ง merge ซ้ำ เก็บชื่อไฟล์เดิมเพื่อรักษาลิงก์และบริบททีม จึงไม่มีการลบไฟล์เอกสารในรอบนี้ เนื้อหาเก่าดูย้อนหลังใน Git ได้

AGENTS.md เป็นคำสั่งการทำงาน ส่วน specification เป็นข้อกำหนด ไม่ปรับ requirements ให้ตรงกับช่องว่างของ implementation ข้อขัดแย้งให้ดู PROJECT_REVIEW_TH และตกลงกับทีมก่อน
