# UI ปัจจุบัน

อัปเดต 17 กันยายน 2026 UI หลักอยู่ที่ `ui/src/App.tsx`, build เป็น `ui/dist/` และ FastAPI ให้บริการที่ `/ui`

## Analyst Workspace

- รับ Alert แบบข้อความและ optional alert ID ตาม PRD
- เลือก `Offline / Rules`, `Gemini 3.5 Flash-Lite` หรือ `OpenRouter`
- แสดง Technique 0–3 รายการ, tactic, support score, evidence spans และ MITRE URL
- แสดง `needs_human_review`, disclaimer และ MITRE ATT&CK Enterprise 19.1 attribution
- เปิด candidate drawer เพื่อดู top-5 ที่ Retriever พิจารณา
- แสดงสถานะ Parser/Router/Inferencer/Judge, provider/model, fallback reason และ confidence source จาก response headers
- ไม่ส่ง API key จาก browser; key อยู่ฝั่ง serverเท่านั้น

## Evaluation dashboard

เรียก `/evaluate` ใน `runtime` mode ซึ่งปิด provider และใช้ bundled synthetic gold set 35 alerts แสดง Exact F1, Parent Recall, Grounding และ Hallucinated ID พร้อมตาราง Exact/Parent/Miss

คะแนน 97.30% เป็นผล Offline `behavior-rules-v3` ไม่ใช่ Gemini/OpenRouter ดู [MODEL_EVALUATION_RESULTS_TH.md](MODEL_EVALUATION_RESULTS_TH.md)

## Guardrails ที่มองเห็นได้

- no-match ไม่ถูกนำเสนอว่าเป็นการรับรองว่า benign
- score แยก `RULE SUPPORT SCORE` กับ `LLM SUPPORT SCORE` และระบุว่าไม่ใช่ calibrated probability
- prompt-injection probe ต้องไม่สร้าง T9999 และต้องส่ง review
- ปุ่ม Clear ล้าง state; UI ไม่ใช้ localStorage/sessionStorage
- online provider failure แสดง fallback reason โดยไม่แสดง raw exception/secret

## การ build และทดสอบ

```bash
npm run build --prefix ui
PLAYWRIGHT_BROWSERS_PATH=/tmp/security-alert-browsers \
  .venv/bin/python scripts/browser_acceptance.py \
  --output docs/reports/browser-acceptance.json
```

Browser acceptance ล่าสุดผ่าน mode selector, inference/evidence, candidates, benign no-match, provider-safe fallback, LLM score rendering, evaluation dashboard, disclaimer, no browser storage และ theme screenshots

UI นี้เป็น dashboard สำหรับ alert text ตาม PRD จึงไม่จำเป็นต้องทำ upload/chat เพิ่ม เว้นแต่ข้อกำหนดเปลี่ยน
