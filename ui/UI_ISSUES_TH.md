# รายงานการแก้ไข UI — 15 กันยายน 2026

อ้างอิงข้อกำหนดหลักหัวข้อ 8 (API Contract), 10 (Security & Guardrails) และ 11 (UI สัปดาห์ที่ 6)

## ปัญหาที่แก้แล้ว

1. **เปิด dev server และ build ไม่ได้**: `vite.config.ts` import `.figma/make/site.json` ที่ไม่มีอยู่ ทำให้เกิด TS2307 และ UNRESOLVED_IMPORT เปลี่ยนเป็น `site.config.json` ที่อยู่ในโปรเจกต์ พร้อมชื่อหน้า ภาษา และคำอธิบาย
2. **หน้าขาวเมื่อเปิด `/ui` ผ่าน FastAPI**: API เดิมส่ง HTML ที่อ้าง `/src/main.tsx` โดยไม่มีตัวแปลง TSX หรือเส้นทางให้บริการไฟล์ เปลี่ยนเป็นส่ง `ui/dist/index.html`, ให้บริการไฟล์ `/ui/assets` และตั้ง Vite base เป็น `/ui/`
3. **ไม่มีหน้าใช้งานเมื่อยังไม่ได้ build**: เก็บหน้า HTML เดิมจาก Git HEAD เป็น `fallback.html` ซึ่งเชื่อม API เดิมอยู่แล้ว และใช้เมื่อไม่มี bundle
4. **สี badge ไม่แสดง**: การต่อ `18` หลัง `var(--red)` หรือ `var(--green)` ไม่ใช่ CSS color ที่ถูกต้อง เปลี่ยนเป็น `color-mix()` ในรายการ entity และ match badge
5. **build ไม่ตรวจชนิดข้อมูล**: เพิ่ม `typecheck` และให้คำสั่ง build ตรวจ TypeScript ก่อนสร้าง bundle
6. **ข้อมูลตัวอย่างดูเหมือนผลจริง**: เพิ่มข้อความแจ้งตลอดทั้งหน้า React ว่า prediction, evaluation และ guardrail status เป็นข้อมูลตัวอย่าง ต้องให้ผู้เชี่ยวชาญตรวจสอบ
7. เพิ่ม ignore สำหรับ dependencies, pnpm store และไฟล์ build เพื่อไม่ให้ติดเข้า Git

## ปัญหาที่ยังเหลือและข้อขัดแย้งกับข้อกำหนด

- `App.tsx` ยังใช้ `INFERENCE_RESULTS`, `EVAL_ROWS` และคะแนน/สถานะ guardrail แบบกำหนดไว้ตายตัว ปุ่มใช้ timer ไม่ได้เรียก `/alerts/infer` หรือ `/evaluate`
- ข้อความที่พิมพ์เองได้ผลตัวอย่างชุดแรก และการแก้ข้อความหลังเลือก sample ยังได้ผล sample เดิม จึงยังใช้วิเคราะห์ Alert จริงไม่ได้
- ตัวอย่างมี tactic นอก Initial Access, Execution และ Credential Access เช่น Lateral Movement และมี evidence ที่ย่อด้วย `...` ซึ่งไม่ใช่ช่วงข้อความต้นฉบับครบถ้วน
- ค่าบน dashboard ไม่ได้มาจาก evaluation runner จึงใช้ยืนยัน quality gates หรือผล security testing ไม่ได้

ทางเลือกถัดไป: เชื่อมหน้า React กับ API จริงตาม schema ในข้อกำหนด และแทนที่ข้อมูลจำลองทั้งหมดด้วยผลจาก backend หรือคงหน้านี้เป็น UI preview ที่ระบุสถานะชัดเจน การแก้ครั้งนี้เลือกติดป้าย preview และรายงานข้อขัดแย้ง ไม่เปลี่ยน taxonomy, gold labels หรือเดาวิธีคำนวณผลแทน backend

## ผลตรวจสอบ

- `npm run build`: ผ่าน รวม TypeScript และ Vite production build
- Python ใน `.venv` รัน `-m pytest -q`: **105 passed**
- ตรวจ `/ui` และ JavaScript/CSS ที่หน้าอ้างผ่าน ASGI HTTP client: HTTP 200 ทั้งหมด พร้อม content type ถูกต้อง
- `git diff --check`: ผ่าน มีเพียงคำเตือนการแปลง LF/CRLF ของ Git บน Windows
- ตรวจ `git status --short` แล้ว รักษาไฟล์ UI ที่ผู้ใช้แก้ค้างไว้
- ทดสอบ HTML ไฟล์เดียวผ่าน Edge แบบ offline: เปิดไฟล์โดยตรง เลือก sample แสดงผลตัวอย่าง และสลับแท็บได้ ไม่มี browser error หรือ HTTP request
- ยังไม่ได้ทดสอบ React เชื่อม inference/evaluation จริงแบบครบวงจร เพราะยังใช้ข้อมูลจำลอง

## วิธีใช้งาน

**เปิดหน้า UI อย่างเดียว:** ดับเบิลคลิก `เปิดหน้า-UI.html` ได้ทันที ไม่ต้องติดตั้ง Node, pnpm หรือเปิด server ไฟล์นี้รวม JavaScript และ CSS แล้ว ใช้ฟอนต์ที่มีในเครื่อง และยังเป็นหน้า preview ข้อมูลจำลองตามป้ายแจ้งบนหน้า

ขั้นตอนด้านล่างสำหรับผู้พัฒนาที่แก้ source เท่านั้น คำสั่ง build จะสร้าง HTML ไฟล์เดียวข้างต้นให้ใหม่ด้วย

ในโฟลเดอร์ `ui` ให้รัน `pnpm install --frozen-lockfile` แล้ว `pnpm build` จากนั้นเปิด `/ui` บน FastAPI ที่รันอยู่ หากแก้ React ต้อง build ใหม่ก่อนรีเฟรชหน้า API

สำหรับพัฒนา UI รัน `pnpm dev` แล้วเปิด `http://localhost:8443/ui/` หากไม่กำหนด PORT เพิ่มเติม

หน้า React ที่ build แล้วยังคงเป็น preview ตามข้อจำกัดข้างต้น ส่วน fallback เดิมใช้เฉพาะกรณีไม่มีไฟล์ build
