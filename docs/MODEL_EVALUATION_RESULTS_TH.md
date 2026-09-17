# ผลประเมินโมเดลสำหรับการนำเสนอ

อัปเดต 18 กันยายน 2026 หลัง merge-fix เอกสารนี้เป็นแหล่งอ้างอิงหลักสำหรับหัวข้อ Model evaluation/results ในการนำเสนอ

อ้างอิงข้อกำหนดหลักหัวข้อ Evaluation Pack, Dataset และ Security & Guardrails

## ผลที่เปรียบเทียบได้

| ระบบ | ชุดข้อมูล | Exact F1 | Parent recall | Grounding | Hallucinated ID | สถานะ |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| Iteration 2 lexical baseline | Full gold set 35 alerts | 34.55% | 52.70% | 100% | 0% | ไม่ผ่าน F1/parent thresholds |
| Offline `behavior-rules-v3` | Full gold set 35 alerts | 97.30% | 97.30% | 100% | 0% | ผ่าน numeric PRD gates |
| Gemini `gemini-3.5-flash-lite` | Intended 35 alerts | N/A | N/A | N/A | N/A | Incomplete: rate-limited ที่ `eval-005` |
| OpenRouter `openrouter/free` | Intended 35 alerts | N/A | N/A | N/A | N/A | Incomplete: rate-limited ที่ `eval-001` |

ผล Offline ถูกสร้างใหม่หลัง merge-fix โดยผูกกับ `code_sha256` ใน
`docs/reports/runtime-final.json` และมี test evidence 207 tests,
failures/errors/skipped เท่ากับ 0 รายงานใช้ source hash เพื่อจับความล้าสมัยแม้ working tree ยังไม่ถูก commit

## วิธีตีความ

- ค่า 97.30% เป็นผลของ deterministic offline pipeline ไม่ใช่ผล Gemini/OpenRouter
- Strict LLM evaluation ไม่ยอมรับ fallback; เมื่อ provider ใช้งานไม่ครบทุก stage ระบบหยุด
  และไม่คำนวณ metrics จาก partial run
- Provider attempts ใช้เฉพาะ bundled synthetic dataset พร้อม explicit consent
- OpenRouter request ตั้ง `provider.data_collection=deny`
- Confidence ของ offline เป็น rule support score ส่วน online เป็น LLM self-assessed score;
  ทั้งสองแบบยังไม่ใช่ calibrated probability
- Gold labels และ provisional subset ยังรอการรับรองจากผู้สอน/ผู้ตรวจอิสระ

## หลักฐาน

- Offline full set: `docs/reports/runtime-final.json`
- Gemini attempt: `docs/reports/llm-gemini-full.json`
- OpenRouter attempt: `docs/reports/llm-openrouter-full.json`
- Tests: `docs/reports/tests.xml`
- Browser acceptance: `docs/reports/browser-acceptance.json`
- Clean-copy verification: `docs/reports/clean-verification.json`
- Release manifest: `docs/reports/release-manifest.json`
