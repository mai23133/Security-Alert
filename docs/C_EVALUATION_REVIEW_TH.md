# รายการแก้ไขสาย C ก่อนรวมงาน

เอกสารนี้สรุปผล review branch `yean-work` ของสาย C (Dataset และ Evaluation) เพื่อใช้แก้ไขก่อน merge เข้า `mai-work`.

## สถานะโดยย่อ

งานสาย C มี foundation ที่ดีและรันแบบ offline ได้:

- Dataset synthetic/sanitized 35 alerts
- 5 multi-technique และ 5 ambiguous alerts รวม 10 กรณีพิเศษ
- 5 negative controls
- Metrics, evaluation runner, saved predictions และ report
- ไม่เรียก Gemini หรือ network

อย่างไรก็ตาม ยังมีรายการต่อไปนี้ที่ต้องแก้หรือยืนยันก่อน merge เพื่อให้ตรงกับ `security-alert-attack-technique-inference.md`.

## 1. แก้ Parent Technique Recall ให้เป็น partial credit

ข้อกำหนดระบุว่า เมื่อทำนาย parent ของ gold sub-technique ต้องได้ **คะแนนบางส่วน** ไม่ใช่คะแนนเต็ม

โค้ดปัจจุบันใน `eval/metrics.py` ให้คะแนนเต็ม เช่น:

```text
gold:      T1059.001
predicted: T1059
ผลปัจจุบัน: parent recall = 1.0
```

สิ่งที่ต้องทำ:

1. ทีมกำหนดน้ำหนัก partial credit ที่ใช้ร่วมกัน เช่น `0.5` หรือค่าอื่นที่ตกลง
2. เขียน constant และอธิบายสูตรใน docstring/README ของ evaluation
3. แก้ `parent_technique_recall()` ให้ exact match ได้ 1.0 และ parent match ได้เฉพาะน้ำหนัก partial credit
4. แก้ test ที่ปัจจุบันคาด `1.0` ให้ตรวจค่าน้ำหนักใหม่

## 2. เพิ่ม validation ความสมบูรณ์ของ dataset และ predictions

`validate_dataset()` ปัจจุบันตรวจจำนวนรวม, 10 กรณีพิเศษ, 5 negative และ gold IDs ใน allowlist แล้ว แต่ควรเพิ่มการตรวจดังนี้:

- `alert_id` ของ dataset ต้องไม่ซ้ำ
- `alert_id` ของ saved predictions ต้องไม่ซ้ำ และมีจำนวนเท่ากับ dataset
- category ต้องเป็นหนึ่งใน `positive`, `multi_technique`, `ambiguous`, `negative`
- ต้องมี 20 positive, 5 multi-technique, 5 ambiguous และ 5 negative
- negative control ต้องมี `gold_technique_ids=[]`
- positive/multi/ambiguous ต้องมี gold IDs 1–3 รายการ
- ทุก prediction/candidate ID ต้องตรวจรูปแบบและอยู่ใน allowlist เมื่อเป็นผล fixture ที่อ้างว่าใช้ pinned subset

ควรเพิ่ม test สำหรับทุกกรณีผิดรูปแบบข้างต้น เพื่อให้ runner fail เร็วและอธิบายสาเหตุได้ชัดเจน

## 3. ผูก evaluation allowlist กับ source of truth

ไฟล์ `data/eval/technique_ids-v19.1.json` ตรงกับ `data/processed/technique_ids.json` ในปัจจุบัน (127 IDs) แต่เป็น snapshot แยก จึงเสี่ยงล้าสมัยเมื่อ regenerate taxonomy

เลือกอย่างใดอย่างหนึ่ง:

1. ใช้ `data/processed/technique_ids.json` เป็น default allowlist ของ runner โดยตรง หรือ
2. เก็บ snapshot ต่อไป แต่เพิ่ม test ที่บังคับให้ snapshot เท่ากับ allowlist หลักทุก ID ก่อนรัน evaluation

ต้องคง `data/raw/enterprise-attack-19.1.json` และ processed allowlist เป็น taxonomy source of truth ตาม specification

## 4. แยก report สำหรับ fixture ออกจากผล pipeline จริง

`saved_predictions-v1.0.json` ตั้งใจเป็น fixture สำหรับทดสอบ metric และให้ผลสมบูรณ์ จึงทำให้ report ได้ F1/grounding 100%.

สิ่งนี้เหมาะกับการทดสอบ framework แต่ **ไม่ใช่ผลคุณภาพของ `/alerts/infer` จริง**. ให้เพิ่ม metadata หรือข้อความใน report/README เช่น:

```text
report_kind: fixture_validation
not_a_runtime_quality_gate: true
```

เมื่อ pipeline จริงพร้อมประเมิน ให้สร้าง report แยกที่ระบุ model, prompt, dataset และ STIX version ของ run นั้น

## 5. แก้ conflict เอกสารก่อน merge

`yean-work` แก้ `docs/TEAM_WORK_PARALLEL_PROPOSAL_TH.md` จากฐานเอกสารเก่า ซึ่ง conflict กับสถานะล่าสุดบน `mai-work`.

แนวทาง merge:

- ใช้ไฟล์จาก `mai-work` เป็นฐาน เพราะสะท้อน A+B ที่เชื่อมแล้ว
- นำเฉพาะรายละเอียดของ C เช่น dataset, metrics, runner และ acceptance criteria ที่ยังขาดเข้ามา
- ห้ามคืนสถานะ `/alerts/infer` ไปเป็น no-match stub หรือบอกว่า A/B ยังไม่เชื่อม

## ก่อนส่งให้ merge อีกครั้ง

รันจาก root ของ repository:

```bash
python -m pytest -q
python -m eval.run_eval
git diff --check
git status --short
```

และให้สมาชิกทีมคนที่สอง review gold labels ก่อนเปลี่ยน dataset จาก `1.0.0-rc1` เป็น version ที่ล็อกแล้ว
