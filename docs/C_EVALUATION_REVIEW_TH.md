# สถานะ review C หลังแก้ integration

อัปเดต 7 กันยายน 2026: รวม yean-work 5d56d31 เข้า mai-work จากฐาน e2ee2da ที่ commit 6b3a38c รายละเอียดผลส่งมอบอยู่ใน [C_IMPLEMENTATION_SUMMARY_TH.md](C_IMPLEMENTATION_SUMMARY_TH.md)

## ปิดแล้ว

- Parent match ให้ partial credit 0.5 จากงาน C เดิม
- Dataset/prediction IDs, categories, evidence และ flags validation จาก C เดิม
- แก้ prediction เขียนทับ gold fields ทั้ง validation และ build_records
- เพิ่ม nonempty bounded narrative validation
- Default allowlist ผูก generated file และตรวจ snapshot เท่ากัน
- แยก fixture validation กับ runtime quality errors ให้ metric วัดความผิดพลาดได้จริง
- เพิ่ม offline runtime adapter จาก canonical schema
- เพิ่ม /evaluate ที่รับเฉพาะ bundled dataset mode/top_k
- เพิ่ม tests สำหรับ regressions, network isolation และ CLI/API errors
- แก้ conflict เอกสารโดยรักษาสถานะ A+B+D

## ยังต้องรับรองก่อนประกาศผ่านโครงการ

Gold labels/จำนวนชุดข้อมูล/parent credit และ subset ยังต้องให้ทีม/ผู้สอนยืนยัน ไม่ล็อก dataset จาก RC ด้วยการคาดเดา Runtime F1 34.55%, parent recall 52.70% ยังไม่ผ่าน gates และ substring grounding 100% ยังไม่ใช่ semantic grounding

ดู [แผนงาน](WORK_PLAN_TH.md) สำหรับงานถัดไปและ [API](API_OVERVIEW_TH.md) สำหรับ contract
