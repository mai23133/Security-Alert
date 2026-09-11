# ส่งต่องานหลังรวม A+B+C+D

อัปเดต 7 กันยายน 2026: mai-work รวม C 5d56d31 บนฐาน e2ee2da ที่ commit 6b3a38c และแก้ evaluation integration แล้ว อ่าน [สรุปงาน C](C_IMPLEMENTATION_SUMMARY_TH.md) ก่อน

## เตรียมระบบ

~~~bash
python -m pip install -r requirements.txt
python -m src.rag.ingest_stix
GOOGLE_API_KEY='' GEMINI_API_KEY='' python -m pytest -q
python -m eval.run_eval --mode fixture
python -m eval.run_eval --mode runtime
git diff --check
git status --short
~~~

ใช้ Python 3.11 ที่ activate แล้ว processed files ยัง ignore และต้องสร้างก่อน import API tests ใหม่ที่ใช้ TestClient อาจต้องรันนอก sandbox ที่จำกัด thread/event-loop wakeup; ห้ามปิด tests เพื่อให้ผ่าน

## Contract ส่งต่อ

Canonical ATTACKInferenceResult ไม่เปลี่ยน; runtime adapter เปลี่ยนชื่อ candidates_considered เฉพาะจุดส่งเข้า metric ไม่ให้ predictions ทับ gold fields

/evaluate รับ mode/runtime-or-fixture และ top_k เท่านั้น ไม่รับ filesystem paths ข้อมูลประเมินเป็น bundled synthetic dataset และ provider disabled เสมอ CLI --require-quality-gates ใช้กับ runtime เพื่อคืน nonzero เมื่อไม่ผ่านตัวเลข

## งานรับรองคงเหลือ

Dataset ยัง RC pending label review; composition/parent weight/subset ต้องยืนยันกับผู้สอน ผล F1/parent recall ยังไม่ผ่าน Semantic grounding และ operational controls ยังต้องแก้ต่อ ไม่มีการรับรองว่าโครงการทั้งหมดเสร็จ 100%

[รายงานโครงการ](PROJECT_REVIEW_TH.md), [API contract](API_OVERVIEW_TH.md) และ [แผนผังไฟล์](PROJECT_FILE_MAP_TH.md) อธิบายรายละเอียดปัจจุบัน
