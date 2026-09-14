# สรุปการดำเนินงานตาม PROJECT_COMPLETION_PLAN_TH

อัปเดต 14 กันยายน 2026 — ต่อจาก baseline commit `0be7a1092ed46d0d34d4b5df1de28ea33d39370f` บน `mai-work`

ดำเนินส่วน implementation, tests, evaluation และเอกสารตามแผนแล้วหลายส่วน แต่ **ยังไม่ครบ 100% ตาม Definition of Done**: parent recall ยังไม่ถึง 90%, subset/gold labels ยังไม่มีหลักฐานอนุมัติ และยังไม่ได้ตรวจ semantic grounding/calibration โดยผู้ตรวจอิสระ

เอกสารนี้อธิบายทั้งงานสะสมจากรอบก่อนและงานที่ทำต่อ โดยใช้ [ข้อกำหนดหลัก](../security-alert-attack-technique-inference.md) หัวข้อ Agent Architecture, Knowledge Base, API Contract, Evaluation, Security & Guardrails และ Milestone Mapping เป็นหลัก

## ผลก่อนและหลัง

ใช้ course pack เดิม 35 alerts, gold labels เดิม, parent partial credit 0.5 และ provisional subset เดิม 127 IDs ตลอดการเปรียบเทียบ

| Metric | Baseline | รอบก่อน behavior-v1 | ล่าสุด behavior-v2 | เกณฑ์รับมอบ |
| --- | ---: | ---: | ---: | --- |
| Exact precision | 26.03% | 100% | 93.10% | รายงาน |
| Exact recall | 51.35% | 64.86% | 72.97% | รายงาน |
| Exact F1 | 34.55% | 78.69% | 81.82% | ≥70% ผ่าน |
| Parent recall | 52.70% | 64.86% | 72.97% | ≥90% **ยังไม่ผ่าน** |
| Hallucinated ID rate | 0% | 0% | 0% | 0% ผ่าน |
| Verbatim grounding | 100% | 100% | 100% | ≥85% ผ่านตามนิยาม substring |
| Negative-control FPR | 40% | 0% | 0% | รอผู้สอนกำหนด threshold |
| Recall@1 | 37.84% | 70.27% | 72.97% | รายงาน |
| Recall@3 | 64.86% | 78.38% | 81.08% | รายงาน |
| Recall@5 | 72.97% | 86.49% | 86.49% | รายงาน |

behavior-evidence rate ล่าสุด 100% เป็นการตรวจความสอดคล้องกับกฎที่ระบบใช้เอง ไม่ใช่หลักฐานว่า semantic correctness จากผู้เชี่ยวชาญเป็น 100%
Negative controls มีเพียง 5 รายการ ผล FPR 0% จึงยังไม่ยืนยันผลกับข้อมูลจริงทั่วไป
Human-review rate ล่าสุด 34.29%, tactic accuracy 80%; diagnostics ยังพบ ambiguity ที่ไม่ได้ส่ง review 1 รายการ, extra prediction 2 รายการ, inference miss 5 รายการ และ retrieval miss 4 รายการ หมวด error นับซ้อนกันได้

หลักฐาน: [baseline](reports/runtime-before.json), [v1 checkpoint](reports/runtime-v1-checkpoint.json), [ผล runtime ล่าสุด](reports/runtime-final.json)

## สิ่งที่ทำเพิ่มในรอบต่อเนื่องล่าสุด

1. แก้การตรวจ negation ที่เคยตัด exploit เพราะมีคำว่า “without user interaction” แม้ข้อความยืนยันว่า exploit เกิดขึ้นจริง
2. แยกข้อความที่บอกว่า metadata ไม่ได้ถูกบันทึกออกจากการปฏิเสธ execution และเพิ่มการตรวจ ambiguity เพื่อส่ง review
3. เพิ่มรูปแบบพฤติกรรมด้าน authentication, remote services, removable media, interpreter และ spelling/actor variants เช่น e-mail/staff โดย evidence ยังเป็นข้อความต้นฉบับ
4. เพิ่ม development fixtures จาก 37 เป็น 47 records, เปลี่ยนเวอร์ชันเป็น development-2 และเพิ่ม regression tests
5. เพิ่ม release manifest collector สำหรับ hashes ของโค้ด/dependencies/STIX/dataset/prompts/UI/tests และตรวจว่ารายงาน runtime ไม่เก่ากว่าโค้ด
6. ทำไฟล์สรุปฉบับนี้และปรับ README, WORK_PLAN, decision record และแผนให้แสดงสถานะจริง

## สถานะเทียบแผนทุกขั้น

| ขั้น | สิ่งที่ดำเนินการแล้ว | ส่วนที่ยังไม่ผ่าน/เงื่อนไข |
| --- | --- | --- |
| 0 — Source of Truth | decision record, manifest template และ checklist ตรวจครบ 35 records | ผู้สอน/ผู้ตรวจคนที่สองต้องยืนยันจริง; dataset ยังเป็น RC |
| 1 — Baseline | เก็บผล baseline, ใช้ Python 3.11, lock dependencies, แยก development และตรวจในสำเนาสะอาด | dataset สำหรับรับมอบยังไม่ locked |
| 2 — Error analysis | per-alert errors, ranked IDs, gold/predicted IDs, evidence offsets/hash, stage traces, confidence bins | ต้องใช้ backlog ด้านล่างแก้ failures ที่ยังเหลือ |
| 3 — Retrieval | manifest filtering, metadata เต็ม, atomic snapshot, normalization, weighted query, deterministic BM25 + reranking | approval ของ subset และ recall บางพฤติกรรมยังไม่ครบ |
| 4 — Inference/grounding | candidate bounds, behavior checks, contextual evidence, benign/negation, ambiguity, confidence/review policy | semantic validation และ calibration อิสระยังไม่มี; ambiguity ยังพลาด 1 record |
| 5 — Quality gates | metrics, diagnostics, development gates, full runtime gate และ CI jobs | full parent-recall gate ยัง fail; ไม่ลด threshold |
| 6 — API/security | lifespan, verified snapshot, deadline/worker bounds, typed errors, auth/rate limit/CORS, privacy/logging, lock file | deployment policy ต้องได้รับการยืนยัน; distributed controls ยังอยู่นอก local sandbox |
| 7 — Acceptance/release | unit/integration/security tests, Chromium E2E, demo 5 ขั้น, clean-copy verifier, release artifacts | final release/deployment ยังรอ quality และ approval |

## รายละเอียด implementation สะสม

### Knowledge Base และ retrieval

`src/rag/ingest_stix.py` ตรวจ pinned STIX SHA-256, กรอง 3 tactics/Windows/Linux และตัด revoked/deprecated ก่อนสร้างข้อมูล
รองรับ `--manifest` ซึ่งต้องมี 30–50 unique IDs, STIX version และข้อมูล approval ที่ครบ; default ยังเป็น 127 IDs ที่ระบุ provisional เพื่อเปรียบเทียบผลเดิม

สร้าง sidecar metadata ที่เก็บ tactics ทุกตัว, platforms, full description, STIX object ID และ external references โดยไม่เพิ่ม field ใน canonical TechniqueCandidate
Runtime อ่าน `kb_snapshot.json` ไฟล์เดียวที่ publish ด้วย atomic replace; startup ตรวจ candidate และ metadata เทียบ raw STIX จริง
Server ถือ generation เดิมจน restart เพื่อให้ taxonomy และ inference ใช้ข้อมูลชุดเดียวกัน

Retriever ใช้ full-description BM25, aliases ของศัพท์ security และ behavior reranking หลังกรอง allowlist/tactics
Weighted query รับเฉพาะ actions/IOCs ที่เป็น substring ของ narrative เพื่อไม่ให้ annotation จาก provider เพิ่มคำที่ไม่อยู่ใน input ค่า top-k เริ่มต้นยังเป็น 5; development Recall@3/5 ผ่าน แต่ course Recall@5 ยังมีช่องว่าง
โหมด offline ปัจจุบัน parser fallback คืน annotations ว่าง จึงยังใช้ประโยชน์จาก weighted actions/IOCs ไม่เต็มที่

### Inference, evidence และ review

`src/agents/behavior.py` ตรวจกลุ่มพฤติกรรมใน clause; inferencer เลือกจาก candidates เท่านั้นและตัด parent ที่ซ้ำกับ sub-technique ที่มีหลักฐานเดียวกัน
Pipeline ตรวจ ID/name/tactic/URL, duplicate และจำนวนผลลัพธ์ซ้ำก่อนเผยแพร่ เพื่อป้องกันผลผิดสัญญาจากส่วนอนุมาน

Linker ตรวจทั้ง span แบบ verbatim, พฤติกรรมที่อ้าง และบริบทของ clause ที่ครอบ span เพื่อป้องกันการตัดคำปฏิเสธออกจากหลักฐาน
Judge ส่ง review เมื่อ no-match, confidence ต่ำ, พบ prompt injection/ambiguity หรือมี candidate ที่ยังแข่งขันกัน
คะแนน 0.82/0.60/0.55 และ threshold 0.80 เป็น policy score; UI ระบุว่าไม่ใช่ probability การ audit confidence bins บน development ไม่ทดแทน independent calibration

### API และ privacy

- API เปิดได้แม้ KB หาย; `/ready` และ routes ที่ต้องใช้ KB ตอบ typed 503
- Inference/RAG/evaluation ทำงานผ่าน worker จำกัด 4 งานต่อ process และ deadline รวมเริ่มต้น 15 วินาที
- Thread ที่ timeout ยังคงครอง slot จนจบ ป้องกันการสะสมงานค้างไม่จำกัด
- Batch รักษาลำดับ; item failure เป็น no-match/review ตาม contract เดิม ส่วน deadline รวมตอบ 504
- จำกัด request body, narrative และ batch; validation error ไม่สะท้อน input
- มี API-key auth เมื่อตั้งค่า, per-IP/process rate limit และ explicit CORS allowlist
- Structured logs เก็บเฉพาะ route template/status/latency/server-generated request ID; ไม่มี narrative, alert ID หรือ exception traceback
- API offline เสมอและไม่โหลด .env อัตโนมัติ; provider wrapper สำหรับการทดลองโดยตรงต้องมี consent และมี redaction ขั้นต้น
- UI มีปุ่มล้างข้อมูล, ไม่มี local/session storage, แสดง disclaimer และ MITRE attribution

อ่านค่าตั้งและข้อจำกัดใน [DEPLOYMENT_PRIVACY_TH](DEPLOYMENT_PRIVACY_TH.md)

### Evaluation และ CI

`eval/diagnostics.py` จัดหมวด router/retrieval/inference/grounding/benign/ambiguity/parent mismatch และส่งออกเฉพาะ IDs กับ evidence offsets/hash
`eval/evaluator.py` บันทึก code/STIX/dataset/prompt/snapshot hashes, dependency versions, model/provider mode และ metrics เพิ่มเติม
CLI `--development` ประเมินชุดพัฒนาแยก; `--require-quality-gates` ล้มเหลวจริงเมื่อ full runtime ยังไม่ผ่าน

CI เพิ่ม development runtime gate, Chromium acceptance และ full runtime quality job พร้อม upload artifact แม้ gate fail การแก้ workflow ในเครื่องยังไม่ใช่หลักฐานว่า GitHub Actions รันผ่าน

## ผลตรวจและ artifacts

Tests ล่าสุด: **125 passed**, ไม่มี failures/errors/skips ดู [JUnit](reports/tests.xml)
Development มี 47 records และผ่าน numeric gates แต่เป็นข้อมูลที่ผู้พัฒนาสร้างเพื่อทดสอบ ไม่ใช่ independent holdout

| หลักฐาน | ไฟล์/คำสั่ง |
| --- | --- |
| Baseline error taxonomy | [baseline-errors.json](reports/baseline-errors.json) |
| Fixture validation | [fixture-final.json](reports/fixture-final.json) — คะแนนสมบูรณ์ใช้ตรวจ evaluator เท่านั้น |
| Development และ confidence bins | [development-final.json](reports/development-final.json) |
| Full runtime / quality gates | [runtime-final.json](reports/runtime-final.json) |
| Browser UI acceptance | [browser-acceptance.json](reports/browser-acceptance.json) |
| Demo ทั้ง 5 ขั้น | [demo.json](reports/demo.json) — functional demo pass ไม่เท่ากับ quality pass |
| Clean source copy / fresh venv | [clean-verification.json](reports/clean-verification.json) |
| Checklist รอผู้ตรวจ labels | [review-checklist.json](reports/review-checklist.json) |
| รวม hashes และ release blockers | [release-manifest.json](reports/release-manifest.json) |

Clean verifier คัดลอก source ที่รวมงานยังไม่ commit ไปยัง /tmp แล้วสร้าง venv ใหม่ โดยไม่คัดลอก .env, .git หรือ generated KB ดังนั้นเป็น clean working-tree copy ไม่ใช่การอ้างว่ามี release commit ใหม่แล้ว
ผล install, pip check, ingestion, tests, fixture และ development ต้องผ่าน; full runtime quality ยัง exit 1 ตาม parent-recall gate

## Backlog ที่ยังต้องปิด

| ปัญหา | งานถัดไป/ไฟล์ | ผลที่ต้องวัด |
| --- | --- | --- |
| Retrieval misses | เพิ่ม development cases จากพฤติกรรม STIX และปรับ src/rag/retriever.py หลังยืนยัน subset | Recall@1/3/5, parent recall |
| Inference misses / extra predictions | ทดสอบการระบุ subject/action และบริบทของ src/agents/behavior.py | precision, recall, F1, FPR |
| Ambiguity ไม่ส่ง review | ตรวจเหตุผลที่ข้อมูลยังไม่พอ แล้วเพิ่ม regression ใน development และ grounding_judge.py | ambiguity failures = 0 |
| Calibration/semantic review ยังไม่อิสระ | ผู้ตรวจอีกคนตรวจ evidence และจัดชุด calibration/holdout | semantic correctness และ calibration report |
| Dataset/subset ยัง pending | ผู้สอนยืนยัน decision record และ checklist โดยมีชื่อ/วัน/หลักฐาน | locked dataset + approved manifest |
| Final acceptance | รัน full gates, clean verification และ environment acceptance หลังรายการข้างต้นเสร็จ | Definition of Done ทุกข้อผ่าน |

## คำสั่งตรวจซ้ำ

```bash
.venv/bin/python -m src.rag.ingest_stix
GOOGLE_API_KEY='' GEMINI_API_KEY='' .venv/bin/python -m pytest -q
.venv/bin/python -m compileall -q src eval tests scripts
.venv/bin/python -m eval.run_eval --mode runtime --development --diagnostics --require-quality-gates
.venv/bin/python -m eval.run_eval --mode runtime --subset full --diagnostics --require-quality-gates
PLAYWRIGHT_BROWSERS_PATH=/tmp/security-alert-browsers .venv/bin/python scripts/browser_acceptance.py
.venv/bin/python scripts/demo_acceptance.py
.venv/bin/python scripts/verify_clean.py
git diff --check
git status --short
```

ยังไม่มีการเปลี่ยน gold labels, ยืนยันผู้ตรวจแทนบุคคลจริง, อนุมัติ subset, commit/push หรือ deploy ภายนอกในงานนี้
