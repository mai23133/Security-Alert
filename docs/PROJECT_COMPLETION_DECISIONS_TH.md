# Decision record สำหรับปิดโครงการ

วันที่จัดทำ: 14 กันยายน 2026

สถานะ: รอผู้สอน/เจ้าของหลักสูตรยืนยันขั้น 0; ยังไม่ใช่การอนุมัติหรือการรับมอบ
ผู้อนุมัติและวันที่อนุมัติ: ยังไม่ได้รับข้อมูล

อ้างอิง [ข้อกำหนดหลัก](../security-alert-attack-technique-inference.md) หัวข้อ 3, 4, 7, 9, 10 และ [แผนปิดโครงการ](PROJECT_COMPLETION_PLAN_TH.md) ขั้น 0–1
นำแผนมาจาก commit `243fe93d4679a3581ca8261423ff1e77cfa58273` บน main เพื่อดำเนินงานบน mai-work

## ประเด็นที่ต้องยืนยัน

| ประเด็น | หลักฐานปัจจุบัน | ข้อเสนอสำหรับพิจารณา | สถานะ |
| --- | --- | --- | --- |
| Technique subset | แผนระบุ implementation 127 IDs แต่ข้อกำหนดหัวข้อ 3 ตั้งเป้า 30–50 | ให้ผู้สอนส่งรายชื่อ 30–50 IDs; หากต้องการคง 127 ต้องมีการอนุมัติและปรับข้อกำหนดให้สอดคล้องก่อน | รอรายชื่อ/การตัดสินใจ |
| Dataset composition | data/eval/README.md ระบุ 20 positive + 5 multi-technique + 5 ambiguous + 5 negative รวม 35 | คงโครงสร้าง 35 รายการนี้หากผู้สอนยืนยันว่า 10 ambiguous/multi และ 5 negative นับรวมแล้ว | รอยืนยันการตีความ |
| Gold labels | metadata เป็น 1.0.0-rc1, pending_independent_review และไม่มี reviewer | ผู้ตรวจคนที่สองตรวจทุก narrative/ID แล้วบันทึกชื่อ วันที่ และผลตรวจ พร้อมหลักฐานผู้สอนยืนยัน | รอการตรวจจริง |
| Parent credit | eval/metrics.py ให้ exact 1.0 และ parent-only 0.5 | คง 0.5 เพื่อเทียบผลเดิมได้ โดยรอผู้สอนยืนยัน | รออนุมัติ |
| Target environment | ยังไม่มี deployment decision สำหรับแผนนี้ | local course sandbox และปิด provider ระหว่าง evaluation; การส่ง alert ไป provider ต้องมี privacy/consent policy ที่อนุมัติ | รอยืนยัน |
| False-positive gate | ข้อกำหนดให้รายงาน FPR แต่ไม่ระบุ threshold | ให้ผู้สอนกำหนด threshold บน negative controls ก่อนรับมอบ | รอค่าเกณฑ์ |

## หลักฐานที่ต้องได้รับก่อนล็อกข้อมูล

1. รายชื่อ subset ที่อนุมัติ พร้อมชื่อผู้อนุมัติ วันที่ และแหล่งอ้างอิงการอนุมัติ
2. คำยืนยันจำนวนและองค์ประกอบ dataset, parent credit และ target environment
3. ผลตรวจครบทุก alert_id โดยผู้ตรวจคนที่สอง พร้อมชื่อ/วันที่ และการยืนยันจากผู้สอน
4. เกณฑ์ false-positive rate สำหรับใช้ตรวจรับ

เมื่อได้รับข้อมูลแล้วจึงสร้าง tracked approved subset manifest, ตรวจให้ generated allowlist และ evaluation snapshot ตรงกันทุก ID และอัปเดต dataset version/review metadata ตามผลตรวจจริง
ต้องอัปเดต data/eval/README.md, WORK_PLAN_TH.md และ API_OVERVIEW_TH.md ให้สอดคล้องกัน ก่อนสร้าง baseline สำหรับการปรับระบบ

## ขอบเขตงานที่ดำเนินการแล้ว

ผู้ใช้สั่งให้ดำเนินงานทั้งหมดและทำต่อจากส่วนที่เหลือ จึงดำเนินส่วนวิศวกรรมและทดสอบใน local sandbox ต่อแล้ว โดยยังใช้ subset/dataset เดิมสำหรับเทียบผล
คำสั่งนี้ไม่ใช่หลักฐานการตรวจ gold labels โดยผู้สอน จึงยังคงสถานะ pending ตามข้อเท็จจริง
มี ingestion ที่รับ approved manifest, review checklist ครบ 35 records และนโยบาย sandbox พร้อมตรวจได้แล้ว ดู [สรุป implementation](PROJECT_COMPLETION_IMPLEMENTATION_TH.md)

- อ่านข้อกำหนดหลักและแผนปิดโครงการครบ
- นำไฟล์แผนจาก main มาไว้ในสาขาปัจจุบัน โดยไม่ได้ merge การเปลี่ยนแปลงอื่น
- เตรียม decision record และข้อเสนอให้ผู้รับผิดชอบตรวจ

ขั้น 0 ยังไม่ผ่าน และยังไม่ได้ล็อก subset/dataset หรือประกาศผ่าน runtime quality gates
ผลใหม่อยู่ใน docs/reports/runtime-final.json; ตัวเลข baseline ที่ปรากฏในเนื้อหาแผนเดิมเก็บไว้เพื่อเปรียบเทียบ
