# ดัชนีเอกสาร Security-Alert

อัปเดต 17 กันยายน 2026

## เริ่มอ่านจากตรงนี้

1. [ข้อกำหนดหลัก](../security-alert-attack-technique-inference.md) — Source of Truth
2. [ภาพรวมสถาปัตยกรรม](architecture.md) — components, modes และ trust boundaries
3. [ลำดับการทำงานตามไฟล์โค้ด](SYSTEM_FLOW_CODE_GUIDE_TH.md) — end-to-end code walkthrough
4. [API contract](API_OVERVIEW_TH.md) — endpoints, schemas, headers, errors
5. [การรันและ Privacy](DEPLOYMENT_PRIVACY_TH.md) — environment, consent, retention

## สถานะและผลประเมิน

- [สถานะงานล่าสุด](WORK_PLAN_TH.md)
- [สรุป implementation](PROJECT_COMPLETION_IMPLEMENTATION_TH.md)
- [สรุปภาษาง่าย](สิ่งที่ทำไปแล้ว_TH.md)
- [ผลเปรียบเทียบโมเดล](MODEL_EVALUATION_RESULTS_TH.md)
- [Decision record ที่ยังรออนุมัติ](PROJECT_COMPLETION_DECISIONS_TH.md)
- [แผนปิดโครงการ](PROJECT_COMPLETION_PLAN_TH.md) — เก็บเป็นแผน/เกณฑ์ ไม่ใช่สถานะ runtime ล่าสุด

## การนำเสนอและ UI

- [บทนำเสนอ 10 นาทีสำหรับ 4 คน](PRESENTATION_SCRIPT_4_PEOPLE_TH.md)
- [สคริปต์เดโม 3 นาที](DEMO_SCRIPT_3_MIN_TH.md)
- [UI reference](UI_REFERENCE_TH.md)

## หลักฐานที่เครื่องสร้าง

ไฟล์ใน `docs/reports/` เป็น artifacts จาก tests/evaluation/acceptance ไม่ควรแก้ตัวเลขด้วยมือเพื่อให้ผ่านเกณฑ์ รายงานหลักคือ:

- `runtime-final.json` — Offline full gold-set metrics
- `tests.xml` — 199 tests ล่าสุด
- `browser-acceptance.json` — Chromium/UI acceptance
- `clean-verification.json` — clean-copy verification
- `release-manifest.json` — hashes, test summary และ blockers
- `llm-gemini-full.json`, `llm-openrouter-full.json` — strict provider attempts ที่ incomplete เพราะ rate limit

## กติกาการตีความผล

- F1/parent recall 97.30%, grounding 100% และ hallucinated ID 0% เป็นผลของ Offline `behavior-rules-v3`
- Gemini/OpenRouter ยังไม่มี full-set metrics ที่ครบและห้ามนำคะแนน Offline ไปอ้างแทน
- `acceptance_ready=false` จนกว่า subset/gold labels และ independent review ได้รับอนุมัติ
