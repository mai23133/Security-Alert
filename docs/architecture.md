# สถาปัตยกรรมปัจจุบัน

ตรวจ 11 กันยายน 2026 บน main; [ข้อกำหนด](../security-alert-attack-technique-inference.md) หัวข้อ 5/6/7/8/10

## เส้นทางข้อมูล

~~~mermaid
flowchart TD
    S["Pinned raw STIX 19.1"] --> ING["Offline ingestion"]
    ING --> KB["Generated candidates + allowlist"]
    KB --> R["BM25 ในหน่วยความจำ"]
    U["UI หรือ API client"] --> V["FastAPI validation"]
    V --> P["Parser"]
    P --> T["Tactic router"]
    T --> S1["Initial Access specialist"]
    T --> S2["Execution specialist"]
    T --> S3["Credential Access specialist"]
    S1 --> R
    S2 --> R
    S3 --> R
    R --> I["LLM candidate selector หรือ lexical offline fallback"]
    I --> E["Exact-substring evidence linker"]
    E --> J["Judge คืน review flag"]
    J --> O["ATTACKInferenceResult"]
    P -. "เมื่อเปิด key" .-> G["Gemini provider"]
    T -. "เมื่อเปิด key" .-> G
    I -. "เมื่อเปิด key" .-> G
~~~

ไม่มี dense vector database; TextEmbedder ใช้ tokenize เท่านั้น embed() ยังคืน [] eval มี fixture/runtime runner และ /evaluate แล้ว; prompt files ยังเป็น placeholders

## Runtime

1. main import alerts route ซึ่งโหลด RETRIEVER จาก processed files ก่อนรับ request จากนั้น main โหลด .env
2. request ผ่าน Pydantic validation; UI ส่ง narrative ไป single endpoint
3. parser คง narrative ต้นฉบับเสมอ router เลือก tactics ที่ผ่าน allowlist
4. ไม่มี key/provider ใช้ไม่ได้ → parser lists ว่างและ router ค้นทุก tactic ใน scope ไม่ได้หยุด inference
5. Router dispatch ไปยัง tactic specialists; แต่ละ path ใช้ BM25 กับ tactic ของตน แล้วรวมคะแนนเป็น global top-k
6. เมื่อมี key inferencer ให้ Gemini เลือก structured candidate และ Pydantic ตรวจ output; offline mode ใช้ lexical baseline
7. linker ตัด evidence ที่ไม่อยู่ใน narrative; judge ตรวจ structural conditions แล้วคืน bool เพื่อใส่ needs_human_review

ผลรวมอาจเปลี่ยนเมื่อเปิด provider เพราะ router เลือก tactic ต่างกันได้ คำว่า deterministic ใช้กับ retrieval/inference baseline เมื่อ input/candidates/mode เหมือนกัน ไม่ใช่รับประกัน live provider ซ้ำทุกครั้ง

## Lifecycle และ trust boundaries

- Raw STIX อยู่ใน Git; processed files ถูก ignore และสร้างด้วย ingestion ก่อนเปิด API/tests
- API inference/search แชร์ retriever ตอน import; taxonomy อ่านไฟล์ใหม่ทุก request จึงต้อง restart หลัง rebuild
- Request/LLM output เป็น untrusted; parser/router/inferencer escape delimiters และ validate JSON/Pydantic แต่ไม่ใช่หลักประกัน semantic correctness
- Judge คืน review flag ไม่ได้ sanitize prediction ทุกประเภทเอง; pipeline ใช้ candidate-bounded inferencer และ linker ร่วมกัน
- Provider เป็น external boundary; ข้อมูลอาจออกนอกเครื่องเมื่อมี key ต้องผ่านนโยบาย sandbox ก่อนใช้ข้อมูลจริง
- Async route เรียก synchronous SDK/pipeline; batch วนทีละ alert ยังไม่มี worker/total deadline

## Evaluation architecture

CLI หรือ /evaluate → eval/evaluator.py → validate dataset/allowlist → fixture หรือ run_inference(use_provider=False) → adapter candidates_considered เป็น candidates → eval/metrics.py → report

Runtime output ที่มี quality error ยังถูกส่งเข้า metrics ไม่ผ่าน strict fixture validator จึงวัด hallucinated IDs และ invalid evidence ได้ /evaluate รับเฉพาะ mode/top_k ของ bundled dataset และไม่เขียนไฟล์ Provider ถูกปิดแบบ explicit ใน evaluation โดย single/batch inference เดิมยังทำงานตาม key

## งานที่ยังไม่อยู่ใน architecture (คงเหลือ)

locked evaluation dataset, semantic judge, calibrated confidence, operational privacy/auth/rate limiting และ dependency lock ดู [แผนงาน](WORK_PLAN_TH.md) ก่อนเปลี่ยน schema หรือ subset
