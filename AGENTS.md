# Security-Alert Codex Instructions

## Mandatory specification

`security-alert-attack-technique-inference.md` เป็นเอกสารข้อกำหนดหลักและ Source of Truth ของโปรเจกต์นี้

ก่อนเริ่มวิเคราะห์ วางแผน แก้โค้ด สร้างไฟล์ เขียน Test หรือ Review งานใด ๆ ต้องอ่านไฟล์ `security-alert-attack-technique-inference.md` ทั้งไฟล์ก่อนเสมอ

ห้ามเริ่มแก้ไขไฟล์จนกว่าจะอ่านเอกสารดังกล่าวเรียบร้อย

ก่อนลงมือทำ ให้ระบุสั้น ๆ ว่างานครั้งนี้เกี่ยวข้องกับหัวข้อใดในเอกสาร เช่น:

- In Scope / Out of Scope
- Source of Truth
- Agent Architecture
- Data Schemas
- Knowledge Base
- API Contract
- Evaluation Pack
- Security & Guardrails
- Milestone Mapping
- Dataset

## During work

ใช้ข้อกำหนดใน `security-alert-attack-technique-inference.md` เป็นหลักตลอดการทำงาน

ก่อนตัดสินใจเกี่ยวกับ architecture, schema, API, MITRE ATT&CK, dataset, evaluation หรือ security ให้กลับไปอ่านหัวข้อที่เกี่ยวข้องในเอกสารอีกครั้ง

ห้ามสร้าง implementation ที่ขัดกับ In Scope, Out of Scope, schema, API contract, pinned STIX version หรือ security guardrails ที่ระบุไว้

หาก source code ปัจจุบันขัดกับเอกสาร ห้ามแก้โดยคาดเดา ให้รายงานความขัดแย้งและเสนอทางเลือกก่อน

หากไฟล์ข้อกำหนดไม่มีอยู่ อ่านไม่ได้ หรือเนื้อหาไม่ชัดเจน ให้หยุดและแจ้งผู้ใช้

## Before completion

ก่อนแจ้งว่างานเสร็จ ให้ตรวจอีกครั้งว่า:

1. Implementation ตรงกับหัวข้อที่เกี่ยวข้องในเอกสาร
2. ไม่มีงานนอกขอบเขตถูกเพิ่มโดยไม่จำเป็น
3. Schema และ API contract ยังเข้ากันได้
4. ไม่ละเมิด Security & Guardrails
5. Test ที่เกี่ยวข้องผ่าน

รันการตรวจสอบด้วย:

```bash
python -m pytest -q
git diff --check
git status --short
