# สคริปต์วิดีโอเดโม 3 นาที

อัปเดต 18 กันยายน 2026: ใช้ `Offline / Rules` เป็นเส้นทางหลักที่ผ่าน full gold-set evaluation ส่วน Gemini/OpenRouter เป็น experimental modes และไม่ใช้คะแนน 97.30% อ้างเป็นคะแนน LLM

อ้างอิงข้อกำหนดหลักหัวข้อ **12. แผนสาธิต 3 นาที** รวมถึง Agent Architecture, Evaluation Pack และ Security & Guardrails

> คำเตือนที่ควรคงไว้ตลอดเดโม: ผลลัพธ์ของระบบเป็นคำแนะนำสำหรับนักวิเคราะห์ ไม่ใช่การตอบสนองเหตุการณ์อัตโนมัติ

## ลำดับภาพและบทพูด

### 0:00–0:15 — เกริ่น

**ภาพ:** หน้าแรกของระบบ หรือหน้า `Infer Alert`

**พูด:**

> สวัสดีครับ/ค่ะ วิดีโอนี้สาธิตระบบ Security Alert Attack Technique Inference ระบบรับข้อความ Security Alert แล้วแนะนำ MITRE ATT&CK Technique ที่เกี่ยวข้อง พร้อมหลักฐานจากข้อความ เพื่อช่วยให้นักวิเคราะห์ตรวจสอบเหตุการณ์ได้รวดเร็วขึ้น ผลลัพธ์ทั้งหมดเป็นเพียงคำแนะนำและต้องให้ผู้เชี่ยวชาญตรวจสอบก่อนใช้งานจริง

### 0:15–0:55 — Alert: Brute Force และ PowerShell

**ภาพ:** วาง Alert แล้วกด Infer

```text
Host WIN-SRV-04 logged 847 failed RDP authentication attempts from IP
203.0.113.44 between 02:00–04:00 UTC, followed by a successful login
and execution of encoded PowerShell.
```

**พูด:**

> ตัวอย่างแรก เครื่อง WIN-SRV-04 มีการยืนยันตัวตนผ่าน RDP ล้มเหลว 847 ครั้งจาก IP เดียว ต่อมามีการล็อกอินสำเร็จและรัน encoded PowerShell ระบบแนะนำสอง Technique คือ `T1110 – Brute Force` และ `T1059.001 – PowerShell`

**ภาพ:** ซูมผลลัพธ์ Technique, confidence และ evidence spans

**พูด:**

> จุดสำคัญคือระบบแสดงหลักฐานที่ตรวจสอบย้อนกลับได้ โดย `847 failed RDP authentication attempts` สนับสนุน Brute Force และ `execution of encoded PowerShell` สนับสนุน PowerShell เราจึงไม่ต้องเชื่อผลลัพธ์เพียงเพราะระบบระบุ ID มาให้

### 0:55–1:20 — RAG candidates ก่อน inference

**ภาพ:** เปิดหน้า RAG Search หรือ candidate list และแสดง top-5

**พูด:**

> ก่อน inference ระบบจะค้นหา candidate จากฐานความรู้ MITRE ATT&CK Enterprise STIX 2.1 เวอร์ชันที่ตรึงไว้ คือ `enterprise-attack-19.1` หน้านี้แสดง top-5 candidates พร้อมชื่อ Technique, tactic และคำอธิบายย่อ

> Retrieval ยังไม่ใช่คำตัดสินว่าเหตุการณ์เกิดขึ้นจริง แต่เป็นการจำกัดรายการที่ Inferencer จะพิจารณา และระบบจะไม่เลือก Technique ที่อยู่นอก candidate หรืออยู่นอก pinned subset

### 1:20–1:45 — Benign patch management

**ภาพ:** เปลี่ยนข้อความ Alert แล้วกด Infer

```text
The IT operations team installed approved monthly security patches during
the scheduled maintenance window. No suspicious authentication activity
or command execution was observed.
```

**พูด:**

> ต่อไปเป็นกิจกรรมปกติ: ทีม IT ติดตั้ง security patches ตามช่วงเวลาบำรุงรักษาที่ได้รับอนุมัติ และไม่มีพฤติกรรมยืนยันตัวตนหรือการรันคำสั่งที่น่าสงสัย ในกรณีนี้ระบบควรไม่คืน Technique หรือคืนผลที่ confidence ต่ำ พร้อมเปิดสถานะ `needs_human_review`

> การไม่ระบุ Technique ไม่ได้แปลว่าระบบรับรองว่าเหตุการณ์ปลอดภัย แต่ช่วยหลีกเลี่ยงการติดป้ายพฤติกรรมโจมตีให้กับงานดูแลระบบปกติ

### 1:45–2:20 — Grounding Judge

**ภาพ:** กลับไป Alert แรก ลบข้อความ `failed RDP authentication attempts` หรือ `execution of encoded PowerShell` แล้วรัน/ตรวจ Judge อีกครั้ง

**พูด:**

> ตอนนี้เราลบช่วงข้อความที่เป็นหลักฐานออกจาก Alert แล้วส่งผลให้ Grounding Judge ตรวจซ้ำ เมื่อไม่มี evidence span ที่รองรับ ระบบจะปฏิเสธ Technique ที่เกี่ยวข้อง หรือส่งผลให้มนุษย์ตรวจแทน

> ขั้นตอนนี้ป้องกันไม่ให้ระบบอ้าง Technique โดยไม่มีข้อความจริงรองรับ และช่วยลดความเสี่ยงจากคำตอบที่สร้างขึ้นเอง

### 2:20–2:50 — Evaluation dashboard

**ภาพ:** เปิดหน้า Evaluation dashboard หรือรายงานการประเมิน

**พูด:**

> ส่วนสุดท้ายคือการวัดคุณภาพของระบบ เราแสดง Exact Technique F1 ซึ่งวัดความตรงของ Technique IDs ที่ทำนาย, Parent Technique Recall ซึ่งให้เครดิตบางส่วนเมื่อพบ Technique หลักแต่พลาด sub-technique, และ Hallucinated ID Rate ซึ่งต้องเป็นศูนย์

> นอกจากนี้ควรตรวจ Evidence Grounding Rate และ False-positive Rate สำหรับ benign controls ร่วมด้วย เกณฑ์สาธิตในข้อกำหนดคือ F1 อย่างน้อย 70 เปอร์เซ็นต์, parent recall อย่างน้อย 90 เปอร์เซ็นต์, evidence grounding อย่างน้อย 85 เปอร์เซ็นต์ และ hallucinated ID เท่ากับศูนย์

### 2:50–3:00 — สรุป

**ภาพ:** กลับไปหน้าผลลัพธ์แรก

**พูด:**

> สรุป ระบบช่วยเชื่อม Security Alert กับ MITRE ATT&CK ด้วยผลลัพธ์ที่มีหลักฐาน ตรวจสอบ candidate ได้ และส่งกรณีไม่แน่ใจให้มนุษย์พิจารณา ขอบคุณครับ/ค่ะ

## Checklist ก่อนอัดคลิป

- เตรียม Alert ทั้ง 2 ข้อความไว้สำหรับคัดลอกวาง
- เตรียมหน้าจอ RAG top-5 และ Evaluation dashboard ให้เปิดได้ทันที
- ตรวจว่าแสดง MITRE attribution และ STIX version ใน metadata ตามระบบ
- เดโมเฉพาะข้อมูลจำลองภายใน course sandbox และไม่แสดงข้อมูล Alert จริง
- ซ้อมจับเวลาให้จบภายใน 3 นาที
