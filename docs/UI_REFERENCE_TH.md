# UI ที่ปรับจากกิ่ง ui-test

อ้างอิง `ui/src/App.tsx` และ `ui/src/index.css` ของกิ่ง
[ui-test](https://github.com/mai23133/Security-Alert/tree/ui-test/ui)
นำรูปแบบ SOC workspace สองคอลัมน์ สี amber, sample picker, confidence bars,
candidate drawer, scorecards, ตารางกรองผล และ guardrail cards มาปรับใช้
ยังเปิดผ่าน `/ui` ได้โดยไม่ต้องติดตั้ง Node หรือ build frontend เพิ่ม

ธีมเริ่มต้นเป็นสว่าง และมีปุ่มสลับเป็นธีมมืดตามต้นฉบับ
ไม่เก็บการเลือกธีม, API key หรือ narrative ใน browser storage

## การใช้งานที่เชื่อมกับระบบจริง

- Analyst Workspace เรียก `/alerts/infer`, แสดง evidence และ review จาก API
- Candidate drawer แสดง candidates ที่ใช้จริงพร้อมลำดับและ tactic
- Full Evaluation เรียก `/evaluate` ด้วย `diagnostics: true` เพื่อแสดง 35 records
- กรอง All / Exact / Parent / Miss จากชุด gold/predicted IDs จริง; Exact ต้องตรงทั้งชุด
- Prompt injection ส่งข้อความจำลองที่ขอ T9999 และ system prompt ผ่าน inference
  PASS เฉพาะเมื่อไม่คืน prediction และตั้ง human review; ไม่อ้างว่าป้องกันทุก payload ได้
- Status ตรวจ `/ready` และรองรับ API key ที่กรอกใน workspace

กิ่งต้นฉบับมี evaluation rows, คะแนน, จำนวน injection tests และ calibration/leakage
metrics แบบ hard-coded จึงนำรูปแบบมาเชื่อมกับข้อมูลที่มีจริงแทน
Guardrail cards ด้าน scope/privacy อธิบาย policy ไม่ใช่ผล security audit
No-match ไม่ได้หมายความว่า alert ปลอดภัยแน่นอน และ confidence เป็นคะแนนตามกฎ

## API compatibility และข้อจำกัด

เพิ่ม optional boolean `diagnostics` ใน `/evaluate` ค่าเริ่มต้น false
request เดิมยังใช้ได้ diagnostics คืนเฉพาะ bundled synthetic dataset
โดยมี IDs และ evidence offsets/hash ไม่มี narrative หรือ evidence ดิบเพิ่ม
Schema ผล inference, pinned STIX 19.1 และขอบเขตสาม tactics คงเดิม
ไม่ย้าย mock IDs นอกขอบเขต, version สมมติ หรือ dependency ของ React/Tailwind เข้ามา

การตรวจ browser ครอบคลุมผล inference/evidence, benign, error, evaluation/filter,
injection probe, theme toggle และ mobile overflow ผ่าน `scripts/browser_acceptance.py`
