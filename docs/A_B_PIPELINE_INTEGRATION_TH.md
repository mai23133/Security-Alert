# Contract การรวม A+B

อัปเดต 7 กันยายน 2026: A+B ทำงานผ่าน product shell D บน mai-work f567aa3 แล้ว

~~~python
parsed = parse_alert(narrative)
tactics = route_tactics(parsed)
candidates = retriever.search(parsed.narrative, tactic=tactics, top_k=5)
inferred = infer_techniques(parsed.narrative, candidates)
grounded = link_evidence(parsed.narrative, inferred)
review = judge_result(parsed.narrative, grounded, candidates)
~~~

## สาย A

src/rag/ingest_stix.py สร้าง candidates/allowlist จาก pinned STIX; src/rag/embedder.py ตัดคำ; src/rag/retriever.py ใช้ BM25 และเลือกจาก allowlist เท่านั้น รับ tactic เดี่ยว/list/None พร้อม top_k จำนวนเต็มบวก ผลเรียง score ลงและ technique_id ขึ้น

สร้าง processed ก่อน import API; ไม่มี dense embeddings หรือ persistent vector index metadata platform/source และ subset 127 เทียบเป้าหมาย 30–50 ยังเป็นงานค้าง

## สาย B

Parser/router เรียก provider เมื่อมี keyและ fallback เมื่อผิดพลาด ส่วน inferencer ใช้ lexical overlap อย่างน้อยสองคำ สร้าง prediction ไม่เกินสามจาก candidates เท่านั้น; linker ตรวจ exact substring และ judge ตรวจ structural consistency/no-match/duplicates/confidence

ไม่มี keyยังมี inference ไม่ใช่ no-match เสมอ; ไม่มี semantic grounding/negation/ambiguity validation ที่สมบูรณ์ จึงยังต้องวัด false positives

## API ที่ใช้ contract นี้

Single และ batch เรียก src/inference_pipeline.py; RAG search เรียก retriever ตรง ทั้งสาม endpoint เชื่อมแล้ว ส่วน /evaluate ยังไม่รวม C

62 tests ผ่านในรอบตรวจล่าสุด ดู [รายงาน](PROJECT_REVIEW_TH.md) และ [API overview](API_OVERVIEW_TH.md) สำหรับผลจริงและข้อจำกัด แทนตัวเลข 42 tests ของ snapshot ก่อน D
